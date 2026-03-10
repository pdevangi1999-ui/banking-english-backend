from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import RevisionSchedule

# Spaced Repetition intervals in days
INTERVALS = [1, 3, 7, 14, 30]

def create_revision_entry(db: Session, user_id: int, concept_id: str, concept_name: str):
    """Create a new revision entry after a concept is learned"""
    # Check if already exists
    existing = db.query(RevisionSchedule).filter(
        RevisionSchedule.user_id == user_id,
        RevisionSchedule.concept_id == concept_id
    ).first()
    
    if existing:
        return existing
    
    entry = RevisionSchedule(
        user_id=user_id,
        concept_id=concept_id,
        concept_name=concept_name,
        next_revision_date=datetime.utcnow() + timedelta(days=1),
        interval_days=1,
        ease_factor=2.5,
        last_result="new",
        repetitions=0,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def update_revision_result(db: Session, user_id: int, concept_id: str, result: str):
    """
    Update revision schedule using SM-2 algorithm.
    result: 'good' (knew it) or 'forgot' (didn't know)
    """
    entry = db.query(RevisionSchedule).filter(
        RevisionSchedule.user_id == user_id,
        RevisionSchedule.concept_id == concept_id
    ).first()
    
    if not entry:
        return None
    
    if result == "good":
        entry.repetitions += 1
        # SM-2: increase interval
        if entry.repetitions <= len(INTERVALS):
            new_interval = INTERVALS[min(entry.repetitions - 1, len(INTERVALS) - 1)]
        else:
            new_interval = int(entry.interval_days * entry.ease_factor)
        
        # Increase ease factor slightly
        entry.ease_factor = min(entry.ease_factor + 0.1, 3.0)
        entry.interval_days = new_interval
        entry.last_result = "good"
    else:
        # Reset on forgetting
        entry.repetitions = 0
        entry.interval_days = 1
        entry.ease_factor = max(entry.ease_factor - 0.2, 1.3)
        entry.last_result = "forgot"
    
    entry.next_revision_date = datetime.utcnow() + timedelta(days=entry.interval_days)
    db.commit()
    db.refresh(entry)
    return entry

def get_due_today(db: Session, user_id: int) -> list:
    """Get concepts due for revision today"""
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    
    entries = db.query(RevisionSchedule).filter(
        RevisionSchedule.user_id == user_id,
        RevisionSchedule.next_revision_date <= tomorrow
    ).all()
    
    return entries

def get_upcoming(db: Session, user_id: int, days: int = 7) -> list:
    """Get concepts due in the next N days"""
    now = datetime.utcnow()
    future = now + timedelta(days=days)
    tomorrow = now + timedelta(days=1)
    
    entries = db.query(RevisionSchedule).filter(
        RevisionSchedule.user_id == user_id,
        RevisionSchedule.next_revision_date > tomorrow,
        RevisionSchedule.next_revision_date <= future
    ).order_by(RevisionSchedule.next_revision_date).all()
    
    return entries
