# Quick Reference: Admin Account Setup

## 3 Ways to Create Admin/Authority Accounts

### 🚀 **Option 1: API Role Assignment (Recommended After First Admin)**

**Prerequisite**: Have an existing admin user

```bash
# 1. Create user account (CITIZEN by default)
curl -X POST "http://localhost:8000/api/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_authority",
    "email": "john@municipality.gov",
    "password": "password123",
    "full_name": "John Authority"
  }'

# 2. Promote to AUTHORITY (as admin_id=1)
curl -X PUT "http://localhost:8000/api/users/2/role?admin_id=1&admin_secret=adfyatdshadtejkdksauhje6765hjahdka" \
  -H "Content-Type: application/json" \
  -d '{"role": "authority"}'
```

---

### 🗄️ **Option 2: SQLite Database Direct Edit (For First Admin)**

```bash
# Open database
cd backend
sqlite3 community_hero.db

# Make first user an admin
UPDATE users SET role = 'admin' WHERE id = 1;

# Verify
SELECT id, username, role FROM users;

# Exit
.exit
```

---

### 🐍 **Option 3: Python Script (Easiest for Development)**

**Create `backend/set_admin.py`:**

```python
from app.utils.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
import sys

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        print(f"❌ User {user_id} not found")
        sys.exit(1)
    
    user.role = UserRole.ADMIN
    db.commit()
    print(f"✅ {user.username} is now ADMIN")
    
finally:
    db.close()
```

**Run it:**
```bash
cd backend
python set_admin.py 1
```

---

## Login Workflow

### Register
```bash
POST /api/users/register
{
  "username": "john_authority",
  "email": "john@municipality.gov",
  "password": "password123",
  "full_name": "John Authority"
}
```

### Login
```bash
POST /api/users/login
?username=john_authority&password=password123
```

### Response
```json
{
  "user_id": 2,
  "username": "john_authority",
  "token": "mock_token"
}
```

---

## Role Assignments After First Admin

```bash
# Assign AUTHORITY
PUT /api/users/2/role?admin_id=1&admin_secret=adfyatdshadtejkdksauhje6765hjahdka
{"role": "authority"}

# Assign ADMIN
PUT /api/users/3/role?admin_id=1&admin_secret=adfyatdshadtejkdksauhje6765hjahdka
{"role": "admin"}

# Revert to CITIZEN
PUT /api/users/2/role?admin_id=1&admin_secret=adfyatdshadtejkdksauhje6765hjahdka
{"role": "citizen"}
```

---

## Verify Your Setup

```bash
# Get user profile
curl "http://localhost:8000/api/users/1"

# Response shows role
{
  "id": 1,
  "username": "admin_user",
  "role": "admin",
  ...
}
```

---

## Permissions Matrix

| Permission | CITIZEN | AUTHORITY | ADMIN |
|-----------|---------|-----------|-------|
| Report Issues | ✅ | ✅ | ✅ |
| Verify Issues | ✅ | ✅ | ✅ |
| Claim Issues | ❌ | ✅ | ✅ |
| Resolve Issues | ❌ | ✅ | ✅ |
| Assign Roles | ❌ | ❌ | ✅ |
| View Admin Panel | ❌ | ❌ | ✅ |

---

## First Time Setup Checklist

- [ ] Start backend: `python -m uvicorn app.main:app --reload`
- [ ] Register user account via `/api/users/register`
- [ ] Promote to admin using **Option 1, 2, or 3** above
- [ ] Login and verify role shows in profile
- [ ] Create authority account using `/api/users/{id}/role`
- [ ] Test claiming/resolving issues with authority account

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Only admins can assign roles" | Verify admin_id has role='admin' in database |
| "Email already registered" | Use unique email for each user |
| Frontend doesn't show role | Clear browser storage: `localStorage.clear()` |
| Role change not visible | Logout and login again |

See **ADMIN_SETUP.md** for full documentation.
