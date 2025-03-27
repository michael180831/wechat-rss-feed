import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv

def send_email(subject, body, is_error=False):
    try:
        load_dotenv()
        
        # 获取环境变量
        sender = os.getenv('EMAIL_SENDER')
        password = os.getenv('EMAIL_PASSWORD')
        recipient = os.getenv('EMAIL_RECIPIENT')

        print(f"Sending email from {sender} to {recipient}")
        
        # 创建邮件
        message = MIMEText(body, 'plain', 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        message['From'] = sender
        message['To'] = recipient

        # 连接SMTP服务器
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.set_debuglevel(1)  # 开启调试模式
        
        # 登录
        print("Attempting to login...")
        server.login(sender, password)
        
        # 发送邮件
        print("Sending message...")
        server.sendmail(sender, [recipient], message.as_string())
        
        # 关闭连接
        server.quit()
        print("Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试发送
    send_email(
        "Test Email",
        "This is a test email from WeChat Monitor",
        is_error=False
    )