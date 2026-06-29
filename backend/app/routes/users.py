from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from app.utils.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserProfile, UserRoleAssignment, UserRole
from app.models.user import User, UserRole as UserRoleEnum
from app.utils.helpers import hash_password, verify_password
from app.utils.logging_config import logger
import shutil
import os

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"User registration attempt: {user.username} ({user.email})")
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        logger.warning(f"Registration failed: Email {user.email} already exists.")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User {db_user.username} registered successfully with ID {db_user.id}")
    return db_user

@router.post("/login", response_model=UserResponse)
def login(username: str, password: str, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for username: {username}")
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        logger.warning(f"Login failed for username: {username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    logger.info(f"Login successful for user: {username} (ID: {user.id}, role: {user.role})")
    return user

@router.get("/{user_id}", response_model=UserProfile)
def get_user(user_id: int, db: Session = Depends(get_db)):
    logger.debug(f"Fetching profile for user_id: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User profile not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=List[UserResponse])
def get_all_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()

@router.put("/{user_id}", response_model=UserProfile)
def update_user(user_id: int, full_name: Optional[str] = None, bio: Optional[str] = None, 
                address: Optional[str] = None, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if full_name:
        user.full_name = full_name
    if bio:
        user.bio = bio
    if address:
        user.address = address
    
    db.commit()
    db.refresh(user)
    return user

@router.get("/leaderboard/top")
def get_leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.reputation_score.desc()).limit(100).all()
    return [{"username": u.username, "reputation_score": u.reputation_score, "badges": u.badges_earned} for u in users]

@router.put("/{user_id}/role", response_model=UserResponse)
def assign_role(user_id: int, admin_id: int, role_assignment: UserRoleAssignment, db: Session = Depends(get_db)):
    """
    Assign or change a user's role. Only ADMIN users can call this endpoint.
    
    Parameters:
    - user_id: The ID of the user whose role to change
    - admin_id: The ID of the admin making this change (header or query param)
    - role_assignment: The new role to assign
    
    Example:
    PUT /api/users/2/role?admin_id=1
    {
        "role": "authority"
    }
    """
    logger.info(f"Role assignment attempt: admin_id={admin_id} changing user_id={user_id} to {role_assignment.role}")
    
    # Verify admin exists and has ADMIN role
    admin = db.query(User).filter(User.id == admin_id).first()
    if not admin:
        logger.warning(f"Role assignment failed: Admin user {admin_id} not found")
        raise HTTPException(status_code=404, detail="Admin user not found")
    
    if admin.role != UserRoleEnum.ADMIN:
        logger.warning(f"Role assignment failed: User {admin_id} is not an admin (role: {admin.role})")
        raise HTTPException(status_code=403, detail="Only admins can assign roles")
    
    # Get target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        logger.warning(f"Role assignment failed: Target user {user_id} not found")
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Prevent self-demotion from admin
    if admin_id == user_id and role_assignment.role != UserRoleEnum.ADMIN:
        logger.warning(f"Role assignment failed: Admin {admin_id} attempted self-demotion")
        raise HTTPException(status_code=400, detail="Cannot demote yourself from admin role")
    
    old_role = target_user.role
    target_user.role = role_assignment.role
    db.commit()
    db.refresh(target_user)
    
    logger.info(f"Role assignment successful: user_id={user_id} changed from {old_role} to {role_assignment.role} by admin_id={admin_id}")
    return target_user
