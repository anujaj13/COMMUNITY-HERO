from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.utils.database import get_db
from app.schemas.issue import IssueCreate, IssueResponse, IssueUpdate, IssueCategoryResponse
from app.models.issue import Issue, IssueStatus, IssueCategory
from app.services.issue import IssueService
from app.services.ai_service import analyze_multimodal_issue
from app.utils.logging_config import logger
import os
import shutil

router = APIRouter(prefix="/api/issues", tags=["issues"])

@router.post("/ai-report", response_model=IssueResponse)
def create_ai_issue(
    user_id: int,
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: str = Form(...),
    priority: Optional[str] = Form(None),
    context: Optional[str] = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Creates an issue by analyzing uploaded media with AI.
    """
    temp_path = None
    try:
        # 1. Validate inputs
        logger.info(f"AI report request: user_id={user_id}, file={file.filename}, content_type={file.content_type}")
        
        if not file:
            raise ValueError("No file provided")
        
        logger.info(f"File received: {file.filename}")
        
        # 2. Save file temporarily
        os.makedirs("uploads", exist_ok=True)
        temp_path = f"uploads/temp_{file.filename}"
        logger.debug(f"Saving file to {temp_path}")
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved successfully to {temp_path}")
        
        # 3. Run AI Analysis
        logger.info(f"Starting AI analysis for file: {file.filename}")
        ai_result = analyze_multimodal_issue(context or "", temp_path, file.content_type)
        logger.info(f"AI analysis complete: title='{ai_result.get('title')}'")
        
        final_title = ai_result.get("title", "Unidentified Issue")
        final_desc = ai_result.get("description", "Issue uploaded without AI analysis.")
        final_cat = ai_result.get("category", "other")
        final_priority = priority or ai_result.get("priority", "medium")
        
        # Log if AI analysis failed
        if "error" in ai_result.get("tags", []):
            logger.warning(f"AI analysis failed, using fallback values")
        
        logger.debug(f"Final values: title={final_title}, category={final_cat}, priority={final_priority}")
        
        # 4. Create Issue in database
        db_issue = Issue(
            title=final_title,
            description=final_desc,
            category=final_cat,
            priority=final_priority,
            latitude=latitude,
            longitude=longitude,
            address=address,
            reported_by_id=user_id,
            impact_score=IssueService._calculate_impact_score(final_priority)
        )
        db.add(db_issue)
        db.commit()
        db.refresh(db_issue)
        
        logger.info(f"Issue {db_issue.id} created in database")
        
        # 5. Rename file with issue ID
        extension = os.path.splitext(file.filename)[1]
        final_path = f"uploads/{db_issue.id}{extension}"
        logger.debug(f"Renaming file to {final_path}")
        
        if os.path.exists(temp_path):
            os.rename(temp_path, final_path)
            logger.info(f"File renamed to {final_path}")
        else:
            logger.warning(f"Temp file not found: {temp_path}")
        
        # 6. Update issue with media URL
        if extension.lower() in [".mp4", ".mov", ".avi"]:
            db_issue.video_url = final_path
        else:
            db_issue.image_url = final_path
        
        db.commit()
        db.refresh(db_issue)
        logger.info(f"Issue {db_issue.id} created successfully with media at {final_path}")
        
        return db_issue
        
    except Exception as e:
        logger.error(f"Error creating AI issue: {type(e).__name__}: {str(e)}", exc_info=True)
        # Clean up temp file if it exists
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug(f"Cleaned up temp file: {temp_path}")
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to create issue: {str(e)}")


@router.post("/", response_model=IssueResponse)
def create_issue(issue: IssueCreate, user_id: int, db: Session = Depends(get_db)):
    logger.info(f"Standard issue creation requested by user_id={user_id}")
    return IssueService.create_issue(db, issue, user_id)

@router.get("/", response_model=List[IssueResponse])
def get_issues(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching issues (skip={skip}, limit={limit}, status={status}, category={category})")
    query = db.query(Issue)
    if status:
        query = query.filter(Issue.status == status)
    if category:
        query = query.filter(Issue.category == category)
    results = query.offset(skip).limit(limit).all()
    logger.debug(f"Found {len(results)} issues.")
    return results

@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue

@router.put("/{issue_id}", response_model=IssueResponse)
def update_issue(issue_id: int, update_data: IssueUpdate, user_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Authorization check: only the issue reporter can edit their own issue
    if issue.reported_by_id != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own issues")
    
    if update_data.title:
        issue.title = update_data.title
    if update_data.description:
        issue.description = update_data.description
    if update_data.category:
        issue.category = update_data.category
    if update_data.priority:
        issue.priority = update_data.priority
    if update_data.status:
        issue.status = update_data.status
    
    db.commit()
    db.refresh(issue)
    logger.info(f"Issue {issue_id} updated by user {user_id}")
    return issue

@router.get("/nearby/list")
def get_nearby_issues(latitude: float, longitude: float, radius_km: float = 5, db: Session = Depends(get_db)):
    issues = IssueService.get_nearby_issues(db, latitude, longitude, radius_km)
    return issues

@router.get("/trending/list")
def get_trending_issues(days: int = 7, db: Session = Depends(get_db)):
    return IssueService.get_trending_issues(db, days)

@router.post("/{issue_id}/upload-media")
def upload_issue_media(issue_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    os.makedirs("uploads", exist_ok=True)
    extension = os.path.splitext(file.filename)[1]
    file_path = f"uploads/{issue_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    if extension.lower() in [".mp4", ".mov", ".avi"]:
        issue.video_url = file_path
    else:
        issue.image_url = file_path
        
    db.commit()
    return {"file_path": file_path, "type": "video" if issue.video_url == file_path else "image"}

@router.get("/stats/by-category")
def get_issues_by_category(db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    results = db.query(Issue.category, func.count(Issue.id)).group_by(Issue.category).all()
    total = sum([count for _, count in results])
    
    return [
        IssueCategoryResponse(
            category=category,
            count=count,
            percentage=(count / total * 100) if total > 0 else 0
        )
        for category, count in results
    ]
