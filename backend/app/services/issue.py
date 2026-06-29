from sqlalchemy.orm import Session
from app.models.issue import Issue, IssueStatus
from app.models.user import User
from app.schemas.issue import IssueCreate, IssuePriority
from datetime import datetime, timedelta
from app.utils.helpers import get_distance
from app.utils.logging_config import logger

class IssueService:
    @staticmethod
    def create_issue(db: Session, issue: IssueCreate, user_id: int):
        logger.info(f"IssueService: Creating new issue '{issue.title}' for user_id={user_id}")
        db_issue = Issue(
            title=issue.title,
            description=issue.description,
            category=issue.category,
            priority=issue.priority,
            latitude=issue.latitude,
            longitude=issue.longitude,
            address=issue.address,
            reported_by_id=user_id,
            impact_score=IssueService._calculate_impact_score(issue.priority)
        )
        db.add(db_issue)
        db.commit()
        db.refresh(db_issue)
        logger.debug(f"IssueService: Issue created with ID {db_issue.id}")
        
        # Award badge for reporting
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            logger.info(f"IssueService: Updating user reputation for user_id={user_id}")
            user.issues_reported += 1
            user.reputation_score += 10
            if user.issues_reported % 5 == 0:
                user.badges_earned += 1
                logger.info(f"IssueService: User {user_id} earned a new badge!")
            db.commit()
        
        return db_issue
    
    @staticmethod
    def _calculate_impact_score(priority: IssuePriority) -> float:
        priority_scores = {
            IssuePriority.CRITICAL: 100.0,
            IssuePriority.HIGH: 75.0,
            IssuePriority.MEDIUM: 50.0,
            IssuePriority.LOW: 25.0
        }
        score = priority_scores.get(priority, 50.0)
        logger.debug(f"IssueService: Calculated impact score {score} for priority {priority}")
        return score
    
    @staticmethod
    def get_nearby_issues(db: Session, latitude: float, longitude: float, radius_km: float = 5):
        logger.info(f"IssueService: Searching for issues near ({latitude}, {longitude}) within {radius_km}km")
        all_issues = db.query(Issue).all()
        nearby = []
        for issue in all_issues:
            distance = get_distance(latitude, longitude, issue.latitude, issue.longitude)
            if distance <= radius_km:
                nearby.append(issue)
        logger.info(f"IssueService: Found {len(nearby)} nearby issues.")
        return nearby
    
    @staticmethod
    def get_trending_issues(db: Session, days: int = 7):
        logger.info(f"IssueService: Fetching trending issues for last {days} days")
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        results = db.query(Issue).filter(
            Issue.created_at >= cutoff_date
        ).order_by(Issue.verification_count.desc()).limit(10).all()
        logger.debug(f"IssueService: Found {len(results)} trending issues.")
        return results

class VerificationService:
    @staticmethod
    def verify_issue(db: Session, issue_id: int, user_id: int, is_confirmed: bool, severity_level: str):
        from app.models.verification import Verification
        from app.models.issue import IssueStatus
        logger.info(f"VerificationService: Verifying issue_id={issue_id} by user_id={user_id} (Confirmed: {is_confirmed})")
        
        # Check if issue is resolved or closed (locked status)
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if issue and issue.status in [IssueStatus.RESOLVED, IssueStatus.CLOSED]:
            logger.warning(f"VerificationService: Cannot verify {issue.status} issue {issue_id}")
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail=f"Cannot verify {issue.status} issue. It is locked."
            )
        
        # Check if user has already verified this issue
        existing_verification = db.query(Verification).filter(
            Verification.issue_id == issue_id,
            Verification.verified_by_id == user_id
        ).first()
        
        if existing_verification:
            logger.warning(f"VerificationService: User {user_id} has already verified issue {issue_id}")
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Already verified by you"
            )
        
        verification = Verification(
            issue_id=issue_id,
            verified_by_id=user_id,
            is_confirmed=is_confirmed,
            severity_level=severity_level
        )
        db.add(verification)
        
        # Update issue
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if issue:
            issue.verification_count += 1
            logger.debug(f"VerificationService: Issue {issue_id} verification count increased to {issue.verification_count}")
            if is_confirmed:
                issue.status = IssueStatus.VERIFIED
                logger.info(f"VerificationService: Issue {issue_id} status updated to VERIFIED (confirmed verification)")
            issue.impact_score = issue.verification_count * 10 + (100 if is_confirmed else 0)
        
        # Update user
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.verifications_made += 1
            user.reputation_score += 15
            logger.debug(f"VerificationService: User {user_id} reputation increased.")
        
        db.commit()
        return verification
