from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

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

# ── Health check MUST be registered before anything else ──
@app.get("/health")
def health():
    return JSONResponse(content={"status": "healthy"}, status_code=200)

@app.get("/")
def root():
    return JSONResponse(content={
        "app": "BankEnglish AI",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }, status_code=200)

# ── Load routers and database AFTER health check ──
from database.db import init_db
from routers import auth_router, quiz_router, ai_router, student_router, revision_router

app.include_router(auth_router.router)
app.include_router(quiz_router.router)
app.include_router(ai_router.router)
app.include_router(student_router.router)
app.include_router(revision_router.router)

@app.on_event("startup")
def on_startup():
    try:
        init_db()
        print("✅ Database tables created")
    except Exception as e:
        print(f"⚠️ Database init error: {e}")
    print("✅ BankEnglish AI backend started")