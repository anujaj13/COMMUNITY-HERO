from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from app.utils.database import get_db
from app.models.issue import Issue
from app.services.ai_service import analyze_issue, find_duplicates, analyze_multimodal_issue
from app.services.insights_service import generate_insights, forecast_resolution
from app.utils.logging_config import logger
import os
import shutil

router = APIRouter(prefix="/api/ai", tags=["ai"])


class AnalyzeRequest(BaseModel):
    title: str
    description: str
    check_duplicates: bool = True


class AnalyzeResponse(BaseModel):
    category: str
    priority: str
    tags: list[str]
    summary: str
    severity_rationale: str
    duplicates: list[dict]
    error: Optional[str] = None


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    AI-powered analysis of a new issue report.
    Returns suggested category, priority, tags, summary, and potential duplicates.
    """
    # Run AI analysis
    result = analyze_issue(req.title, req.description)

    # Duplicate detection
    duplicates = []
    if req.check_duplicates:
        existing = db.query(Issue).filter(
            Issue.status != "closed"
        ).order_by(Issue.created_at.desc()).limit(50).all()

        existing_dicts = [
            {
                "id": i.id,
                "title": i.title,
                "description": i.description or "",
                "address": i.address or "",
                "status": i.status,
            }
            for i in existing
        ]
        duplicates = find_duplicates(req.title, req.description, existing_dicts)

    return AnalyzeResponse(
        category=result["category"],
        priority=result["priority"],
        tags=result["tags"],
        summary=result["summary"],
        severity_rationale=result["severity_rationale"],
        duplicates=duplicates,
        error=result.get("error"),
    )


@router.post("/analyze-media")
def analyze_media(
    context: Optional[str] = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Analyzes uploaded media (image/video) without creating an issue.
    Returns detected title, category, description, tags, priority, and summary.
    """
    temp_path = None
    try:
        # 1. Save file temporarily
        os.makedirs("uploads", exist_ok=True)
        temp_path = f"uploads/temp_pre_{file.filename}"
        logger.info(f"Saving file to {temp_path}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File saved successfully, size: {os.path.getsize(temp_path)} bytes")
        
        # 2. Run AI Analysis
        logger.info(f"Starting AI analysis for {file.filename}")
        ai_result = analyze_multimodal_issue(context or "", temp_path, file.content_type)
        logger.info(f"AI analysis complete: {ai_result.get('title')}")
        
        # 3. Check for potential duplicates (optional but good)
        existing = db.query(Issue).filter(
            Issue.status != "closed"
        ).order_by(Issue.created_at.desc()).limit(20).all()

        existing_dicts = [
            {"id": i.id, "title": i.title, "description": i.description or "", "address": i.address or "", "status": i.status}
            for i in existing
        ]
        duplicates = find_duplicates(ai_result["title"], ai_result["description"], existing_dicts)
        
        ai_result["duplicates"] = duplicates
        logger.info(f"Found {len(duplicates)} potential duplicates")
        return ai_result
    except Exception as e:
        logger.error(f"Error in analyze_media: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug(f"Cleaned up temp file: {temp_path}")
            except:
                pass


@router.get("/insights")
def get_predictive_insights(db: Session = Depends(get_db)):
    """
    Returns AI-generated predictive insights for the community dashboard.
    Includes at-risk issues, category trends, hotspot clusters, and a
    narrative summary. Results are cached for 10 minutes.
    """
    logger.info("AI insights endpoint called")
    return generate_insights(db)


@router.get("/insights/resolution-forecast/{issue_id}")
def get_resolution_forecast(issue_id: int, db: Session = Depends(get_db)):
    """
    Returns an AI-generated resolution time forecast for a specific open issue.
    Uses historical resolution patterns for the same category as context.
    """
    logger.info(f"Resolution forecast requested for issue {issue_id}")
    return forecast_resolution(issue_id, db)
