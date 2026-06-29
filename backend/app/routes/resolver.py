from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.utils.database import get_db
from app.models.user import UserRole
from app.services.resolver import ResolverService
from app.schemas.resolver import IssueAssign, IssueStatusUpdate, ResolutionComplete, IssueDetailedResponse, IssueResolutionResponse
from app.utils.logging_config import logger

router = APIRouter(prefix="/api/resolvers", tags=["resolvers"])

@router.post("/{issue_id}/assign", response_model=IssueDetailedResponse)
def assign_issue(
    issue_id: int,
    resolver_id: int,
    data: IssueAssign,
    db: Session = Depends(get_db)
):
    """
    Assign an issue to a resolver (authority/admin).
    The resolver must have AUTHORITY or ADMIN role.
    """
    logger.info(f"Resolver endpoint: Assigning issue {issue_id} to resolver {resolver_id}")
    issue = ResolverService.assign_issue(
        db,
        issue_id,
        resolver_id,
        data.estimated_resolution_date
    )
    return issue

@router.put("/{issue_id}/status", response_model=IssueDetailedResponse)
def update_issue_status(
    issue_id: int,
    resolver_id: int,
    data: IssueStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update the status of an issue during resolution.
    Only the assigned resolver or admin can update status.
    """
    logger.info(f"Resolver endpoint: Updating issue {issue_id} status to {data.status}")
    issue = ResolverService.update_issue_status(
        db,
        issue_id,
        resolver_id,
        data.status,
        data.notes
    )
    return issue

@router.post("/{issue_id}/resolve", response_model=IssueDetailedResponse)
def resolve_issue(
    issue_id: int,
    resolver_id: int,
    data: ResolutionComplete,
    db: Session = Depends(get_db)
):
    """
    Mark an issue as resolved.
    Only the assigned resolver or admin can resolve.
    """
    logger.info(f"Resolver endpoint: Resolving issue {issue_id} by resolver {resolver_id}")
    issue = ResolverService.resolve_issue(
        db,
        issue_id,
        resolver_id,
        data.resolution_notes
    )
    return issue

@router.put("/{issue_id}/close", response_model=IssueDetailedResponse)
def close_issue(
    issue_id: int,
    user_id: int,
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Close an issue (final status).
    Can be done by the reporter, resolver, or admin.
    """
    logger.info(f"Resolver endpoint: Closing issue {issue_id} by user {user_id}")
    issue = ResolverService.close_issue(db, issue_id, user_id, notes)
    return issue

@router.get("/{issue_id}/history", response_model=List[IssueResolutionResponse])
def get_resolution_history(
    issue_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the resolution/status change history for an issue.
    Shows audit trail of all status changes.
    """
    logger.info(f"Resolver endpoint: Getting resolution history for issue {issue_id}")
    history = ResolverService.get_resolution_history(db, issue_id)
    return history

@router.get("/assigned/{resolver_id}", response_model=List[IssueDetailedResponse])
def get_resolver_issues(
    resolver_id: int,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all issues assigned to a specific resolver.
    Optionally filter by status.
    """
    logger.info(f"Resolver endpoint: Getting assigned issues for resolver {resolver_id}, status={status}")
    issues = ResolverService.get_resolver_issues(db, resolver_id, status)
    return issues

@router.get("/pending/list")
def get_pending_issues(db: Session = Depends(get_db)):
    """
    Get all pending issues (not yet assigned or in progress).
    Useful for authorities to see available issues to work on.
    """
    from app.models.issue import Issue, IssueStatus
    
    logger.info("Resolver endpoint: Fetching pending issues")
    pending = db.query(Issue).filter(
        Issue.status.in_([IssueStatus.REPORTED, IssueStatus.VERIFIED])
    ).order_by(Issue.priority.desc(), Issue.created_at.asc()).all()
    
    logger.debug(f"Found {len(pending)} pending issues")
    return pending
