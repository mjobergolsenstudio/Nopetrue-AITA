"""
Kjør denne ÉN gang på PC for å generere YouTube token.
Deretter base64-encode token.pickle og legg inn som GitHub Secret.
"""
import pickle
import base64
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS = 'client_secret.json'
TOKEN_FILE = 'token.pickle'

def main():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(creds, f)

    with open(TOKEN_FILE, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')

    print("\n✅ Token generert!")
    print("\nLegg inn dette som GitHub Secret: YOUTUBE_TOKEN_PICKLE")
    print("\n" + "=" * 60)
    print(encoded)
    print("=" * 60)

if __name__ == '__main__':
    main()
