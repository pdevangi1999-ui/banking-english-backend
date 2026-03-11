from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database.db import get_db
from database.models import User, LearningProgress, RevisionSchedule, LearningHistory, ContentItem
from datetime import date, timedelta

router = APIRouter(prefix="/learning", tags=["Learning"])

# ── GET PROGRESS ─────────────────────────────────────────────────────────────
@router.get("/progress")
def get_progress(user_id: int, db: Session = Depends(get_db)):
    progress = db.query(LearningProgress)\
        .filter(LearningProgress.user_id == user_id).first()

    # First time user — create progress row
    if not progress:
        progress = LearningProgress(
            user_id=user_id,
            current_batch=1,
            batch_completed=False,
            quiz_completed=False,
            last_updated=date.today()
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    # New day check — reset daily flags
    if progress.last_updated < date.today():
        progress.batch_completed = False
        progress.quiz_completed = False
        progress.last_updated = date.today()
        db.commit()

    return {
        "current_batch":   progress.current_batch,
        "batch_completed": progress.batch_completed,
        "quiz_completed":  progress.quiz_completed,
    }


def _upsert_history(db: Session, user_id: int, day: int, type: str):
    history = db.query(LearningHistory).filter(
        LearningHistory.user_id == user_id,
        LearningHistory.day == day,
        LearningHistory.type == type
    ).first()
    if not history:
        history = LearningHistory(
            user_id=user_id,
            day=day,
            type=type,
            date=date.today()
        )
        db.add(history)
    return history

# ── COMPLETE BATCH ────────────────────────────────────────────────────────────
class CompleteBatchRequest(BaseModel):
    user_id: int
    concept_ids: List[str]   # the 10/20 items from today's batch
    type: str = "word"
    total_items: Optional[int] = None

@router.post("/complete-batch")
def complete_batch(req: CompleteBatchRequest, db: Session = Depends(get_db)):
    progress = db.query(LearningProgress)\
        .filter(LearningProgress.user_id == req.user_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    # Mark batch as completed
    progress.batch_completed = True
    progress.last_updated = date.today()

    # Upsert history for this day/type
    history = _upsert_history(db, req.user_id, progress.current_batch, req.type)
    history.batch_completed = True
    history.items_done = len(req.concept_ids)
    history.total_items = req.total_items or len(req.concept_ids)
    history.date = date.today()

    # Add all 10 words to revision_schedule
    for concept_id in req.concept_ids:
        existing = db.query(RevisionSchedule)\
            .filter(
                RevisionSchedule.user_id == req.user_id,
                RevisionSchedule.concept_id == concept_id
            ).first()
        if not existing:
            revision = RevisionSchedule(
                user_id=req.user_id,
                concept_id=concept_id,
                next_revision_date=date.today() + timedelta(days=1),
                interval_days=1,
                ease_factor=2.5,
                repetitions=0
            )
            db.add(revision)

    db.commit()
    return {"success": True, "message": "Batch completed, words added to revision"}

# ── COMPLETE QUIZ ─────────────────────────────────────────────────────────────
class CompleteQuizRequest(BaseModel):
    user_id: int
    type: str = "word"

@router.post("/complete-quiz")
def complete_quiz(req: CompleteQuizRequest, db: Session = Depends(get_db)):
    progress = db.query(LearningProgress)\
        .filter(LearningProgress.user_id == req.user_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    # Mark quiz done and advance to next batch
    progress.quiz_completed = True
    progress.current_batch += 1
    history = _upsert_history(db, req.user_id, progress.current_batch - 1, req.type)
    history.quiz_completed = True
    history.date = date.today()
    db.commit()

    return {
        "success": True,
        "next_batch": progress.current_batch
    }


@router.get("/history")
def get_history(user_id: int, type: str = "word", db: Session = Depends(get_db)):
    rows = db.query(LearningHistory).filter(
        LearningHistory.user_id == user_id,
        LearningHistory.type == type
    ).order_by(LearningHistory.day.asc()).all()
    return {
        "success": True,
        "history": [
            {
                "day": r.day,
                "date": r.date.isoformat(),
                "batch_completed": r.batch_completed,
                "quiz_completed": r.quiz_completed,
                "items_done": r.items_done,
                "total_items": r.total_items,
            } for r in rows
        ]
    }


@router.get("/day-detail")
def get_day_detail(user_id: int, day: int, type: str = "word", limit: int = 20, db: Session = Depends(get_db)):
    items = db.query(ContentItem).filter(
        ContentItem.day == day,
        ContentItem.type == type
    ).order_by(ContentItem.item_order.asc(), ContentItem.id.asc()).limit(limit).all()

    history = db.query(LearningHistory).filter(
        LearningHistory.user_id == user_id,
        LearningHistory.day == day,
        LearningHistory.type == type
    ).first()

    return {
        "success": True,
        "items": [
            {
                "concept_id": i.concept_id,
                "title": i.title,
                "definition": i.definition,
                "metadata": i.extra_data,
                "day": i.day,
                "order": i.item_order,
                "type": i.type,
            } for i in items
        ],
        "history": {
            "batch_completed": history.batch_completed if history else False,
            "quiz_completed": history.quiz_completed if history else False,
            "items_done": history.items_done if history else 0,
            "total_items": history.total_items if history else len(items),
        },
    }
