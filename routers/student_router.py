from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.db import get_db
from database.models import User, ConceptMastery

router = APIRouter(prefix="/student", tags=["Student"])

class TeachingStyleRequest(BaseModel):
    user_id: int
    teaching_style: str

@router.get("/profile")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user.id),
        "email": user.email,
        "teaching_style": user.teaching_style,
        "created_at": str(user.created_at),
        "gemini_api_key": "****configured****",
    }

@router.put("/teaching-style")
def update_teaching_style(req: TeachingStyleRequest, db: Session = Depends(get_db)):
    valid_styles = ["example_heavy", "step_by_step", "definition_first", "question_based"]
    if req.teaching_style not in valid_styles:
        raise HTTPException(status_code=400, detail=f"Style must be one of: {valid_styles}")
    
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.teaching_style = req.teaching_style
    db.commit()
    return {"message": "Teaching style updated", "teaching_style": req.teaching_style}

@router.get("/mastery")
def get_mastery(user_id: int, db: Session = Depends(get_db)):
    mastery = db.query(ConceptMastery).filter(ConceptMastery.user_id == user_id).all()
    return {
        "mastery": [
            {
                "concept_id": m.concept_id,
                "concept_name": m.concept_name or m.concept_id.replace("_", " ").title(),
                "mastery_score": m.mastery_score,
                "total_attempts": m.total_attempts,
                "correct_attempts": m.correct_attempts,
                "is_weak": m.is_weak,
                "last_attempted": str(m.last_attempted),
            } for m in mastery
        ]
    }

@router.get("/weak-concepts")
def get_weak_concepts(user_id: int, db: Session = Depends(get_db)):
    weak = db.query(ConceptMastery).filter(
        ConceptMastery.user_id == user_id,
        ConceptMastery.is_weak == True,
    ).all()
    return {
        "weak_concepts": [
            {
                "concept_id": m.concept_id,
                "concept_name": m.concept_name or m.concept_id.replace("_", " ").title(),
                "mastery_score": m.mastery_score,
            } for m in weak
        ]
    }
