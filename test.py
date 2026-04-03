from dotenv import load_dotenv
load_dotenv()

from event_parser import parse_message
from calendar_client import create_event, list_events, find_event, delete_event, update_event
from datetime import date

today = date.today().isoformat()

tests = [
    "2 PM to 3 PM lunch and 5:30 PM meeting with manager",
    "what's this week?",
    "delete lunch today",
    "move 5:30 PM meeting to 6 PM",
]

for msg in tests:
    print(f"\n--- '{msg}' ---")
    result = parse_message(msg, today)
    print(f"Parsed: {result}")
