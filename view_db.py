from database import SessionLocal, Event

db = SessionLocal()

# Get all events
events = db.query(Event).all()

print(f"📊 Total events in database: {len(events)}\n")

for event in events:
    print(f"{'='*60}")
    print(f"ID: {event.id}")
    print(f"Title: {event.title}")
    print(f"Type: {event.event_type}")
    print(f"Date: {event.date}")
    print(f"Location: {event.location}")
    print(f"Fee: ${event.fee if event.fee else 'Free'}")
    print(f"Organisation: {event.organisation}")
    print(f"Deadline: {event.deadline}")
    print(f"User: {event.username} (ID: {event.user_id})")
    print(f"Created: {event.date_created}")
    print()

db.close()