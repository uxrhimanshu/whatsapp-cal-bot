import os
import json
import base64
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')


def get_calendar_service():
    creds = None

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


def _parse_dt(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str)


def _to_range(date_str: str):
    tz = ZoneInfo(TIMEZONE)
    start = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
    end = start.replace(hour=23, minute=59, second=59)
    return start, end


def create_event(title: str, date: str, start_time: str, end_time: str = None) -> str:
    service = get_calendar_service()
    start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = (datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
              if end_time else start_dt + timedelta(hours=1))

    event = service.events().insert(calendarId='primary', body={
        'summary': title,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': TIMEZONE},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': TIMEZONE},
    }).execute()
    return event.get('htmlLink', '')


def list_events(start_date: str, end_date: str) -> list:
    """Return events between start_date and end_date inclusive."""
    service = get_calendar_service()
    tz = ZoneInfo(TIMEZONE)

    time_min = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=tz)
    time_max = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=tz)

    result = service.events().list(
        calendarId='primary',
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy='startTime',
    ).execute()

    events = []
    for item in result.get('items', []):
        start = item['start'].get('dateTime') or item['start'].get('date')
        end = item['end'].get('dateTime') or item['end'].get('date')

        if 'T' in start:
            s = _parse_dt(start)
            e = _parse_dt(end)
            events.append({
                'id': item['id'],
                'title': item.get('summary', '(No title)'),
                'date_display': s.strftime("%a %b %d"),
                'start_time': s.strftime("%H:%M"),
                'end_time': e.strftime("%H:%M"),
            })
        else:
            events.append({
                'id': item['id'],
                'title': item.get('summary', '(No title)'),
                'date_display': datetime.strptime(start, "%Y-%m-%d").strftime("%a %b %d"),
                'start_time': None,
                'end_time': None,
            })

    return events


def find_event(title: str, date: str, start_time: str = None):
    """Find the best matching event on a given date. Returns raw Google event or None."""
    service = get_calendar_service()
    time_min, time_max = _to_range(date)

    result = service.events().list(
        calendarId='primary',
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        q=title,
        singleEvents=True,
        orderBy='startTime',
    ).execute()

    items = result.get('items', [])
    if not items:
        return None

    if start_time:
        for item in items:
            dt_str = item['start'].get('dateTime', '')
            if dt_str and _parse_dt(dt_str).strftime("%H:%M") == start_time:
                return item

    return items[0]


def delete_event(event_id: str):
    get_calendar_service().events().delete(
        calendarId='primary', eventId=event_id).execute()


def update_event(event_id: str, updates: dict):
    """Patch an event. updates can contain: title, date, start_time, end_time."""
    service = get_calendar_service()
    event = service.events().get(calendarId='primary', eventId=event_id).execute()

    current_start = _parse_dt(event['start']['dateTime'])
    current_end = _parse_dt(event['end']['dateTime'])
    duration = current_end - current_start

    patch = {}

    if 'title' in updates:
        patch['summary'] = updates['title']

    new_date = updates.get('date', current_start.strftime("%Y-%m-%d"))
    new_start_time = updates.get('start_time', current_start.strftime("%H:%M"))
    new_start_dt = datetime.strptime(f"{new_date} {new_start_time}", "%Y-%m-%d %H:%M")
    patch['start'] = {'dateTime': new_start_dt.isoformat(), 'timeZone': TIMEZONE}

    if 'end_time' in updates:
        new_end_dt = datetime.strptime(f"{new_date} {updates['end_time']}", "%Y-%m-%d %H:%M")
    else:
        new_end_dt = new_start_dt + duration
    patch['end'] = {'dateTime': new_end_dt.isoformat(), 'timeZone': TIMEZONE}

    return service.events().patch(
        calendarId='primary', eventId=event_id, body=patch).execute()
