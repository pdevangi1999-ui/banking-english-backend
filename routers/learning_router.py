from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.db import get_db
from database.models import User, LearningProgress, RevisionSchedule
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

# ── COMPLETE BATCH ────────────────────────────────────────────────────────────
class CompleteBatchRequest(BaseModel):
    user_id: int
    concept_ids: list[str]   # the 10 words from today's batch

@router.post("/complete-batch")
def complete_batch(req: CompleteBatchRequest, db: Session = Depends(get_db)):
    progress = db.query(LearningProgress)\
        .filter(LearningProgress.user_id == req.user_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    # Mark batch as completed
    progress.batch_completed = True
    progress.last_updated = date.today()

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
                next_review=date.today() + timedelta(days=1),
                interval=1,
                ease_factor=2.5,
                repetitions=0
            )
            db.add(revision)

    db.commit()
    return {"success": True, "message": "Batch completed, words added to revision"}

# ── COMPLETE QUIZ ─────────────────────────────────────────────────────────────
class CompleteQuizRequest(BaseModel):
    user_id: int

@router.post("/complete-quiz")
def complete_quiz(req: CompleteQuizRequest, db: Session = Depends(get_db)):
    progress = db.query(LearningProgress)\
        .filter(LearningProgress.user_id == req.user_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    # Mark quiz done and advance to next batch
    progress.quiz_completed = True
    progress.current_batch += 1
    db.commit()

    return {
        "success": True,
        "next_batch": progress.current_batch
    }