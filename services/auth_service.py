from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
import base64

SECRET_KEY = os.getenv("SECRET_KEY", "your-very-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except Exception:
        return None

# Simple encryption for Gemini API key
def encrypt_api_key(api_key: str) -> str:
    return base64.b64encode(api_key.encode()).decode()

def decrypt_api_key(encrypted: str) -> str:
    return base64.b64decode(encrypted.encode()).decode()
