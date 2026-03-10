from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.db import get_db
from services.revision_service import get_due_today, get_upcoming, update_revision_result

router = APIRouter(prefix="/revision", tags=["Revision"])

class RevisionUpdateRequest(BaseModel):
    user_id: int
    concept_id: str
    result: str  # "good" or "forgot"

@router.get("/daily")
def daily_revision(user_id: int, db: Session = Depends(get_db)):
    due = get_due_today(db, user_id)
    upcoming = get_upcoming(db, user_id)
    
    return {
        "due_today": [
            {
                "concept_id": r.concept_id,
                "concept_name": r.concept_name or r.concept_id.replace("_", " ").title(),
                "interval_days": r.interval_days,
                "next_revision_date": str(r.next_revision_date),
                "ease_factor": r.ease_factor,
                "last_result": r.last_result,
            } for r in due
        ],
        "upcoming": [
            {
                "concept_id": r.concept_id,
                "concept_name": r.concept_name or r.concept_id.replace("_", " ").title(),
                "interval_days": r.interval_days,
                "next_revision_date": str(r.next_revision_date),
            } for r in upcoming
        ],
    }

@router.post("/update")
def update_revision(req: RevisionUpdateRequest, db: Session = Depends(get_db)):
    entry = update_revision_result(db, req.user_id, req.concept_id, req.result)
    if not entry:
        return {"message": "No revision entry found", "created": False}
    return {
        "message": "Revision updated",
        "next_revision_date": str(entry.next_revision_date),
        "interval_days": entry.interval_days,
    }
