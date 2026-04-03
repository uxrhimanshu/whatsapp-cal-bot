from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from event_parser import parse_message
from calendar_client import create_event, list_events, find_event, delete_event, update_event
from datetime import date
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


def format_event_list(events: list, label: str) -> str:
    if not events:
        return f"No events {label}."

    by_date = {}
    for e in events:
        d = e['date_display']
        by_date.setdefault(d, []).append(e)

    lines = [f"Events {label}:"]
    for day, day_events in by_date.items():
        lines.append(f"\n{day}")
        for e in day_events:
            if e['start_time']:
                lines.append(f"  {e['start_time']}-{e['end_time']}  {e['title']}")
            else:
                lines.append(f"  (all day)  {e['title']}")

    return "\n".join(lines)


@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.form.get('Body', '').strip()
    resp = MessagingResponse()
    msg = resp.message()

    if not incoming_msg:
        msg.body("Send me a message like:\n- '3 PM lunch'\n- 'what's this week?'\n- 'delete lunch today'\n- 'move 3 PM meeting to 4 PM'")
        return str(resp)

    try:
        today = date.today().isoformat()
        result = parse_message(incoming_msg, today)
        intent = result.get('intent')

        if intent == 'create':
            events = result.get('events', [])
            if not events:
                msg.body("Couldn't find any events to add. Please include a time.")
                return str(resp)
            created = []
            for e in events:
                create_event(e['title'], e['date'], e['start_time'], e.get('end_time'))
                time_str = e['start_time']
                if e.get('end_time'):
                    time_str += f"-{e['end_time']}"
                created.append(f"- {e['title']} @ {time_str}")
            msg.body("Added to calendar:\n" + "\n".join(created))

        elif intent == 'view':
            events = list_events(result['start_date'], result['end_date'])
            msg.body(format_event_list(events, result.get('label', '')))

        elif intent == 'delete':
            event = find_event(result['title'], result['date'], result.get('start_time'))
            if not event:
                msg.body(f"Couldn't find '{result['title']}' on that day.")
            else:
                delete_event(event['id'])
                msg.body(f"Deleted: {event.get('summary', result['title'])}")

        elif intent == 'edit':
            target = result['target']
            updates = result['updates']
            event = find_event(target['title'], target['date'], target.get('start_time'))
            if not event:
                msg.body(f"Couldn't find '{target['title']}' on that day.")
            else:
                updated = update_event(event['id'], updates)
                msg.body(f"Updated: {updated.get('summary', target['title'])}")

        else:
            msg.body("Not sure what you mean. Try:\n- '3 PM lunch'\n- 'what's this week?'\n- 'delete lunch today'\n- 'move 3 PM meeting to 4 PM'")

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        msg.body("Something went wrong. Please try again.")

    return str(resp)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
