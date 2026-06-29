from app.utils.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
import sys

# Initialize database
Base.metadata.create_all(bind=engine)

# Get database session
db = SessionLocal()

try:
    # Get user by ID or username
    user_identifier = sys.argv[1] if len(sys.argv) > 1 else "admin_user"
    
    # Try to find by ID first
    if user_identifier.isdigit():
        user = db.query(User).filter(User.id == int(user_identifier)).first()
    else:
        user = db.query(User).filter(User.username == user_identifier).first()
    
    if not user:
        print(f"❌ User '{user_identifier}' not found")
        sys.exit(1)
    
    old_role = user.role
    user.role = UserRole.ADMIN
    db.commit()
    
    print(f"✅ User '{user.username}' (ID: {user.id}) promoted from {old_role} to ADMIN")
    
finally:
    db.close()