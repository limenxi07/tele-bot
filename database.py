import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- DATABASE SETUP --- #
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
SGT = timezone(timedelta(hours=8)) # defaults to SGT

# --- DATABASE MODEL --- #
class Event(Base):
    """Event model for storing extracted event details"""
    __tablename__ = "events"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User who submitted the event
    user_id = Column(BigInteger, nullable=False)
    username = Column(String(255))
    
    # Event details (extracted from LLM)
    title = Column(String(500), nullable=False)
    event_type = Column(String(100), nullable=False)
    date = Column(String(200), nullable=False)
    location = Column(String(500))
    synopsis = Column(Text, nullable=False)
    organisation = Column(String(300))
    fee = Column(String(100))
    signup_link = Column(Text)
    deadline = Column(String(200))
    target_audience = Column(String(300))
    refreshments = Column(String(200))
    key_speakers = Column(Text)
    
    # Raw message for reference
    raw_message = Column(Text, nullable=False)
    
    # User interaction tracking
    user_interested = Column(Boolean, default=None)  # None = not swiped, True = interested, False = not interested
    
    # Metadata
    date_created = Column(DateTime, default=datetime.utcnow)
    parse_error = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', user_id={self.user_id})>"


def init_db():
    """Initialize database - creates all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database operations
def save_event(event_data: dict, user_id: int, username: str, raw_message: str) -> Event:
    """Save an extracted event to the database"""
    db = SessionLocal()
    try:
        event = Event(
            user_id=user_id,
            username=username,
            title=event_data.get('title'),
            event_type=event_data.get('event_type'),
            date=event_data.get('date'),
            location=event_data.get('location'),
            synopsis=event_data.get('synopsis'),
            organisation=event_data.get('organisation'),
            fee=event_data.get('fee'),
            signup_link=event_data.get('signup_link'),
            deadline=event_data.get('deadline'),
            target_audience=event_data.get('target_audience'),
            refreshments=event_data.get('refreshments'),
            key_speakers=event_data.get('key_speakers'),
            raw_message=raw_message,
            parse_error=event_data.get('parse_error', False)
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        print(f"✅ Event saved to database: ID={event.id}")
        return event
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error saving event: {e}")
        raise
    finally:
        db.close()


def get_user_events(user_id: int):
    """Get all events submitted by a user"""
    db = SessionLocal()
    try:
        events = db.query(Event).filter(Event.user_id == user_id).order_by(Event.date_created.desc()).all()
        return events
    finally:
        db.close()


def get_event_by_id(event_id: int):
    """Get a specific event by ID"""
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        return event
    finally:
        db.close()


def update_event_interest(event_id: int, interested: bool):
    """Update user's interest in an event (for swipe functionality)"""
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if event:
            event.user_interested = interested
            db.commit()
            print(f"✅ Event {event_id} interest updated: {interested}")
        return event
    finally:
        db.close()


if __name__ == "__main__":
    # Run this file directly to initialize the database
    print("Initializing database...")
    init_db()