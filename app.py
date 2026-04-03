from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from event_parser import parse_events
from calendar_client import create_event
from datetime import date
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.form.get('Body', '').strip()
    resp = MessagingResponse()
    msg = resp.message()

    if not incoming_msg:
        msg.body("Send me an event like: '2 PM to 3 PM lunch' or '5:30 PM meeting with manager'")
        return str(resp)

    try:
        today = date.today().isoformat()
        events = parse_events(incoming_msg, today)

        if not events:
            msg.body("Couldn't find any events. Try: '3 PM meeting with John' or '2-3 PM lunch'")
            return str(resp)

        created = []
        for event in events:
            link = create_event(
                title=event['title'],
                date=event['date'],
                start_time=event['start_time'],
                end_time=event.get('end_time'),
            )
            time_str = f"{event['start_time']}"
            if event.get('end_time'):
                time_str += f" - {event['end_time']}"
            created.append(f"- {event['title']} @ {time_str}")

        msg.body("Added to calendar:\n" + "\n".join(created))

    except Exception as e:
        logging.error(f"Error processing message: {e}", exc_info=True)
        msg.body("Something went wrong. Please try again.")

    return str(resp)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
