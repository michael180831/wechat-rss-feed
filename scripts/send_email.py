import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

def send_notification_email(title, updated_accounts):
    """发送邮件通知"""
    try:
        # 获取邮件配置
        sender_email = os.environ.get('EMAIL_ADDRESS')
        receiver_email = os.environ.get('EMAIL_ADDRESS')
        password = os.environ.get('EMAIL_PASSWORD')
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT'))

        # 创建邮件
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = title

        # 邮件内容
        body = f"""
检测到以下公众号有更新：

{chr(10).join([f'- {account}' for account in updated_accounts])}

请及时查看最新内容。
"""
        message.attach(MIMEText(body, "plain"))

        # 发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
            
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
