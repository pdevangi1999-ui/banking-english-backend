from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database.db import get_db
from database.models import User
from services.auth_service import hash_password, verify_password, create_token, encrypt_api_key, decrypt_api_key

router = APIRouter(prefix="/auth", tags=["Auth"])

class SignupRequest(BaseModel):
    email: str
    password: str
    gemini_api_key: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    # Check existing user
    existing = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate Gemini key format
    if not req.gemini_api_key.strip().startswith("AIza"):
        raise HTTPException(status_code=400, detail="Invalid Gemini API key format")
    
    # Create user
    user = User(
        email=req.email.lower().strip(),
        hashed_password=hash_password(req.password),
        gemini_api_key_encrypted=encrypt_api_key(req.gemini_api_key.strip()),
        teaching_style="example_heavy",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_token(user.id)
    return {
        "message": "Account created successfully",
        "token": token,
        "user_id": user.id,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "teaching_style": user.teaching_style,
            "created_at": str(user.created_at),
        }
    }

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user.id)
    return {
        "token": token,
        "user_id": user.id,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "teaching_style": user.teaching_style,
            "created_at": str(user.created_at),
        }
    }
