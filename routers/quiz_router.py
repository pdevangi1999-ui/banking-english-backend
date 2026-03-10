from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Any
from database.db import get_db
from database.models import StudentAttempt, ConceptMastery, User
from services.revision_service import create_revision_entry

router = APIRouter(prefix="/quiz", tags=["Quiz"])

class QuizAttemptRequest(BaseModel):
    user_id: int
    quiz_id: str
    concept_id: str
    score: int
    total: int
    answers: List[Any] = []

@router.post("/attempt")
def submit_attempt(req: QuizAttemptRequest, db: Session = Depends(get_db)):
    percentage = (req.score / req.total * 100) if req.total > 0 else 0
    
    # Save attempt
    attempt = StudentAttempt(
        user_id=req.user_id,
        quiz_id=req.quiz_id,
        concept_id=req.concept_id,
        score=req.score,
        total=req.total,
        percentage=percentage,
        answers=req.answers,
    )
    db.add(attempt)
    
    # Update mastery
    mastery = db.query(ConceptMastery).filter(
        ConceptMastery.user_id == req.user_id,
        ConceptMastery.concept_id == req.concept_id,
    ).first()
    
    concept_name = req.concept_id.replace("_", " ").title()
    
    if mastery:
        # Running average
        total_attempts = mastery.total_attempts + 1
        new_score = ((mastery.mastery_score * mastery.total_attempts) + percentage) / total_attempts
        mastery.mastery_score = round(new_score, 2)
        mastery.total_attempts = total_attempts
        if percentage >= 60:
            mastery.correct_attempts += 1
        mastery.is_weak = mastery.mastery_score < 60
    else:
        mastery = ConceptMastery(
            user_id=req.user_id,
            concept_id=req.concept_id,
            concept_name=concept_name,
            mastery_score=round(percentage, 2),
            total_attempts=1,
            correct_attempts=1 if percentage >= 60 else 0,
            is_weak=percentage < 60,
        )
        db.add(mastery)
    
    db.commit()
    
    # Add to revision schedule
    create_revision_entry(db, req.user_id, req.concept_id, concept_name)
    
    return {
        "message": "Attempt saved",
        "percentage": round(percentage, 2),
        "is_weak": percentage < 60,
        "mastery_score": mastery.mastery_score,
    }
