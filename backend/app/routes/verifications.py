from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils.database import get_db
from app.schemas.verification import VerificationCreate, VerificationResponse
from app.models.verification import Verification
from app.services.issue import VerificationService
from app.utils.logging_config import logger

router = APIRouter(prefix="/api/verifications", tags=["verifications"])

@router.post("/", response_model=VerificationResponse)
def verify_issue(verification: VerificationCreate, user_id: int, db: Session = Depends(get_db)):
    logger.info(f"Verification requested for issue_id={verification.issue_id} by user_id={user_id}")
    return VerificationService.verify_issue(db, verification.issue_id, user_id, verification.is_confirmed, verification.severity_level)

@router.get("/issue/{issue_id}", response_model=List[VerificationResponse])
def get_issue_verifications(issue_id: int, db: Session = Depends(get_db)):
    logger.debug(f"Fetching verifications for issue_id={issue_id}")
    return db.query(Verification).filter(Verification.issue_id == issue_id).all()

@router.get("/user/{user_id}", response_model=List[VerificationResponse])
def get_user_verifications(user_id: int, db: Session = Depends(get_db)):
    return db.query(Verification).filter(Verification.verified_by_id == user_id).all()
