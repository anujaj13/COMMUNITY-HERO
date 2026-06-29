from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import time
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.utils.logging_config import logger

load_dotenv()
logger.info("Initializing Community Hero API...")

# Import all models so that Base knows about them before create_all
from app.utils.database import engine, get_db, Base
from app.models import user, issue, verification, comment, gamification, resolution  # noqa: F401

from app.routes import users, issues, verifications, comments, resolver
from app.routes import ai as ai_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize DB tables after uvicorn has bound to the port
    logger.info("Synchronizing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables synchronized.")
    except Exception as e:
        logger.error(f"Failed to synchronize database tables: {e}")
        raise
    yield
    # Shutdown (nothing needed for now)


app = FastAPI(
    title="Community Hero API",
    description="Hyperlocal Problem Solver Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    logger.info(f"Incoming request: {method} {path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    
    logger.info(f"Completed: {method} {path} | Status: {response.status_code} | Time: {formatted_process_time}ms")
    
    return response

logger.info("FastAPI application created.")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
logger.info("Registering application routes...")
app.include_router(users.router)
app.include_router(issues.router)
app.include_router(verifications.router)
app.include_router(comments.router)
app.include_router(resolver.router)
app.include_router(ai_routes.router)

# Serve uploaded files (images, videos)
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
logger.info(f"Mounting static files at /uploads from {uploads_dir}")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.get("/")
def read_root():
    logger.debug("Root endpoint accessed")
    return {
        "message": "Welcome to Community Hero API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "healthy"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": time.time()}

@app.get("/api/stats/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)):
    logger.info("Fetching dashboard statistics...")
    from app.models.user import User
    from app.models.issue import Issue
    from app.models.verification import Verification

    try:
        total_users = db.query(User).count()
        total_issues = db.query(Issue).count()
        total_verifications = db.query(Verification).count()
        resolved_issues = db.query(Issue).filter(Issue.status == "resolved").count()

        stats = {
            "total_users": total_users,
            "total_issues": total_issues,
            "total_verifications": total_verifications,
            "resolved_issues": resolved_issues,
            "resolution_rate": (resolved_issues / total_issues * 100) if total_issues > 0 else 0
        }
        logger.info(f"Dashboard stats retrieved: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise



