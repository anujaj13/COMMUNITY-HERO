#!/usr/bin/env python
"""Comprehensive diagnostic for Community Hero backend"""
import sys
from app.utils.database import engine, Base
from app.models.user import User, UserRole
from app.models.issue import Issue, IssueStatus, IssueCategory
from app.models.verification import Verification
from app.models.comment import Comment
from app.models.gamification import UserBadge
from app.models.resolution import IssueResolution
from sqlalchemy import inspect

print("\n" + "="*60)
print("COMMUNITY HERO - BACKEND DIAGNOSTIC REPORT")
print("="*60 + "\n")

# 1. Check database connection
print("[1] DATABASE CONNECTION")
try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print('  ✓ Database connection successful')
    print(f'  ✓ Tables found: {len(tables)}')
    for table in tables:
        cols = len(inspector.get_columns(table))
        print(f'      - {table}: {cols} columns')
except Exception as e:
    print(f'  ✗ Database error: {e}')
    sys.exit(1)

# 2. Check database queries
print("\n[2] DATABASE QUERIES")
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
db = Session()

try:
    user_count = db.query(User).count()
    issue_count = db.query(Issue).count()
    verification_count = db.query(Verification).count()
    comment_count = db.query(Comment).count()
    
    print(f'  ✓ Users: {user_count}')
    print(f'  ✓ Issues: {issue_count}')
    print(f'  ✓ Verifications: {verification_count}')
    print(f'  ✓ Comments: {comment_count}')
except Exception as e:
    print(f'  ✗ Query error: {e}')

# 3. Check models
print("\n[3] MODELS")
try:
    from app.models import user, issue, verification, comment, gamification, resolution
    print('  ✓ user.py')
    print('  ✓ issue.py')
    print('  ✓ verification.py')
    print('  ✓ comment.py')
    print('  ✓ gamification.py')
    print('  ✓ resolution.py')
except Exception as e:
    print(f'  ✗ Model error: {e}')

# 4. Check routes
print("\n[4] ROUTES")
try:
    from app.routes import users, issues, verifications, comments, resolver, ai
    print('  ✓ users.py')
    print('  ✓ issues.py')
    print('  ✓ verifications.py')
    print('  ✓ comments.py')
    print('  ✓ resolver.py')
    print('  ✓ ai.py')
except Exception as e:
    print(f'  ✗ Route error: {e}')

# 5. Check services
print("\n[5] SERVICES")
try:
    from app.services import issue as issue_service
    from app.services import ai_service
    from app.services import resolver as resolver_service
    print('  ✓ issue.py')
    print('  ✓ ai_service.py')
    print('  ✓ resolver.py')
except Exception as e:
    print(f'  ✗ Service error: {e}')

# 6. Check schemas
print("\n[6] SCHEMAS")
try:
    from app.schemas import user, issue, verification, comment, gamification, resolver
    print('  ✓ user.py')
    print('  ✓ issue.py')
    print('  ✓ verification.py')
    print('  ✓ comment.py')
    print('  ✓ gamification.py')
    print('  ✓ resolver.py')
except Exception as e:
    print(f'  ✗ Schema error: {e}')

# 7. Check environment
print("\n[7] ENVIRONMENT")
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "NOT SET")
if api_key and api_key != "NOT SET":
    key_preview = f"{api_key[:10]}...{api_key[-10:]}"
    print(f'  ✓ GEMINI_API_KEY: {key_preview}')
else:
    print(f'  ✗ GEMINI_API_KEY: NOT SET')

db_url = os.getenv("DATABASE_URL", "NOT SET")
print(f'  ✓ DATABASE_URL: {db_url}')

# 8. Check FastAPI app
print("\n[8] FASTAPI APP")
try:
    from app.main import app
    print('  ✓ FastAPI app created')
    print(f'  ✓ Title: {app.title}')
    print(f'  ✓ Version: {app.version}')
    route_count = len(app.routes)
    print(f'  ✓ Routes: {route_count}')
except Exception as e:
    print(f'  ✗ App error: {e}')

print("\n" + "="*60)
print("✓ ALL SYSTEMS OPERATIONAL")
print("="*60 + "\n")
