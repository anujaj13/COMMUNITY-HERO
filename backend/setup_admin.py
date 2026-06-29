from app.utils.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
import sys
import os

print(f"🔍 Starting admin promotion script...")
print(f"📍 Current working directory: {os.getcwd()}")
_db_url = os.getenv('DATABASE_URL', 'Not set')
_masked = _db_url.split("@")[-1] if "@" in _db_url else _db_url
print(f"📍 DATABASE_URL: ...@{_masked}")

# Initialize database
try:
    print("📊 Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables initialized")
except Exception as e:
    print(f"❌ Failed to initialize database: {e}")
    sys.exit(1)

# Get database session
db = SessionLocal()

try:
    # Debug: Check if users table exists and has any records
    user_count = db.query(User).count()
    print(f"📈 Total users in database: {user_count}")
    
    if user_count == 0:
        print("⚠️  No users found in database!")
        print("Available users: NONE")
        sys.exit(1)
    
    # Print all users for debugging
    print("\n📋 Available users in database:")
    all_users = db.query(User).all()
    for u in all_users:
        print(f"   - ID: {u.id}, Username: {u.username}, Role: {u.role}")
    print()
    
    # Get user by ID or username
    user_identifier = sys.argv[1] if len(sys.argv) > 1 else "admin_user"
    print(f"🔎 Looking for user: '{user_identifier}'")
    
    user = None
    
    # Try to find by ID first
    if user_identifier.isdigit():
        print(f"   → Searching by ID: {user_identifier}")
        user = db.query(User).filter(User.id == int(user_identifier)).first()
    else:
        print(f"   → Searching by username: {user_identifier}")
        user = db.query(User).filter(User.username == user_identifier).first()
    
    if not user:
        print(f"\n❌ User '{user_identifier}' not found")
        print(f"\n💡 Did you mean one of these?")
        for u in all_users:
            print(f"   - {u.username} (ID: {u.id})")
        sys.exit(1)
    
    old_role = user.role
    user.role = UserRole.ADMIN
    db.commit()
    
    print(f"\n✅ Success!")
    print(f"   User: {user.username} (ID: {user.id})")
    print(f"   Role changed: {old_role} → ADMIN")
    
except Exception as e:
    print(f"\n❌ Error during promotion: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
finally:
    db.close()