"""
Run this once locally to authenticate with Google Calendar.
It will open a browser, ask you to log in, and save token.json.

After running:
  python auth.py
  cat token.json | base64 | tr -d '\n'

Copy that output and set it as GOOGLE_TOKEN_B64 on Render.
"""

import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar']


def main():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    with open('token.json', 'w') as f:
        f.write(creds.to_json())

    print("token.json saved.")
    print()
    print("For Render deployment, set GOOGLE_TOKEN_B64 to:")
    with open('token.json', 'rb') as f:
        encoded = base64.b64encode(f.read()).decode()
    print(encoded)


if __name__ == '__main__':
    main()
