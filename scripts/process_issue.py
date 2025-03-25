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
        print(f"AI API Key exists: {bool(self.api_key)}")  # 调试信息
        self.api_url = "https://api.deepseek.com/v1/chat/completions"

    def is_job_related(self, text: str) -> bool:
        """判断文章是否与招聘/求职相关"""
        try:
            print(f"Checking if text is job related. Text length: {len(text)}")  # 调试信息
            prompt = f"""
            请判断以下文章是否与招聘或求职相关。
            只返回 true 或 false。
            
            文章内容：
            {text}
            """
            
            response = self._call_ai_api(prompt)
            print(f"AI response for job relevance: {response}")  # 调试信息
            return 'true' in response.lower()
            
        except Exception as e:
            print(f"Error checking job relevance: {str(e)}")
            return False

    # ... [其他方法保持不变]

def process_issue():
    """处理新的 Issue"""
    try:
        print("Starting process_issue function")  # 调试信息
        event_path = os.environ.get('GITHUB_EVENT_PATH')
        print(f"Event path: {event_path}")  # 调试信息
        
        if not event_path:
            raise ValueError("No event data found")
            
        with open(event_path, 'r') as f:
            event_data = json.load(f)
        print(f"Event data: {json.dumps(event_data, indent=2)}")  # 调试信息
            
        issue = event_data['issue']
        print(f"Processing issue #{issue['number']}")  # 调试信息
        print(f"Issue labels: {[label['name'] for label in issue.get('labels', [])]}")  # 调试信息
        
        # 提取内容和链接
        content, article_url, biz = extract_content_and_link(issue['body'])
        print(f"Extracted content length: {len(content) if content else 0}")  # 调试信息
        print(f"Extracted URL: {article_url}")  # 调试信息
        print(f"Extracted biz: {biz}")  # 调试信息
        
        if not content:
            print("No content found to summarize")
            return False
            
        # 创建服务实例
        print("Initializing services...")  # 调试信息
        ai_service = AIService()
        notification_service = NotificationService()
        
        # 判断是否与招聘相关
        print("Checking if content is job related...")  # 调试信息
        is_job = ai_service.is_job_related(content)
        print(f"Is job related: {is_job}")  # 调试信息
        
        if not is_job:
            print("Article is not job-related")
            print("Updating issue with not-job-related status...")  # 调试信息
            update_issue_with_status(
                issue['number'],
                issue['body'],
                "文章与招聘/求职无关"
            )
            return True
        
        # 生成总结
        print("Generating summary...")  # 调试信息
        summary = ai_service.summarize(content, biz)
        print(f"Generated summary: {json.dumps(summary, indent=2, ensure_ascii=False)}")  # 调试信息
        
        # 发送通知
        print("Sending email notification...")  # 调试信息
        notification_success = notification_service.send_email(summary, article_url)
        print(f"Email notification success: {notification_success}")  # 调试信息
        
        # 更新 Issue
        print("Updating issue with summary...")  # 调试信息
        success = update_issue_with_summary(
            issue['number'],
            issue['body'],
            summary
        )
        print(f"Issue update success: {success}")  # 调试信息
        
        return success
        
    except Exception as e:
        print(f"Error processing issue: {str(e)}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")  # 添加完整的错误追踪
        return False

# ... [其他代码保持不变]