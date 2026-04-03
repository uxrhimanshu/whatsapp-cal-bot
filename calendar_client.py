import os
import json
import base64
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')


def get_calendar_service():
    creds = None

    # On Render: token stored as base64-encoded JSON in env var
    token_b64 = os.getenv('GOOGLE_TOKEN_B64')
    if token_b64:
        token_data = json.loads(base64.b64decode(token_b64).decode())
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    elif os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds:
        raise RuntimeError("No Google credentials found. Run auth.py first.")

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build('calendar', 'v3', credentials=creds)


def create_event(title: str, date: str, start_time: str, end_time: str = None) -> str:
    """Create a Google Calendar event. Returns the event HTML link."""
    service = get_calendar_service()

    start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")

    if end_time:
        end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
    else:
        end_dt = start_dt + timedelta(hours=1)

    event_body = {
        'summary': title,
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': TIMEZONE,
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': TIMEZONE,
        },
    }

    event = service.events().insert(calendarId='primary', body=event_body).execute()
    return event.get('htmlLink', '')
