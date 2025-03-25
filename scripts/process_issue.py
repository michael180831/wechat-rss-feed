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
        self.api_key = os.environ.get('SILKLAB_API_KEY')
        print(f"Silklab API Key exists: {bool(self.api_key)}")
        self.api_url = "https://api.silklab.ai/v1/chat/completions"

    def _call_silklab_api(self, prompt: str) -> str:
        """调用硅基流动API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "silicon-wiz-7b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error calling Silklab API: {str(e)}")
            return ""

    def is_job_related(self, text: str) -> bool:
        """判断文章是否与招聘/求职相关"""
        try:
            print(f"Checking if text is job related. Text length: {len(text)}")
            prompt = f"""
            请判断以下文章是否与招聘或求职相关。
            只返回 true 或 false。
            
            文章内容：
            {text}
            """
            response = self._call_ai_api(prompt)
            print(f"AI response for job relevance: {response}")
            return 'true' in response.lower()
        except Exception as e:
            print(f"Error checking job relevance: {str(e)}")
            return False

    def summarize(self, content: str, biz: str) -> Dict[str, str]:
        """生成文章总结"""
        try:
            prompt = f"""
            请分析以下招聘信息，提取关键信息并按以下格式返回JSON：
            {{
                "职位": "职位名称",
                "公司": "公司名称（如果有）",
                "工作地点": "工作地点",
                "工资待遇": "薪资范围和福利",
                "工作要求": "主要要求",
                "联系方式": "联系方式"
            }}

            招聘信息：
            {content}

            微信公众号biz: {biz}
            """
            
            response = self._call_ai_api(prompt)
            # 尝试解析JSON响应
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                print(f"Failed to parse AI response as JSON: {response}")
                return {"error": "无法解析响应"}
                
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return {"error": str(e)}

class NotificationService:
    """通知服务"""
    def __init__(self):
        self.sender = os.environ.get('EMAIL_SENDER')
        self.password = os.environ.get('EMAIL_PASSWORD')
        self.recipient = os.environ.get('EMAIL_RECIPIENT')
        
        # 添加调试信息
        print(f"Sender email configured: {bool(self.sender)}")
        print(f"Email password configured: {bool(self.password)}")
        print(f"Recipient email configured: {bool(self.recipient)}")
        
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
            print(f"Warning: Using default SMTP settings for {self.sender}")
            self.smtp_server = 'smtp.qq.com'  # 默认使用QQ邮箱设置
            self.smtp_port = 465
            self.use_ssl = True

    def send_email(self, summary: Dict[str, str], article_url: str) -> bool:
        """发送邮件通知"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.recipient
            msg['Subject'] = "新的招聘信息"

            # 构建邮件内容
            content = "新的招聘信息摘要：\n\n"
            for key, value in summary.items():
                content += f"{key}: {value}\n"
            content += f"\n原文链接：{article_url}"

            msg.attach(MIMEText(content, 'plain', 'utf-8'))

            # 发送邮件
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

def extract_content_and_link(body: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """从Issue内容中提取文章内容和链接"""
    try:
        print(f"Extracting content from body: {body[:100]}...")  # 打印前100个字符用于调试
        
        # 在"#原内容"之后的所有内容作为文章内容
        content_match = re.search(r'#原内容\s*([\s\S]*?)(?=\s*$)', body)
        content = content_match.group(1).strip() if content_match else None
        
        # 尝试提取微信链接和biz参数
        url_match = re.search(r'https?://mp\.weixin\.qq\.com/[^\s]+', body)
        url = url_match.group(0) if url_match else None
        
        biz_match = re.search(r'__biz=([^&]+)', url) if url else None
        biz = biz_match.group(1) if biz_match else None
        
        print(f"Extracted content length: {len(content) if content else 0}")
        print(f"Extracted URL: {url}")
        print(f"Extracted biz: {biz}")
        
        return content, url, biz
        
    except Exception as e:
        print(f"Error extracting content: {str(e)}")
        return None, None, None

def update_issue_with_status(issue_number: int, original_body: str, status: str) -> bool:
    """更新Issue状态"""
    try:
        headers = {
            "Authorization": f"token {os.environ.get('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # 构建更新后的内容
        updated_body = f"{original_body}\n\n---\n\n状态：{status}"
        
        # 发送更新请求
        url = f"https://api.github.com/repos/michael180831/wechat-rss-feed/issues/{issue_number}"
        response = requests.patch(url, headers=headers, json={"body": updated_body})
        response.raise_for_status()
        
        return True
        
    except Exception as e:
        print(f"Error updating issue status: {str(e)}")
        return False

def update_issue_with_summary(issue_number: int, original_body: str, summary: Dict[str, str]) -> bool:
    """更新Issue添加总结"""
    try:
        headers = {
            "Authorization": f"token {os.environ.get('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # 构建总结内容
        summary_text = "\n\n---\n\n### AI总结\n"
        for key, value in summary.items():
            summary_text += f"- **{key}**: {value}\n"
            
        # 更新Issue内容
        updated_body = original_body + summary_text
        
        # 发送更新请求
        url = f"https://api.github.com/repos/michael180831/wechat-rss-feed/issues/{issue_number}"
        response = requests.patch(url, headers=headers, json={"body": updated_body})
        response.raise_for_status()
        
        print("Successfully updated issue with summary")
        return True
        
    except Exception as e:
        print(f"Error updating issue with summary: {str(e)}")
        return False

def process_issue():
    """处理新的 Issue"""
    try:
        print("Starting process_issue function")
        event_path = os.environ.get('GITHUB_EVENT_PATH')
        print(f"Event path: {event_path}")
        
        if not event_path:
            raise ValueError("No event data found")
            
        with open(event_path, 'r') as f:
            event_data = json.load(f)
        print(f"Event data loaded")
            
        issue = event_data['issue']
        print(f"Processing issue #{issue['number']}")
        print(f"Issue labels: {[label['name'] for label in issue.get('labels', [])]}")
        
        # 提取内容和链接
        content, article_url, biz = extract_content_and_link(issue['body'])
        print(f"Extracted content length: {len(content) if content else 0}")
        print(f"Extracted URL: {article_url}")
        print(f"Extracted biz: {biz}")
        
        if not content:
            print("No content found to summarize")
            return False
            
        # 创建服务实例
        print("Initializing services...")
        ai_service = AIService()
        notification_service = NotificationService()
        
        # 判断是否与招聘相关
        print("Checking if content is job related...")
        is_job = ai_service.is_job_related(content)
        print(f"Is job related: {is_job}")
        
        if not is_job:
            print("Article is not job-related")
            print("Updating issue with not-job-related status...")
            update_issue_with_status(
                issue['number'],
                issue['body'],
                "文章与招聘/求职无关"
            )
            return True
        
        # 生成总结
        print("Generating summary...")
        summary = ai_service.summarize(content, biz)
        print(f"Generated summary: {json.dumps(summary, indent=2, ensure_ascii=False)}")
        
        # 发送通知
        print("Sending email notification...")
        notification_success = notification_service.send_email(summary, article_url)
        print(f"Email notification success: {notification_success}")
        
        # 更新 Issue
        print("Updating issue with summary...")
        success = update_issue_with_summary(
            issue['number'],
            issue['body'],
            summary
        )
        print(f"Issue update success: {success}")
        
        return success
        
    except Exception as e:
        print(f"Error processing issue: {str(e)}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = process_issue()
    print(f"Process completed with status: {success}")
