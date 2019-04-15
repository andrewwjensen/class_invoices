import base64
import logging
import os
import pickle
import threading
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import google.auth.exceptions
import oauthlib
import wx
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import app_config
from model.columns import Column
from model.family import get_students
from pdf.generate import generate_one_invoice
from util import start_thread, MyBytesIO

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

logger = logging.getLogger(f'classinvoices.{__name__}')


def get_credentials_dir():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    return credential_dir


def authenticate(force_new=False, connect_to_google=True):
    """Get credentials to authenticate to Google for using Gmail API."""
    credentials = None
    # The config key GMAIL_TOKEN_KEY stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if not force_new and app_config.conf.Exists(app_config.GMAIL_TOKEN_KEY):
        # Token is pickled and base64 encoded for storing in a text config file
        token_b64 = app_config.conf.Read(app_config.GMAIL_TOKEN_KEY)
        token = base64.b64decode(token_b64)
        credentials = pickle.loads(token)
    # If there are no (valid) credentials available, let the user log in.
    if force_new or not credentials or not credentials.valid:
        if not force_new and credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        elif connect_to_google:
            flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
            credentials = flow.run_local_server()
        else:
            # Caller did not want to retrieve new token now, just validate existing one.
            return None
        # Save the credentials in config for the next run
        token = pickle.dumps(credentials)
        token_b64 = base64.b64encode(token)
        app_config.conf.Write(app_config.GMAIL_TOKEN_KEY, token_b64)
        app_config.conf.Flush()
    return credentials


def check_credentials(parent, show_popup_if_no_action_needed=True):
    """Check if Gmail API credentials have been set up. Prompt user to set them up if not."""
    credentials = authenticate(connect_to_google=False)
    if credentials is None:
        msg = 'In order to use the email feature, you must have a Gmail account. You need to' \
              ' log in to Google and authorize this app to send email on your' \
              ' behalf. Do you wish to do this now? (You will be redirected to your browser)'
        caption = 'Google Authentication Required'
        dlg = wx.MessageDialog(parent=None,
                               message=msg,
                               caption=caption,
                               style=wx.OK | wx.CANCEL)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            wx.YieldIfNeeded()  # Make sure dialog goes away before we open a new one
            wait_dialog = wx.ProgressDialog(
                title='Waiting for response from Google...',
                message='Respond to prompts in your browser. This\n'
                        'dialog will close automatically after you\n'
                        'approve or deny the authorization request.')
            wait_dialog.Pulse()
            dialog_done = threading.Event()
            start_thread(authenticate_with_google, parent, dialog_done)
            check_for_done_loop(dialog_done)
            if parent.error_msg:
                return False
            return True
    elif show_popup_if_no_action_needed:
        dlg = wx.MessageDialog(parent=None,
                               message='Email is already properly set up.',
                               caption='No Action Needed',
                               style=wx.OK)
        dlg.ShowModal()
        dlg.Destroy()
    return credentials is not None


def authenticate_with_google(parent, dialog_done):
    """Start Google authentication process."""
    try:
        parent.error_msg = 'Unable to authorize. Please try again.'
        if authenticate():
            parent.error_msg = None
    finally:
        dialog_done.set()


def check_for_done_loop(dialog_done):
    """This is simply to make sure the application keeps responding and doesn't "freeze" as seen by the OS."""
    while not dialog_done.is_set():
        time.sleep(0.3)  # prevent tight loop
        wx.YieldIfNeeded()


def get_gmail_service():
    try:
        try:
            # Authenticate, or use refresh token
            return build('gmail', 'v1', credentials=authenticate(), cache_discovery=False)
        except google.auth.exceptions.RefreshError:
            logger.exception('Token refresh failed.')
        # Since refresh failed, user probably revoked authorization. Try restarting
        # the email authentication process and have the user approve again.
        return build('gmail', 'v1', credentials=authenticate(force_new=True))
    except oauthlib.oauth2.rfc6749.errors.OAuth2Error:
        pass
    raise RuntimeError(
        'Failed to authenticate to Google for sending mail. Please try again.')


def create_message_with_attachment(sender, recipients, cc, subject, body, data):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      recipients: List of email addresses to receive the message.
      cc: if 'cc', then cc the sender; likewise for 'bcc'; otherwise do not cc or bcc.
      subject: The subject of the email message.
      body: The text of the email message.
      data: The contents of the attachment.

    Returns:
      An object containing a base64url encoded email object.
    """

    message = MIMEMultipart()
    message['to'] = ', '.join(recipients)
    message['from'] = sender
    message['subject'] = subject
    if cc == 'cc':
        message['cc'] = sender
    elif cc == 'bcc':
        message['bcc'] = sender

    body = MIMEText(body)
    message.attach(body)

    # For our purposes, assume PDF data
    attachment = MIMEApplication(data, _subtype='pdf')
    filename = 'class_invoice.pdf'
    # For some reason, must set this for PDF to appear correctly in Apple Mail. Without it, the
    # 'Content-ID' and 'X-Attachment-Id' headers appear but are empty, apparently causing the issue.
    attachment.add_header('X-Attachment-Id', filename)
    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(attachment)

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
    message = service.users().messages().send(userId=user_id, body=message).execute()
    return message


def send_emails(subject, body, cc, families, class_map, note, term, progress):
    msg_prefix = progress.GetMessage()
    gmail_service = get_gmail_service()
    profile = gmail_service.users().getProfile(userId='me').execute()
    sender = profile['emailAddress']
    for n, family in enumerate(families.values()):
        if progress.WasCancelled():
            break
        msg = f"{msg_prefix}{family['last_name']}"
        wx.CallAfter(progress.Update, n, newmsg=msg)
        if get_students(family):
            pdf_buffer = MyBytesIO()
            generate_one_invoice(family, class_map, note, term, pdf_buffer)
            parents = family['parents']
            recipients = [
                f'"{p[Column.FIRST_NAME]} {p[Column.LAST_NAME]}" <{p[Column.EMAIL]}>'
                for p in parents]
            if recipients:
                msg = create_message_with_attachment(sender=sender,
                                                     recipients=recipients,
                                                     cc=cc,
                                                     subject=subject,
                                                     body=body,
                                                     data=pdf_buffer.getvalue())
                send_message(gmail_service, 'me', msg)


def create_draft(service, user_id, message_body):
    """Create and insert a draft email.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
               can be used to indicate the authenticated user.
      message_body: The body of the email message, including headers.

    Returns:
      Draft object, including draft id and message meta data.
    """
    message = {'message': message_body}
    draft = service.users().drafts().create(userId=user_id, body=message).execute()
    return draft


def create_drafts(subject, body, cc, families, class_map, note, term, progress):
    msg_prefix = progress.GetMessage()
    gmail_service = get_gmail_service()
    profile = gmail_service.users().getProfile(userId='me').execute()
    sender = profile['emailAddress']
    draft_ids = []
    for n, family in enumerate(families.values()):
        if progress.WasCancelled():
            break
        msg = f"{msg_prefix}{family['last_name']}"
        wx.CallAfter(progress.Update, n, newmsg=msg)
        if get_students(family):
            pdf_buffer = MyBytesIO()
            generate_one_invoice(family, class_map, note, term, pdf_buffer)
            parents = family['parents']
            recipients = [
                f'"{p[Column.FIRST_NAME]} {p[Column.LAST_NAME]}" <{p[Column.EMAIL]}>'
                for p in parents]
            if recipients:
                msg = create_message_with_attachment(sender=sender,
                                                     recipients=recipients,
                                                     cc=cc,
                                                     subject=subject,
                                                     body=body,
                                                     data=pdf_buffer.getvalue())
                draft = create_draft(gmail_service, 'me', msg)
                draft_ids.append(draft['id'])
    return draft_ids


def send_draft(service, user_id, draft_id):
    draft = {
        'id': draft_id
    }
    message = service.users().drafts().send(userId=user_id, body=draft).execute()
    logger.debug("Draft with ID: " + draft_id + " sent successfully.")
    logger.debug("Draft sent as Message with ID: " + str(dir(message)))


def send_drafts(draft_ids, progress):
    """Send drafts with given list of draft_ids. These IDs must be for drafts already created and now
    sitting in the Drafts folder of the Gmail account."""
    msg_prefix = progress.GetMessage()
    gmail_service = get_gmail_service()
    for n, draft_id in enumerate(draft_ids):
        if progress.WasCancelled():
            break
        msg = f"{msg_prefix} {n}/{len(draft_ids)}..."
        wx.CallAfter(progress.Update, n, newmsg=msg)
        send_draft(gmail_service, 'me', draft_id)
