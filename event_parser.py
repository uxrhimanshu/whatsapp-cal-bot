import anthropic
import json
import os
from datetime import date, timedelta

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))


def parse_events(message: str, today: str) -> list[dict]:
    """Parse a natural language message into a list of calendar events."""
    tomorrow = (date.fromisoformat(today) + timedelta(days=1)).isoformat()

    prompt = f"""Extract all calendar events from this message.

Today is {today}. Tomorrow is {tomorrow}.

Message: "{message}"

Return a JSON array of events. Each event object must have:
- "title": string (the event name)
- "date": string in YYYY-MM-DD format (use today's date {today} if not specified)
- "start_time": string in HH:MM 24-hour format
- "end_time": string in HH:MM 24-hour format, or null (default to 1 hour after start if not given)

Rules:
- If multiple events are mentioned, return all of them
- If no date is mentioned, use today ({today})
- "tomorrow" means {tomorrow}
- Convert 12-hour time (2 PM → 14:00, 5:56 PM → 17:56, 12 PM → 12:00, 12 AM → 00:00)
- Return ONLY valid JSON, no explanation, no markdown

Examples:
Input: "2 PM to 3 PM lunch"
Output: [{{"title": "Lunch", "date": "{today}", "start_time": "14:00", "end_time": "15:00"}}]

Input: "5:56 PM meeting with manager"
Output: [{{"title": "Meeting with manager", "date": "{today}", "start_time": "17:56", "end_time": "18:56"}}]

Input: "2 PM to 3 PM lunch and 5:56 PM meeting with manager"
Output: [{{"title": "Lunch", "date": "{today}", "start_time": "14:00", "end_time": "15:00"}}, {{"title": "Meeting with manager", "date": "{today}", "start_time": "17:56", "end_time": "18:56"}}]"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(text)
