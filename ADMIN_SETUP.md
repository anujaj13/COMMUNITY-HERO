# Admin Account Setup Guide

## Overview

The Community Hero platform has three user roles:
- **CITIZEN**: Regular users who report issues and verify others' reports
- **AUTHORITY**: Government/municipal officials who can claim and resolve issues
- **ADMIN**: System administrators who can manage users and assign roles

## Quick Start: Create Your First Admin Account

### Step 1: Create a Regular User Account

Register a new user through the API:

```bash
curl -X POST "http://localhost:8000/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_user",
    "email": "admin@example.com",
    "password": "secure_password_123",
    "full_name": "System Administrator",
    "role": "citizen"
  }'
```

**Response:**
```json
{
  "id": 1,
  "username": "admin_user",
  "email": "admin@example.com",
  "full_name": "System Administrator",
  "avatar_url": null,
  "role": "citizen",
  "is_verified": false,
  "reputation_score": 0,
  "badges_earned": 0,
  "issues_reported": 0,
  "verifications_made": 0,
  "issues_resolved": 0,
  "created_at": "2024-01-15T10:30:00"
}
```

Note the user's `id` (in this example: `1`).

### Step 2: Manually Update Database (First Admin Only)

Since you need an admin to assign roles, the first admin must be created manually. Use one of these methods:

#### Method A: SQLite Command Line

```bash
# Navigate to backend directory
cd backend

# Open SQLite database
sqlite3 community_hero.db

# Update the first user to admin role
UPDATE users SET role = 'admin' WHERE id = 1;

# Verify the change
SELECT id, username, role FROM users;

# Exit
.exit
```

#### Method B: Python Script

Create `backend/setup_admin.py`:

```python
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
```

Run it:

```bash
cd backend
python setup_admin.py admin_user
# Or by ID:
python setup_admin.py 1
```

### Step 3: Login and Verify

```bash
curl -X POST "http://localhost:8000/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_user",
    "password": "secure_password_123"
  }'
```

**Response:**
```json
{
  "user_id": 1,
  "username": "admin_user",
  "token": "mock_token"
}
```

## Create Authority/Admin Accounts (After First Admin)

Once you have an admin account, use the role assignment endpoint to create other admins or authority accounts.

### Create an Authority Account

#### Step 1: Register new user
```bash
curl -X POST "http://localhost:8000/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "authority_officer",
    "email": "officer@municipality.gov",
    "password": "authority_password_123",
    "full_name": "John Authority Officer"
  }'
```

Response will show `id: 2`.

#### Step 2: Assign AUTHORITY role (as admin)
```bash
curl -X PUT "http://localhost:8000/api/users/2/role?admin_id=1&admin_secret=adfyatdshadtejkdksauhje6765hjahdka" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "authority"
  }'
```

**Response:**
```json
{
  "id": 2,
  "username": "authority_officer",
  "email": "officer@municipality.gov",
  "full_name": "John Authority Officer",
  "avatar_url": null,
  "role": "authority",
  "is_verified": false,
  "reputation_score": 0,
  "badges_earned": 0,
  "issues_reported": 0,
  "verifications_made": 0,
  "issues_resolved": 0,
  "created_at": "2024-01-15T10:35:00"
}
```

### Create Another Admin Account

Same process, but with `"role": "admin"`:

```bash
# Register
curl -X POST "http://localhost:8000/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin2",
    "email": "admin2@example.com",
    "password": "admin_password_123",
    "full_name": "Second Administrator"
  }'

# Promote to admin (as admin 1)
curl -X PUT "http://localhost:8000/api/users/3/role?admin_id=1&admin_secret=adfyatdshadtejkdksauhje6765hjahdka" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin"
  }'
```

## Role Assignment Endpoint

### Endpoint Details

```
PUT /api/users/{user_id}/role?admin_id={admin_id}&admin_secret={admin_secret}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | The ID of the user whose role to change (URL path) |
| `admin_id` | integer | Yes | The ID of the admin making the change (query parameter) |
| `admin_secret` | string | Yes | The admin secret key matching `ADMIN_SECRET_KEY` (query parameter) |
| `role` | string | Yes | The new role: `"citizen"`, `"authority"`, or `"admin"` (JSON body) |

### Request Body

```json
{
  "role": "authority"
}
```

### Responses

**Success (200)**
```json
{
  "id": 2,
  "username": "authority_officer",
  "role": "authority",
  ...
}
```

**Admin not found (404)**
```json
{
  "detail": "Admin user not found"
}
```

**Not an admin (403)**
```json
{
  "detail": "Only admins can assign roles"
}
```

**Target user not found (404)**
```json
{
  "detail": "Target user not found"
}
```

**Admin attempting self-demotion (400)**
```json
{
  "detail": "Cannot demote yourself from admin role"
}
```

## Permissions by Role

### CITIZEN
- ✅ Create issue reports
- ✅ Verify other issues
- ✅ Comment on issues
- ✅ View leaderboard
- ✅ View own profile
- ❌ Assign/resolve issues
- ❌ Change user roles

### AUTHORITY
- ✅ All CITIZEN permissions
- ✅ Claim (assign to self) issue reports
- ✅ Update issue status (IN_PROGRESS → RESOLVED)
- ✅ Resolve issues with notes
- ✅ View resolution history
- ✅ Earn reputation for resolving
- ❌ Change user roles

### ADMIN
- ✅ All AUTHORITY permissions
- ✅ Assign/change user roles
- ✅ Promote/demote any user
- ✅ System management capabilities

## Testing Your Admin Account

### 1. Login with Admin
```bash
curl -X POST "http://localhost:8000/api/users/login?username=admin_user&password=secure_password_123"
```

### 2. Create a Test Issue (as citizen)
```bash
# First, create/login as a citizen
curl -X POST "http://localhost:8000/api/issues/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Pothole on Main Street",
    "description": "Large pothole near the intersection",
    "category": "pothole",
    "priority": "high",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "user_id": 3,
    "status": "reported"
  }'
```

### 3. Claim Issue (as authority)
```bash
curl -X POST "http://localhost:8000/api/resolvers/issues/1/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2
  }'
```

### 4. Update Status (as authority)
```bash
curl -X PUT "http://localhost:8000/api/resolvers/issues/1/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "user_id": 2
  }'
```

### 5. Resolve Issue (as authority)
```bash
curl -X POST "http://localhost:8000/api/resolvers/issues/1/resolve" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "notes": "Pothole repaired successfully"
  }'
```

## Database Manual Access

### SQLite Direct Commands

```bash
# Open database
sqlite3 backend/community_hero.db

# View all users with roles
SELECT id, username, email, role, reputation_score FROM users;

# Change a user's role directly
UPDATE users SET role = 'authority' WHERE id = 2;

# View specific user
SELECT * FROM users WHERE username = 'admin_user';

# Exit
.exit
```

### List All Users with Their Roles

```bash
sqlite3 backend/community_hero.db "SELECT id, username, email, role, created_at FROM users ORDER BY id;"
```

## Troubleshooting

### "Only admins can assign roles"
- Make sure the `admin_id` parameter is a valid admin user
- Verify the admin user has `role = 'admin'` in the database

### "Cannot demote yourself from admin role"
- Admins cannot remove their own admin role (prevents accidental lockout)
- Have another admin demote you if needed

### "Email already registered"
- Use a unique email for each new user
- Delete the user from database if you need to reuse an email

### Role changes not visible in frontend
- Frontend caches user info in browser storage
- Clear localStorage and reload: `localStorage.clear(); location.reload()`
- Or logout and login again

## Development: Quick Setup Script

Create `backend/quick_setup.sh` (Linux/Mac) or `backend/quick_setup.bat` (Windows):

**Windows (quick_setup.bat):**
```batch
@echo off
echo Creating first admin account...

sqlite3 community_hero.db ^
  "INSERT INTO users (username, email, password_hash, full_name, role, reputation_score) VALUES ('admin', 'admin@localhost', 'hashed_pwd', 'Admin User', 'admin', 0);"

echo Getting user ID...
sqlite3 community_hero.db "SELECT id, username, role FROM users WHERE username='admin';"

echo Done! Login with:
echo   Username: admin
echo   Password: admin (after authentication setup)
pause
```

**Linux/Mac (quick_setup.sh):**
```bash
#!/bin/bash
echo "Creating first admin account..."

sqlite3 backend/community_hero.db \
  "INSERT INTO users (username, email, password_hash, full_name, role, reputation_score) VALUES ('admin', 'admin@localhost', 'hashed_pwd', 'Admin User', 'admin', 0);"

echo "Getting user ID..."
sqlite3 backend/community_hero.db "SELECT id, username, role FROM users WHERE username='admin';"

echo "Done! Use the user ID with the role assignment endpoint."
```

## Summary

1. **First Admin**: Manually update database (SQLite or Python script)
2. **Subsequent Admins/Authorities**: Use `/api/users/{user_id}/role` endpoint with existing admin credentials
3. **Frontend**: Admins see role badges and additional UI elements
4. **Authorization**: All endpoints check user role at service layer

For questions, check the resolver workflow documentation or review the code in `app/routes/users.py` and `app/services/resolver.py`.
