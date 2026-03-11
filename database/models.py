from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from database.db import Base
from datetime import date

class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    current_batch   = Column(Integer, default=1, nullable=False)
    batch_completed = Column(Boolean, default=False, nullable=False)
    quiz_completed  = Column(Boolean, default=False, nullable=False)
    last_updated    = Column(Date, default=date.today, nullable=False)

    
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    gemini_api_key_encrypted = Column(Text, nullable=False)
    teaching_style = Column(String(50), default="example_heavy")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class StudentAttempt(Base):
    __tablename__ = "student_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    quiz_id = Column(String(255), nullable=False)
    concept_id = Column(String(255), nullable=False)
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)
    answers = Column(JSON, default=[])
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ConceptMastery(Base):
    __tablename__ = "concept_mastery"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    concept_id = Column(String(255), nullable=False)
    concept_name = Column(String(255), default="")
    mastery_score = Column(Float, default=0.0)
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    is_weak = Column(Boolean, default=True)
    last_attempted = Column(DateTime(timezone=True), server_default=func.now())

class AiGeneratedContent(Base):
    __tablename__ = "ai_generated_content"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    concept_id = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)  # explanation / exercises / revision
    teaching_style = Column(String(50), default="example_heavy")
    difficulty = Column(String(50), default="basic")
    content_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StudentTeachingStyle(Base):
    __tablename__ = "student_teaching_style"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    teaching_style = Column(String(50), default="example_heavy")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class RevisionSchedule(Base):
    __tablename__ = "revision_schedule"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    concept_id = Column(String(255), nullable=False)
    concept_name = Column(String(255), default="")
    next_revision_date = Column(DateTime(timezone=True), nullable=False)
    interval_days = Column(Integer, default=1)
    ease_factor = Column(Float, default=2.5)
    last_result = Column(String(50), default="unknown")
    repetitions = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
