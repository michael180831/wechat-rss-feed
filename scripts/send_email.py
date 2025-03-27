import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

def send_notification_email(title, updated_accounts):
    """发送邮件通知"""
    try:
        # 只需要邮箱和密码配置
        sender_email = os.environ.get('EMAIL_ADDRESS')
        receiver_email = os.environ.get('EMAIL_ADDRESS')  # 接收邮件地址与发送地址相同
        password = os.environ.get('EMAIL_PASSWORD')

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

        # 使用默认的 SMTP 设置
        # 假设使用 Gmail，可以直接使用 smtp.gmail.com
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # 发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
            
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
