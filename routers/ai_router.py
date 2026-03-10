from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.db import get_db
from database.models import User, AiGeneratedContent
from services.auth_service import decrypt_api_key
from services import ai_service

router = APIRouter(prefix="/ai", tags=["AI"])

def get_user_api_key(user_id: int, db: Session) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return decrypt_api_key(user.gemini_api_key_encrypted)

class ExplainRequest(BaseModel):
    user_id: int
    concept_id: str
    teaching_style: str = "example_heavy"

class ExerciseRequest(BaseModel):
    user_id: int
    concept_id: str
    difficulty: str = "basic"

class RevisionRequest(BaseModel):
    user_id: int
    concept_id: str

@router.post("/explain")
def explain(req: ExplainRequest, db: Session = Depends(get_db)):
    # Check if content already exists (reuse to save API calls)
    existing = db.query(AiGeneratedContent).filter(
        AiGeneratedContent.user_id == req.user_id,
        AiGeneratedContent.concept_id == req.concept_id,
        AiGeneratedContent.content_type == "explanation",
        AiGeneratedContent.teaching_style == req.teaching_style,
    ).first()
    
    if existing:
        return {"explanation": existing.content_json.get("text", ""), "cached": True}
    
    # Generate new content
    api_key = get_user_api_key(req.user_id, db)
    try:
        explanation = ai_service.generate_explanation(api_key, req.concept_id, req.teaching_style)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
    
    # Cache it
    content = AiGeneratedContent(
        user_id=req.user_id,
        concept_id=req.concept_id,
        content_type="explanation",
        teaching_style=req.teaching_style,
        content_json={"text": explanation},
    )
    db.add(content)
    db.commit()
    
    return {"explanation": explanation, "cached": False}

@router.post("/exercises")
def exercises(req: ExerciseRequest, db: Session = Depends(get_db)):
    api_key = get_user_api_key(req.user_id, db)
    try:
        exs = ai_service.generate_exercises(api_key, req.concept_id, req.difficulty)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
    
    # Cache it
    content = AiGeneratedContent(
        user_id=req.user_id,
        concept_id=req.concept_id,
        content_type="exercises",
        teaching_style="",
        difficulty=req.difficulty,
        content_json={"exercises": exs},
    )
    db.add(content)
    db.commit()
    
    return {"exercises": exs}

@router.post("/revision-questions")
def revision_questions(req: RevisionRequest, db: Session = Depends(get_db)):
    api_key = get_user_api_key(req.user_id, db)
    try:
        questions = ai_service.generate_revision_questions(api_key, req.concept_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
    
    return {"questions": questions}
