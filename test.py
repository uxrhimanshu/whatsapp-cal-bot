from dotenv import load_dotenv
load_dotenv()

from event_parser import parse_events
from calendar_client import create_event
from datetime import date

today = date.today().isoformat()
msg = "2 PM to 3 PM lunch and 5:30 PM meeting with manager"

print(f"Parsing: '{msg}'")
events = parse_events(msg, today)
print(f"Parsed: {events}")

for event in events:
    link = create_event(
        title=event['title'],
        date=event['date'],
        start_time=event['start_time'],
        end_time=event.get('end_time'),
    )
    print(f"Created: {event['title']} -> {link}")
