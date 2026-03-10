from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import init_db
from routers import auth_router, quiz_router, ai_router, student_router, revision_router

app = FastAPI(
    title="BankEnglish AI — Backend API",
    description="AI-powered English learning system for banking exam aspirants",
    version="1.0.0"
)

# CORS — allow Flutter app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router.router)
app.include_router(quiz_router.router)
app.include_router(ai_router.router)
app.include_router(student_router.router)
app.include_router(revision_router.router)

@app.on_event("startup")
def on_startup():
    init_db()
    print("✅ BankEnglish AI backend started")

@app.get("/")
def root():
    return {
        "app": "BankEnglish AI",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
