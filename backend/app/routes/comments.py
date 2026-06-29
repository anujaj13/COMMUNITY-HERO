from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils.database import get_db
from app.schemas.comment import CommentCreate, CommentResponse
from app.models.comment import Comment
from app.models.issue import Issue
from app.utils.logging_config import logger

router = APIRouter(prefix="/api/comments", tags=["comments"])

@router.post("/", response_model=CommentResponse)
def create_comment(comment: CommentCreate, user_id: int, db: Session = Depends(get_db)):
    logger.info(f"Adding comment to issue_id={comment.issue_id} by user_id={user_id}")
    issue = db.query(Issue).filter(Issue.id == comment.issue_id).first()
    if not issue:
        logger.warning(f"Failed to add comment: Issue {comment.issue_id} not found")
        raise HTTPException(status_code=404, detail="Issue not found")
    
    db_comment = Comment(
        issue_id=comment.issue_id,
        user_id=user_id,
        text=comment.text
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    logger.info(f"Comment {db_comment.id} added successfully.")
    return db_comment

@router.get("/issue/{issue_id}", response_model=List[CommentResponse])
def get_issue_comments(issue_id: int, db: Session = Depends(get_db)):
    logger.debug(f"Fetching comments for issue_id={issue_id}")
    return db.query(Comment).filter(Comment.issue_id == issue_id).all()

@router.put("/{comment_id}/like")
def like_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment.likes += 1
    db.commit()
    return {"likes": comment.likes}
