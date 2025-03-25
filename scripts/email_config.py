import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailConfig:
    def __init__(self):
        self.sender = os.environ.get('EMAIL_SENDER')
        self.password = os.environ.get('EMAIL_PASSWORD')
        self.recipient = os.environ.get('EMAIL_RECIPIENT')

        # 根据发件人邮箱判断使用的服务器
        if '@qq.com' in self.sender:
            self.smtp_server = 'smtp.qq.com'
            self.smtp_port = 465
            self.use_ssl = True
        elif '@163.com' in self.sender:
            self.smtp_server = 'smtp.163.com'
            self.smtp_port = 465
            self.use_ssl = True
        elif '@gmail.com' in self.sender:
            self.smtp_server = 'smtp.gmail.com'
            self.smtp_port = 587
            self.use_ssl = False
        else:
            raise ValueError(f"Unsupported email provider for {self.sender}")

    def send_email(self, subject, content):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.recipient
            msg['Subject'] = subject

            msg.attach(MIMEText(content, 'plain', 'utf-8'))

            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()

            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()

            print("Email sent successfully!")
            return True

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
