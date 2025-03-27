import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

def send_notification_email(title, updated_accounts):
    """发送邮件通知"""
    try:
        # 使用现有的环境变量名称
        sender_email = os.environ.get('EMAIL_SENDER')
        receiver_email = os.environ.get('EMAIL_RECIPIENT')
        password = os.environ.get('EMAIL_PASSWORD')

        # 验证必要的环境变量
        if not all([sender_email, receiver_email, password]):
            print("Missing required email configuration")
            return False

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

        # QQ邮箱的SMTP设置（如果使用的是QQ邮箱）
        smtp_server = "smtp.qq.com"
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
