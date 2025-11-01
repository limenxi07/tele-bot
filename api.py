import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from sqlalchemy.orm import Session
from database import get_db, Event, SessionLocal, validate_and_use_token, SGT

app = FastAPI(title="EventSort API", version="1.0.0")

# Enable CORS so React frontend can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums for filtering
class EventFilter(str, Enum):
    ALL = "all"
    UPCOMING = "upcoming"
    URGENT = "urgent"  # Within next 7 days


# Pydantic models for request/response validation
class ErrorResponse(BaseModel):
    error: str
    code: str
    status: int


class EventResponse(BaseModel):
    id: int
    user_id: int
    username: str
    title: str
    event_type: str
    date: str
    location: Optional[str]
    synopsis: str
    organisation: Optional[str]
    fee: Optional[float]
    signup_link: Optional[str]
    deadline: Optional[str]
    target_audience: Optional[str]
    refreshments: Optional[str]
    key_speakers: Optional[str]
    raw_message: Optional[str] = None  # Only included if requested
    user_interested: Optional[bool]
    date_created: str
    
    class Config:
        from_attributes = True


class SwipeRequest(BaseModel):
    interested: bool  # True = swipe right, False = swipe left


class AuthResponse(BaseModel):
    user_id: int
    username: str
    message: str


# Helper function to parse event dates
def parse_event_date(date_str: str) -> Optional[datetime]:
    """
    Attempt to parse various date formats from event dates.
    Returns None if parsing fails.
    """
    if not date_str or date_str.lower() in ['tbc', 'ongoing', 'none']:
        return None
    
    # Common formats in your events
    formats = [
        "%d %b %Y, %I:%M %p",  # "4 Nov 2025, 5:30 PM"
        "%d %b %Y",  # "4 Nov 2025"
        "%d-%d %b %Y",  # "8-9 Nov 2025"
        "%d %b, %I:%M %p",  # "4 Nov, 5:30 PM" (assume current year)
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str.split(',')[0].strip(), fmt.split(',')[0])
            # If year not in string, assume current year
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except:
            continue
    
    return None


def filter_events_by_date(events: List[Event], filter_type: EventFilter) -> List[Event]:
    """Filter events based on date criteria"""
    if filter_type == EventFilter.ALL:
        return events
    
    now = datetime.now(SGT).replace(tzinfo=None)
    filtered = []
    
    for event in events:
        event_date = parse_event_date(event.date)
        
        if not event_date:
            # If can't parse date, include in "upcoming" but not "urgent"
            if filter_type == EventFilter.UPCOMING:
                filtered.append(event)
            continue
        
        if filter_type == EventFilter.UPCOMING:
            if event_date >= now:
                filtered.append(event)
        
        elif filter_type == EventFilter.URGENT:
            week_from_now = now + timedelta(days=7)
            if now <= event_date <= week_from_now:
                filtered.append(event)
    
    return filtered


# Dependency to get current user from token
def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Validate user session. 
    Expects Authorization header with format: "Bearer <user_id>"
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Not authenticated",
                "code": "UNAUTHORIZED",
                "status": 401
            }
        )
    
    try:
        # Extract user_id from "Bearer <user_id>"
        scheme, user_id = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Invalid authentication scheme",
                    "code": "INVALID_AUTH_SCHEME",
                    "status": 401
                }
            )
        
        return {"user_id": int(user_id)}
    except:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Invalid authentication",
                "code": "INVALID_AUTH",
                "status": 401
            }
        )


# API Endpoints

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "EventBot API is running"}


@app.post("/auth/validate-token", response_model=AuthResponse)
def validate_token(token: str):
    """
    Validate a one-time token from Telegram bot.
    Returns user info and marks token as used.
    Frontend should call this on page load with token from URL.
    """
    user_info = validate_and_use_token(token)
    
    if not user_info:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Invalid or expired token",
                "code": "INVALID_TOKEN",
                "status": 401
            }
        )
    
    return {
        "user_id": user_info["user_id"],
        "username": user_info["username"],
        "message": "Authentication successful"
    }


@app.get("/events", response_model=List[EventResponse])
def get_events(
    filter: EventFilter = Query(EventFilter.UPCOMING, description="Filter events by date"),
    include_raw: bool = Query(False, description="Include raw message text"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get unread events for the authenticated user.
    Returns events that haven't been swiped yet (user_interested = NULL).
    
    Filters:
    - all: All events (past and future)
    - upcoming: Only events that haven't passed yet (default)
    - urgent: Events happening within the next 7 days
    """
    user_id = current_user["user_id"]
    
    # Get events for this user that haven't been swiped
    events = db.query(Event)\
        .filter(Event.user_id == user_id)\
        .filter(Event.user_interested == None)\
        .order_by(Event.date_created.desc())\
        .all()
    
    # Apply date filtering
    events = filter_events_by_date(events, filter)
    
    # Convert to response models, conditionally including raw_message
    response = []
    for event in events:
        event_dict = {
            "id": event.id,
            "user_id": event.user_id,
            "username": event.username,
            "title": event.title,
            "event_type": event.event_type,
            "date": event.date,
            "location": event.location,
            "synopsis": event.synopsis,
            "organisation": event.organisation,
            "fee": event.fee,
            "signup_link": event.signup_link,
            "deadline": event.deadline,
            "target_audience": event.target_audience,
            "refreshments": event.refreshments,
            "key_speakers": event.key_speakers,
            "user_interested": event.user_interested,
            "date_created": str(event.date_created)
        }
        
        if include_raw:
            event_dict["raw_message"] = event.raw_message
        
        response.append(EventResponse(**event_dict))
    
    return response


@app.get("/events/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    include_raw: bool = Query(True, description="Include raw message text"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific event by ID (must belong to authenticated user)"""
    user_id = current_user["user_id"]
    
    event = db.query(Event)\
        .filter(Event.id == event_id)\
        .filter(Event.user_id == user_id)\
        .first()
    
    if not event:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Event not found",
                "code": "EVENT_NOT_FOUND",
                "status": 404
            }
        )
    
    # Build response
    event_dict = {
        "id": event.id,
        "user_id": event.user_id,
        "username": event.username,
        "title": event.title,
        "event_type": event.event_type,
        "date": event.date,
        "location": event.location,
        "synopsis": event.synopsis,
        "organisation": event.organisation,
        "fee": event.fee,
        "signup_link": event.signup_link,
        "deadline": event.deadline,
        "target_audience": event.target_audience,
        "refreshments": event.refreshments,
        "key_speakers": event.key_speakers,
        "user_interested": event.user_interested,
        "date_created": str(event.date_created)
    }
    
    if include_raw:
        event_dict["raw_message"] = event.raw_message
    
    return EventResponse(**event_dict)


@app.post("/events/{event_id}/swipe")
def swipe_event(
    event_id: int,
    swipe: SwipeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Record user's swipe on an event.
    interested=True means swipe right (interested)
    interested=False means swipe left (not interested)
    """
    user_id = current_user["user_id"]
    
    event = db.query(Event)\
        .filter(Event.id == event_id)\
        .filter(Event.user_id == user_id)\
        .first()
    
    if not event:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Event not found",
                "code": "EVENT_NOT_FOUND",
                "status": 404
            }
        )
    
    # Update user interest
    event.user_interested = swipe.interested
    db.commit()
    db.refresh(event)
    
    return {
        "success": True,
        "event_id": event_id,
        "interested": swipe.interested,
        "message": f"Swipe {'right' if swipe.interested else 'left'} recorded"
    }


@app.get("/events/interested/all", response_model=List[EventResponse])
def get_interested_events(
    include_raw: bool = Query(False, description="Include raw message text"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all events the user swiped right on (interested)"""
    user_id = current_user["user_id"]
    
    events = db.query(Event)\
        .filter(Event.user_id == user_id)\
        .filter(Event.user_interested == True)\
        .order_by(Event.date_created.desc())\
        .all()
    
    # Convert to response models
    response = []
    for event in events:
        event_dict = {
            "id": event.id,
            "user_id": event.user_id,
            "username": event.username,
            "title": event.title,
            "event_type": event.event_type,
            "date": event.date,
            "location": event.location,
            "synopsis": event.synopsis,
            "organisation": event.organisation,
            "fee": event.fee,
            "signup_link": event.signup_link,
            "deadline": event.deadline,
            "target_audience": event.target_audience,
            "refreshments": event.refreshments,
            "key_speakers": event.key_speakers,
            "user_interested": event.user_interested,
            "date_created": str(event.date_created)
        }
        
        if include_raw:
            event_dict["raw_message"] = event.raw_message
        
        response.append(EventResponse(**event_dict))
    
    return response


@app.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get statistics about events for authenticated user"""
    user_id = current_user["user_id"]
    
    query = db.query(Event).filter(Event.user_id == user_id)
    
    total = query.count()
    interested = query.filter(Event.user_interested == True).count()
    not_interested = query.filter(Event.user_interested == False).count()
    pending = query.filter(Event.user_interested == None).count()
    
    # Get urgent events count (within 7 days)
    all_events = query.filter(Event.user_interested == None).all()
    urgent = len(filter_events_by_date(all_events, EventFilter.URGENT))
    
    return {
        "total_events": total,
        "interested": interested,
        "not_interested": not_interested,
        "pending_swipes": pending,
        "urgent_events": urgent
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)