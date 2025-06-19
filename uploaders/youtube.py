import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


class YouTubeUploader:
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    def __init__(self):
        self.service = None
        self.credentials_file = 'credentials/youtube_credentials.json'
        self.token_file = 'credentials/youtube_token.json'

    def authenticate(self, client_id, client_secret):
        credentials_data = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"]
            }
        }

        os.makedirs('credentials', exist_ok=True)
        with open(self.credentials_file, 'w') as f:
            json.dump(credentials_data, f)

        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())

        self.service = build('youtube', 'v3', credentials=creds)
        return True

    def upload(self, video_path, title, description, tags, category, privacy, made_for_kids=False):
        if not self.service:
            raise Exception("YouTube service not authenticated. Call authenticate() first.")

        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags_list,
                'categoryId': self._get_category_id(category)
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': made_for_kids
            }
        }

        media = MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True,
            mimetype='video/*'
        )

        try:
            request = self.service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Upload progress: {int(status.progress() * 100)}%")

            print(f"YouTube upload successful! Video ID: {response['id']}")
            return response['id']

        except HttpError as e:
            print(f"YouTube upload error: {e}")
            raise e

    def _get_category_id(self, category):
        category_map = {
            'Gaming': '20',
            'Entertainment': '24',
            'Comedy': '23',
            'Music': '10',
            'Sports': '17',
            'Education': '27',
            'Technology': '28',
            'Lifestyle': '22'
        }
        return category_map.get(category, '22')