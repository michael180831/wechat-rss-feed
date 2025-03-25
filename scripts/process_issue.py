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
            
            response = self._call_ai_api(prompt)
            
            # 解析响应为字典格式
            summary = self._parse_summary(response)
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return {}

    def _call_ai_api(self, prompt: str) -> str:
        """调用 Deepseek API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",  # 或其他适合的模型
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                print(f"API call failed: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"Error calling AI API: {str(e)}")
            return ""

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

def extract_content_and_link(body: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """从 Issue 正文中提取需要总结的内容、链接和 biz 参数"""
    try:
        content_start = body.find("## 原文内容")
        if content_start == -1:
            return None, None, None
        
        content = body[content_start + len("## 原文内容"):].strip()
        
        # 提取链接
        link_match = re.search(r"链接: (.*?)\n", body)
        link = link_match.group(1) if link_match else None
        
        # 提取 biz 参数
        biz = None
        if link:
            biz_match = re.search(r"biz=([^&]+)", link)
            biz = biz_match.group(1) if biz_match else None
        
        return content, link, biz
    except Exception as e:
        print(f"Error extracting content: {str(e)}")
        return None, None, None

def process_issue():
    """处理新的 Issue"""
    try:
        event_path = os.environ.get('GITHUB_EVENT_PATH')
        if not event_path:
            raise ValueError("No event data found")
            
        with open(event_path, 'r') as f:
            event_data = json.load(f)
            
        issue = event_data['issue']
        
        # 提取内容和链接
        content, article_url, biz = extract_content_and_link(issue['body'])
        if not content:
            print("No content found to summarize")
            return False
            
        # 创建服务实例
        ai_service = AIService()
        notification_service = NotificationService()
        
        # 判断是否与招聘相关
        if not ai_service.is_job_related(content):
            print("Article is not job-related")
            update_issue_with_status(
                issue['number'],
                issue['body'],
                "文章与招聘/求职无关"
            )
            return True
        
        # 生成总结
        summary = ai_service.summarize(content, biz)
        
        # 发送通知
        notification_service.send_email(summary, article_url)
        
        # 更新 Issue
        success = update_issue_with_summary(
            issue['number'],
            issue['body'],
            summary
        )
        
        return success
        
    except Exception as e:
        print(f"Error processing issue: {str(e)}")
        return False

def update_issue_with_status(issue_number: int, original_body: str, status: str):
    """更新 Issue 状态"""
    try:
        url = f"https://api.github.com/repos/michael180831/wechat-rss-feed/issues/{issue_number}"
        
        new_body = f"""# 处理状态
{status}

---
{original_body}"""
        
        headers = {
            "Authorization": f"token {os.environ.get('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "body": new_body,
            "labels": ["rss-update", "processed", "not-job-related"]
        }
        
        response = requests.patch(url, json=data, headers=headers)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error updating issue: {str(e)}")
        return False

def update_issue_with_summary(issue_number: int, original_body: str, summary: Dict[str, str]):
    """更新 Issue，添加 AI 总结"""
    try:
        url = f"https://api.github.com/repos/michael180831/wechat-rss-feed/issues/{issue_number}"
        
        summary_text = "\n".join([f"{k}：{v}" for k, v in summary.items()])
        
        new_body = f"""# AI 总结
{summary_text}

---
{original_body}"""
        
        headers = {
            "Authorization": f"token {os.environ.get('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "body": new_body,
            "labels": ["rss-update", "processed", "job-related"]
        }
        
        response = requests.patch(url, json=data, headers=headers)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error updating issue: {str(e)}")
        return False

if __name__ == "__main__":
    success = process_issue()
    # 使用新的GitHub Actions输出语法
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f"success={str(success).lower()}", file=fh)
    
    print(f"Issue processing completed. Success: {success}")