import os
import requests
import json
import re
from typing import Optional, Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AIService:
    """AI服务接口"""
    def __init__(self):
        # 这里添加你的 AI 服务凭证
        self.api_key = os.environ.get('AI_API_KEY')
        self.api_url = "YOUR_AI_SERVICE_ENDPOINT"  # 替换为实际的 API 端点

    def is_job_related(self, text: str) -> bool:
        """判断文章是否与招聘/求职相关"""
        try:
            # 调用 AI 服务判断文章类型
            prompt = f"""
            请判断以下文章是否与招聘或求职相关。
            只返回 true 或 false。
            
            文章内容：
            {text}
            """
            
            # TODO: 实现实际的 AI 调用
            # 这里需要根据实际使用的 AI 服务来实现
            response = self._call_ai_api(prompt)
            return 'true' in response.lower()
            
        except Exception as e:
            print(f"Error checking job relevance: {str(e)}")
            return False

    def summarize(self, text: str, biz: str = None) -> Dict[str, str]:
        """生成规范格式的招聘信息总结"""
        try:
            prompt = f"""
            请按以下格式总结这篇招聘文章的信息，如果无法提取某项信息则返回none：

            公司/单位/机构等（招人单位）：[提取]
            工作内容：[提取]
            职位：[提取]
            地址：[提取]
            联系方式/电话/微信：[提取]
            联系人：[提取]
            薪资：[提取]
            条件限制：[提取年龄、性别、工作经验、短期/临时工等限制]
            信息来源：[优先提取公众号名称，如果没有则使用 {biz}]

            文章内容：
            {text}
            """
            
            # TODO: 实现实际的 AI 调用
            # 这里需要根据实际使用的 AI 服务来实现
            response = self._call_ai_api(prompt)
            
            # 解析响应为字典格式
            summary = self._parse_summary(response)
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return {}

    def _call_ai_api(self, prompt: str) -> str:
        """调用 AI API"""
        # TODO: 实现实际的 AI API 调用
        # 这里需要根据实际使用的 AI 服务来实现
        pass

    def _parse_summary(self, response: str) -> Dict[str, str]:
        """解析 AI 响应为字典格式"""
        summary = {}
        lines = response.split('\n')
        current_key = None
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                summary[key] = value if value and value != 'none' else 'none'
        
        return summary

class NotificationService:
    """通知服务"""
    def __init__(self):
        self.email_sender = os.environ.get('EMAIL_SENDER')
        self.email_password = os.environ.get('EMAIL_PASSWORD')
        self.email_recipient = os.environ.get('EMAIL_RECIPIENT')
        self.smtp_server = "smtp.qq.com"  # QQ 邮箱 SMTP 服务器
        self.smtp_port = 587  # QQ 邮箱 SMTP 端口

    def send_email(self, summary: Dict[str, str], article_url: str):
        """发送邮件通知"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_sender
            msg['To'] = self.email_recipient
            msg['Subject'] = "新招聘信息更新"

            body = "发现新的招聘信息：\n\n"
            for key, value in summary.items():
                body += f"{key}：{value}\n"
            body += f"\n原文链接：{article_url}"

            msg.attach(MIMEText(body, 'plain', 'utf-8'))  # 添加 utf-8 编码支持

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)

            print("Email notification sent successfully")
            return True

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False