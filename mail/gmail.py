import base64
import os
import pickle
from email import errors
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

PROJECT_ID = 'class-invoices'
OAUTH_CLIENT_ID = '344465743544-80i03jq6qvshuva8gsd1o6558suotq4e.apps.googleusercontent.com'
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

CLIENT_CONFIG = {
    "installed": {
        "client_id": OAUTH_CLIENT_ID,
        "project_id": PROJECT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "W432Lbc0PUlUSTZN3HdSxFJH",
        "redirect_uris": [
            "urn:ietf:wg:oauth:2.0:oob",
            "http://localhost"
        ]
    }
}


def get_credentials_dir():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    return credential_dir


def authenticate():
    """Shows basic usage of the Gmail API."""
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = os.path.join(get_credentials_dir(), 'token.pickle')
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            credentials = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
            credentials = flow.run_local_server()
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(credentials, token)
    return credentials


def get_gmail_service():
    credentials = authenticate()
    return build('gmail', 'v1', credentials=credentials)


def create_message_with_attachment(sender, recipients, subject, message_text, data):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      recipients: List of email addresses to receive the message.
      subject: The subject of the email message.
      message_text: The text of the email message.
      data: The contents of the attachment.

    Returns:
      An object containing a base64url encoded email object.
    """

    message = MIMEMultipart()
    message['to'] = ', '.join(recipients)
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text)
    message.attach(msg)

    # For our purposes, assume PDF data
    msg = MIMEApplication(data, _subtype='pdf')
    msg.add_header('Content-Disposition', 'attachment', filename='invoice.pdf')
    message.attach(msg)

    return {'raw': str(base64.urlsafe_b64encode(message.as_bytes()).decode())}


def send_message(service, user_id, message):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message.
    """
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def create_draft(service, user_id, message_body):
    """Create and insert a draft email. Print the returned draft's message and id.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
               can be used to indicate the authenticated user.
      message_body: The body of the email message, including headers.

    Returns:
      Draft object, including draft id and message meta data.
    """
    try:
        draft = None  # TODO
        # message = {'message': message_body}
        # draft = service.users().drafts().create(userId=user_id, body=message).execute()
        # draft['id'] = 'r-1943780435138709657'
        # draft['message'] = {'id': '1696980219206a02', 'threadId': '1696980219206a02', 'labelIds': ['DRAFT']}

        return draft
    except errors.MessageError as e:
        print('An error occurred: {}'.format(e))
        return None
