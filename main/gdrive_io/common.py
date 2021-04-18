from pathlib import Path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from main.constants import DATASETS_GDRIVE_FOLDER_NAME, SECRETS_DIR


class GDriveTypes:
    folder = 'application/vnd.google-apps.folder'
    csv = 'text/csv'
    xml = 'text/xml'
    binary = 'application/octet-stream'


def find_dataset_folder_gdrive_id(drive_service):
    files = list_folder(drive_service, folder_id=None, folder_name=DATASETS_GDRIVE_FOLDER_NAME)
    real_folders = [i for i in files if i.get('mimeType') == GDriveTypes.folder]
    return real_folders[0].get('id')


def list_folder(drive_service, folder_id, folder_name=None):
    if folder_name is None:
        request = f"'{folder_id}' in parents and trashed=false"
    else:
        request = f"name = '{folder_name}'"

    page_token = None
    files = []
    while True:
        response = drive_service.files().list(q=request,
                                              spaces='drive',
                                              fields='nextPageToken, files(id, name, mimeType)',
                                              pageToken=page_token).execute()
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    return files


def new_service():
    scopes = ['https://www.googleapis.com/auth/drive']
    token_path = Path(SECRETS_DIR) / 'token.json'
    client_secrets_path = Path(SECRETS_DIR) / 'client_secrets.json'

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, scopes)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)
