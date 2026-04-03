import anthropic
import json
import os
from datetime import date, timedelta

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))


def parse_message(message: str, today: str) -> dict:
    """
    Parse intent and extract structured data from a natural language message.

    Returns one of:
      {"intent": "create", "events": [...]}
      {"intent": "view", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "label": "..."}
      {"intent": "delete", "title": "...", "date": "YYYY-MM-DD", "start_time": "HH:MM|null"}
      {"intent": "edit", "target": {...}, "updates": {...}}
    """
    tomorrow = (date.fromisoformat(today) + timedelta(days=1)).isoformat()
    week_end = (date.fromisoformat(today) + timedelta(days=6)).isoformat()
    next_week_start = (date.fromisoformat(today) + timedelta(days=7)).isoformat()
    next_week_end = (date.fromisoformat(today) + timedelta(days=13)).isoformat()

    prompt = f"""You are a calendar assistant. Classify the intent and extract structured data.

Today is {today}. Tomorrow is {tomorrow}. This week ends {week_end}. Next week is {next_week_start} to {next_week_end}.

Message: "{message}"

Classify as one of: create, view, delete, edit.

Return ONLY valid JSON in exactly one of these formats (no explanation, no markdown):

CREATE - user wants to add event(s):
{{"intent": "create", "events": [{{"title": "...", "date": "YYYY-MM-DD", "start_time": "HH:MM", "end_time": "HH:MM or null"}}]}}

VIEW - user wants to see their schedule:
{{"intent": "view", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "label": "today/tomorrow/this week/next week/etc"}}

DELETE - user wants to remove an event:
{{"intent": "delete", "title": "...", "date": "YYYY-MM-DD", "start_time": "HH:MM or null"}}

EDIT - user wants to modify an existing event:
{{"intent": "edit", "target": {{"title": "...", "date": "YYYY-MM-DD", "start_time": "HH:MM or null"}}, "updates": {{"title": "...", "date": "YYYY-MM-DD", "start_time": "HH:MM", "end_time": "HH:MM"}}}}
(only include fields in "updates" that are actually changing)

Rules:
- Use today ({today}) if no date mentioned
- Convert 12h to 24h (2 PM → 14:00, 5:56 PM → 17:56)
- "this week" = {today} to {week_end}
- "next week" = {next_week_start} to {next_week_end}
- "today" = {today} to {today}
- "tomorrow" = {tomorrow} to {tomorrow}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(text)
