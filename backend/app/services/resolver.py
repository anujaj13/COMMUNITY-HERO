from sqlalchemy.orm import Session
from app.models.issue import Issue, IssueStatus
from app.models.user import User, UserRole
from app.models.resolution import IssueResolution, ResolutionStatus
from app.utils.logging_config import logger
from fastapi import HTTPException
from datetime import datetime

class ResolverService:
    """Service for managing issue resolution workflow"""
    
    @staticmethod
    def assign_issue(db: Session, issue_id: int, resolver_id: int, estimated_resolution_date=None):
        """
        Assign an issue to an authority/admin.
        Only authorities and admins can claim issues.
        Only one resolver can claim an issue - no re-claiming allowed.
        """
        # Verify resolver exists and has authority role
        resolver = db.query(User).filter(User.id == resolver_id).first()
        if not resolver:
            logger.error(f"ResolverService: User {resolver_id} not found")
            raise HTTPException(status_code=404, detail="Resolver not found")
        
        if resolver.role not in [UserRole.AUTHORITY, UserRole.ADMIN]:
            logger.warning(f"ResolverService: User {resolver_id} tried to assign issue but has role {resolver.role}")
            raise HTTPException(status_code=403, detail="Only authorities and admins can claim issues")
        
        # Get the issue
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            logger.error(f"ResolverService: Issue {issue_id} not found")
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Check if already assigned to ANY resolver (prevent duplicate claims)
        if issue.assigned_to_id is not None:
            logger.warning(f"ResolverService: Issue {issue_id} already assigned to {issue.assigned_to_id}, attempted by {resolver_id}")
            raise HTTPException(status_code=400, detail="Issue has already been claimed by another resolver")
        
        # Record previous status for history
        prev_status = issue.status
        
        # Assign the issue
        issue.assigned_to_id = resolver_id
        issue.claimed_at = datetime.utcnow()
        issue.status = IssueStatus.ASSIGNED
        if estimated_resolution_date:
            issue.estimated_resolution_date = estimated_resolution_date
        
        # Award reputation points for claiming the issue
        resolver.reputation_score += 25
        logger.info(f"ResolverService: Added 25 reputation points to resolver {resolver_id} for claiming issue {issue_id}")
        
        db.commit()
        
        # Log to resolution history
        resolution_entry = IssueResolution(
            issue_id=issue_id,
            resolver_id=resolver_id,
            status=ResolutionStatus.ASSIGNED,
            previous_status=prev_status,
            notes=f"Issue assigned to {resolver.full_name}",
            estimated_completion=estimated_resolution_date
        )
        db.add(resolution_entry)
        db.commit()
        
        logger.info(f"ResolverService: Issue {issue_id} assigned to resolver {resolver_id}")
        return issue
    
    @staticmethod
    def update_issue_status(db: Session, issue_id: int, resolver_id: int, new_status: str, notes: str = None):
        """
        Update issue status during resolution.
        Only the assigned resolver can update status.
        Cannot update status if issue is already RESOLVED or CLOSED.
        """
        # Get the issue
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            logger.error(f"ResolverService: Issue {issue_id} not found")
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Check if issue is already resolved or closed (locked status)
        if issue.status in [IssueStatus.RESOLVED, IssueStatus.CLOSED]:
            logger.warning(f"ResolverService: Cannot update status of {issue.status} issue {issue_id}")
            raise HTTPException(status_code=400, detail=f"Cannot modify {issue.status} issue. It is locked.")
        
        # Verify the user is the assigned resolver or admin
        resolver = db.query(User).filter(User.id == resolver_id).first()
        if not resolver:
            raise HTTPException(status_code=404, detail="Resolver not found")
        
        if issue.assigned_to_id != resolver_id and resolver.role != UserRole.ADMIN:
            logger.warning(f"ResolverService: User {resolver_id} tried to update status of issue assigned to {issue.assigned_to_id}")
            raise HTTPException(status_code=403, detail="Only the assigned resolver can update this issue")
        
        # Update status
        prev_status = issue.status
        try:
            issue.status = IssueStatus[new_status.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
        
        db.commit()
        
        # Log to resolution history
        resolution_entry = IssueResolution(
            issue_id=issue_id,
            resolver_id=resolver_id,
            status=ResolutionStatus[new_status.upper()],
            previous_status=prev_status,
            notes=notes or f"Status updated to {new_status}"
        )
        db.add(resolution_entry)
        db.commit()
        
        logger.info(f"ResolverService: Issue {issue_id} status updated to {new_status} by resolver {resolver_id}")
        return issue
    
    @staticmethod
    def resolve_issue(db: Session, issue_id: int, resolver_id: int, resolution_notes: str):
        """
        Mark an issue as resolved.
        Only the assigned resolver or admin can resolve.
        """
        # Get the issue
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Verify authorization
        resolver = db.query(User).filter(User.id == resolver_id).first()
        if not resolver:
            raise HTTPException(status_code=404, detail="Resolver not found")
        
        if issue.assigned_to_id != resolver_id and resolver.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only the assigned resolver can resolve this issue")
        
        # Mark as resolved
        prev_status = issue.status
        issue.status = IssueStatus.RESOLVED
        issue.resolved_by_id = resolver_id
        issue.resolved_at = datetime.utcnow()
        issue.resolution_notes = resolution_notes
        
        # Reward resolver
        resolver.issues_resolved += 1
        resolver.reputation_score += 50
        
        db.commit()
        
        # Log to resolution history
        resolution_entry = IssueResolution(
            issue_id=issue_id,
            resolver_id=resolver_id,
            status=ResolutionStatus.RESOLVED,
            previous_status=prev_status,
            notes=resolution_notes
        )
        db.add(resolution_entry)
        db.commit()
        
        logger.info(f"ResolverService: Issue {issue_id} resolved by {resolver_id}")
        return issue
    
    @staticmethod
    def close_issue(db: Session, issue_id: int, closer_id: int, notes: str = None):
        """
        Close an issue (final status).
        Can be done by resolver, reporter, or admin.
        """
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        closer = db.query(User).filter(User.id == closer_id).first()
        if not closer:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check permissions
        is_reporter = issue.reported_by_id == closer_id
        is_resolver = issue.resolved_by_id == closer_id
        is_admin = closer.role == UserRole.ADMIN
        
        if not (is_reporter or is_resolver or is_admin):
            raise HTTPException(status_code=403, detail="You don't have permission to close this issue")
        
        prev_status = issue.status
        issue.status = IssueStatus.CLOSED
        db.commit()
        
        # Log to resolution history
        resolution_entry = IssueResolution(
            issue_id=issue_id,
            resolver_id=closer_id,
            status=ResolutionStatus.CLOSED,
            previous_status=prev_status,
            notes=notes or "Issue closed"
        )
        db.add(resolution_entry)
        db.commit()
        
        logger.info(f"ResolverService: Issue {issue_id} closed by {closer_id}")
        return issue
    
    @staticmethod
    def get_resolution_history(db: Session, issue_id: int):
        """Get the resolution history for an issue"""
        history = db.query(IssueResolution).filter(
            IssueResolution.issue_id == issue_id
        ).order_by(IssueResolution.changed_at.desc()).all()
        
        logger.debug(f"ResolverService: Retrieved {len(history)} resolution entries for issue {issue_id}")
        return history
    
    @staticmethod
    def get_resolver_issues(db: Session, resolver_id: int, status: str = None):
        """Get all issues assigned to a resolver"""
        query = db.query(Issue).filter(Issue.assigned_to_id == resolver_id)
        
        if status:
            try:
                status_enum = IssueStatus[status.upper()]
                query = query.filter(Issue.status == status_enum)
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        issues = query.order_by(Issue.priority.desc(), Issue.created_at.asc()).all()
        logger.debug(f"ResolverService: Found {len(issues)} issues for resolver {resolver_id}")
        return issues
