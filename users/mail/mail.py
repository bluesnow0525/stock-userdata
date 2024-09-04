import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json

# 如果修改了這些範圍，請刪除文件 token.json。
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_credentials():
    """獲取有效的憑證，如果憑證過期則進行刷新或重新授權。"""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # 如果沒有（有效的）憑證，讓用戶登錄。
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as error:
                print(f'刷新憑證時出現錯誤: {error}')
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=5000, open_browser=True)
        # 保存憑證以便下次使用
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds

def send_email(to_email, subject, body):
    """使用 Gmail API 發送電子郵件。"""
    creds = get_credentials()
    if not creds:
        print('無法獲取有效的憑證。')
        return None

    service = build('gmail', 'v1', credentials=creds)

    # 創建電子郵件消息
    message = MIMEText(body)
    message['to'] = to_email
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # 發送電子郵件
    message = {
        'raw': raw
    }
    try:
        sent_message = (service.users().messages().send(userId="me", body=message).execute())
        print(f'郵件發送成功，郵件 ID: {sent_message["id"]}')
        return sent_message
    except Exception as error:
        print(f'發生錯誤: {error}')
        return None

if __name__ == "__main__":
    # 示例使用
    send_email('weshank20020525@gmail.com', 'Test Subject', 'This is a test email body.')
