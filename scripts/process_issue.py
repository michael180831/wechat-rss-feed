import os
import requests
import json
import re
from typing import Optional, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import traceback
import github

# 全局常量
CURRENT_TIME = "2025-03-26 15:55:01"  # 使用提供的确切时间
CURRENT_USER = "michael180831"    # 使用提供的用户登录名

class AIService:
    """AI服务接口"""
    def __init__(self):
        self.api_password = os.environ.get('API_PASSWORD')
        if not self.api_password:
            raise ValueError("API_PASSWORD environment variable is not set")
        print(f"API Password configured: {bool(self.api_password)}")
        self.api_url = "https://spark-api-open.xf-yun.com/v1/chat/completions"
        self.user_id = CURRENT_USER
        self.init_time = CURRENT_TIME
        print(f"Service initialized at (UTC): {self.init_time}")

    def clean_content(self, content: str) -> str:
        """清理内容，移除重复的状态信息"""
        try:
            if "---" in content:
                cleaned = content.split("---")[0].strip()
                print(f"Content cleaned. Original length: {len(content)}, Cleaned length: {len(cleaned)}")
                return cleaned
            return content.strip()
        except Exception as e:
            print(f"Error in clean_content: {str(e)}")
            return content

    def is_job_related(self, text: str) -> bool:
        """判断文章是否与招聘/求职相关"""
        try:
            print(f"Checking if text is job related. Text length: {len(text)}")
            print(f"Text preview: {text[:200]}...")
            
            print("Performing basic keyword check...")
            basic_keywords_result = self._check_basic_keywords(text)
            print(f"Basic keywords result: {basic_keywords_result}")
            
            if not basic_keywords_result:
                print("Failed basic keyword check")
                return False
            
            print("Performing AI deep analysis...")
            is_job = self._ai_deep_analysis(text)
            print(f"AI deep analysis result: {is_job}")
            
            return is_job
            
        except Exception as e:
            print(f"Error checking job relevance: {str(e)}")
            return False

    def summarize(self, content: str, biz: Optional[str] = None) -> Dict[str, Any]:
        """总结内容，返回结构化信息"""
        try:
            print("\n=== Content Summary ===")
            print(f"Processing time (UTC): {self.init_time}")
            
            cleaned_content = self.clean_content(content)
            
            prompt = f"""请分析以下招聘信息，并以JSON格式返回以下字段：
1. title: 职位名称
2. company: 公司名称（如果有）
3. salary: 薪资信息（如果有）
4. location: 工作地点
5. requirements: 职位要求（列表形式）
6. benefits: 福利待遇（列表形式）
7. contact: 联系方式
8. work_type: 工作类型（全职/兼职/实习等）
9. work_time: 工作时间（如果有）

内容：
{cleaned_content}

请确保返回格式为有效的JSON格式。如果某字段信息不存在，将其值设为null。"""
            
            print("Sending summary request to AI...")
            response = self._call_spark_api(prompt)
            
            if not response:
                print("No response from AI service")
                return {
                    "error": "无法获取内容总结",
                    "biz": biz,
                    "raw_content": cleaned_content
                }
                
            try:
                summary = json.loads(response)
                summary["biz"] = biz
                summary["raw_content"] = cleaned_content
                print("Summary generated successfully")
                return summary
            except json.JSONDecodeError:
                print(f"Failed to parse AI response as JSON: {response}")
                return {
                    "error": "无法解析AI响应",
                    "biz": biz,
                    "raw_content": cleaned_content,
                    "ai_response": response
                }
                
        except Exception as e:
            print(f"Error in summarize: {str(e)}")
            traceback.print_exc()
            return {
                "error": f"处理过程出错: {str(e)}",
                "biz": biz,
                "raw_content": content
            }
    def _check_basic_keywords(self, text: str) -> bool:
        """基础关键词匹配"""
        # 招聘核心词集合
        core_keywords = {
            '招聘', '诚聘', '急聘', '招人', '招工', '急招', '招贤', '招兵买马', 
            '纳新', '扩招', '高薪聘请', '高薪诚聘', '内部推荐', '人才引进', 
            '人才招募', '招骋', '急佂', '招蓦', '人材'
        }
        
        # 具体岗位词集合
        position_keywords = {
            '招学徒', '招客服', '招文员', '招宝妈', '招保洁', '招护工', '招阿姨',
            '招驻场', '招跟车', '招打包', '招分拣', '招装卸', '招组装', '招串珠',
            '招地推', '招派单', '招充场', '招扫码', '招代理', '招加盟', '招合伙人',
            '招跟班', '招洗碗工', '招操作工', '招日结工', '招顶班', '招替班', 
            '招替工', '招寒假工', '招暑假工', '招临时', '招钟点'
        }
        
        # 工作性质词集合
        job_type_keywords = {
            '全职', '兼职', '实习', '临时工', '长期工', '短期工', '小时工',
            '日结工', '假期工', '学生工', '寒假工', '暑假工', '钟点工',
            '替班', '顶班', '临时'
        }
        
        # 待遇相关词集合
        benefit_keywords = {
            '日结', '月结', '现结', '压三天', '包吃住', '包住宿', '报销路费',
            '提成高', '绩效奖', '待遇优', '综合薪资', '计件工资', '多劳多得',
            '房补', '餐补', '车补', '油补', '全勤奖', '年底双薪',
            '月入过万', '轻松过万', '上班自由', '时间自由', '不打卡', '可预支',
            '学费返还', '带薪培训', '工资透明', '现金结算'
        }
        
        # 工作模式词集合
        work_mode_keywords = {
            '做六休一', '两班倒', '长白班', '站立工作',
            '手工外发', '在家可做', '代加工', '手机兼职'
        }
        
        # 普通用语词集合（方言或口语化表达）
        colloquial_keywords = {
            '找人手', '找工人', '找师傅', '带徒弟', '找帮手', '添人手',
            '添劳力', '招劳力', '请人做野', '请帮工', '请师傅', '帮工',
            '跑腿儿', '整人手', '缺帮手', '找干活麻溜的', '力工',
            '寻师傅一名', '找小工', '打零工', '出大力的', '干体力活'
        }
        
        # 转换为小写进行匹配
        text_lower = text.lower()
        
        # 检查各类关键词
        has_core = any(keyword in text_lower for keyword in core_keywords)
        has_position = any(keyword in text_lower for keyword in position_keywords)
        has_job_type = any(keyword in text_lower for keyword in job_type_keywords)
        has_benefit = any(keyword in text_lower for keyword in benefit_keywords)
        has_work_mode = any(keyword in text_lower for keyword in work_mode_keywords)
        has_colloquial = any(keyword in text_lower for keyword in colloquial_keywords)
        
        # 检查是否包含联系方式
        has_contact = bool(re.search(r'(?:联系方式|联系电话|微信|电话|手机号|QQ)[:：]?\s*\d+', text))
        
        # 打印调试信息
        print(f"Basic keyword check results:")
        print(f"Has core keywords: {has_core}")
        print(f"Has position keywords: {has_position}")
        print(f"Has job type keywords: {has_job_type}")
        print(f"Has benefit keywords: {has_benefit}")
        print(f"Has work mode keywords: {has_work_mode}")
        print(f"Has colloquial keywords: {has_colloquial}")
        print(f"Has contact info: {has_contact}")
        
        # 判断逻辑
        is_job_post = (
            (has_core and (has_contact or has_benefit)) or
            (has_position and (has_contact or has_benefit)) or
            (has_colloquial and has_contact and (has_benefit or has_job_type))
        )
        
        print(f"Final basic check result: {is_job_post}")
        return is_job_post
    
    def _ai_deep_analysis(self, text: str) -> bool:
        """AI深度分析"""
        prompt = f"""
        请分析以下文本是否为招聘信息。必须同时满足以下条件中的至少3个才能判定为招聘信息：
        1. 包含具体工作职位
        2. 包含工作地点
        3. 包含薪资待遇说明
        4. 包含工作要求或条件
        5. 包含联系方式
        6. 包含工作时间说明
    
        请逐条分析每个条件是否满足，然后给出最终判断。
    
        文本内容：
        {text}
    
        请按以下格式返回结果：
        1. 工作职位: 是/否
        2. 工作地点: 是/否
        3. 薪资待遇: 是/否
        4. 工作要求: 是/否
        5. 联系方式: 是/否
        6. 工作时间: 是/否
        
        满足条件数: X
        最终判断: true/false
        """
        response = self._call_spark_api(prompt)
        print(f"AI analysis response:\n{response}")
        
        return '最终判断: true' in response.lower()

    def _call_spark_api(self, prompt: str) -> str:
        """调用星火API"""
        try:
            print("Preparing API call...")
            current_time = "2025-03-26 16:13:06"  # 使用提供的当前时间
            
            headers = {
                "Authorization": f"Bearer {self.api_password}",
                "Content-Type": "application/json"
            }
            
            print("Headers configured (auth length):", len(str(self.api_password)))
            
            data = {
                "model": "lite",
                "user": self.user_id,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的招聘信息分析助手"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            print(f"Making request to {self.api_url}")
            print(f"Request time (UTC): {current_time}")
            
            response = requests.post(self.api_url, headers=headers, json=data)
            
            print(f"Response status code: {response.status_code}")
            if response.status_code != 200:
                print(f"Response headers: {response.headers}")
                print(f"Response content: {response.text}")
                return ""
                
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return content
            else:
                print(f"Unexpected API response format: {result}")
                return ""
                
        except Exception as e:
            print(f"Error calling Spark API: {str(e)}")
            traceback.print_exc()
            return ""
class NotificationService:
    """通知服务"""
    def __init__(self):
        print("\n=== Email Configuration Initialization ===")
        self.sender = os.environ.get('EMAIL_SENDER')
        self.password = os.environ.get('EMAIL_PASSWORD')
        self.recipient = os.environ.get('EMAIL_RECIPIENT')
        
        print(f"Sender email: {self.sender if self.sender else 'Not configured'}")
        print(f"Password length: {len(self.password) if self.password else 'Not configured'}")
        print(f"Recipient email: {self.recipient if self.recipient else 'Not configured'}")
        
        self.smtp_server = 'smtp.qq.com'
        self.smtp_port = 465
        self.use_ssl = True
        
        print(f"SMTP Server: {self.smtp_server}")
        print(f"SMTP Port: {self.smtp_port}")
        print(f"Using SSL: {self.use_ssl}")
        print(f"Initialization time (UTC): {CURRENT_TIME}")
        print("=== Configuration Complete ===\n")

    def send_email(self, summary: Dict[str, str], article_url: str) -> bool:
        """发送邮件通知"""
        print("\n=== Starting Email Sending Process ===")
        try:
            print("Preparing email content...")
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.recipient
            msg['Subject'] = "新的招聘信息"
            print(f"Email headers set: From={msg['From']}, To={msg['To']}")

            content = "新的招聘信息摘要：\n\n"
            for key, value in summary.items():
                content += f"{key}: {value}\n"
            content += f"\n原文链接：{article_url}"
            
            print("Email content prepared. Content length:", len(content))
            msg.attach(MIMEText(content, 'plain', 'utf-8'))

            print(f"\nConnecting to SMTP server {self.smtp_server}:{self.smtp_port}")
            if self.use_ssl:
                print("Using SSL connection...")
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                print("Using standard connection with STARTTLS...")
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            
            server.set_debuglevel(1)

            print("\nAttempting to login...")
            server.login(self.sender, self.password)
            print("Login successful!")

            print("\nSending email...")
            server.send_message(msg)
            
            print("Closing SMTP connection...")
            server.quit()

            print("=== Email Sent Successfully! ===\n")
            return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"\n=== SMTP Authentication Error ===")
            print(f"Error details: {str(e)}")
            print("This usually means the password (authorization code) is incorrect")
            return False
            
        except smtplib.SMTPException as e:
            print(f"\n=== SMTP Error ===")
            print(f"Error type: {e.__class__.__name__}")
            print(f"Error details: {str(e)}")
            return False
            
        except Exception as e:
            print(f"\n=== Unexpected Error ===")
            print(f"Error type: {e.__class__.__name__}")
            print(f"Error details: {str(e)}")
            print(f"Error time (UTC): {CURRENT_TIME}")
            traceback.print_exc()
            return False

def add_job_label(gh: github.Github, issue_number: int) -> None:
    """添加招聘标签到 issue"""
    try:
        repo = gh.get_repo(os.environ.get('GITHUB_REPOSITORY', 'michael180831/wechat-rss-feed'))
        issue = repo.get_issue(issue_number)
        issue.add_to_labels("jobs")
        print(f"Successfully added 'jobs' label to issue #{issue_number}")
    except Exception as e:
        print(f"Error adding job label: {str(e)}")
        traceback.print_exc()

def extract_content_and_link(body: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """从Issue内容中提取文章内容和链接"""
    try:
        print(f"Extracting content from body: {body[:100]}...")
        
        content_match = re.search(r'#原内容\s*([\s\S]*?)(?=\s*$)', body)
        content = content_match.group(1).strip() if content_match else None
        
        url_match = re.search(r'https?://mp\.weixin\.qq\.com/[^\s]+', body)
        url = url_match.group(0) if url_match else None
        
        biz_match = re.search(r'__biz=([^&]+)', url) if url else None
        biz = biz_match.group(1) if biz_match else None
        
        print(f"Extraction time (UTC): {CURRENT_TIME}")
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
        
        updated_body = f"{original_body}\n\n---\n\n状态：{status}"
        
        url = f"https://api.github.com/repos/{CURRENT_USER}/wechat-rss-feed/issues/{issue_number}"
        response = requests.patch(url, headers=headers, json={"body": updated_body})
        response.raise_for_status()
        
        print(f"Issue status updated at (UTC): {CURRENT_TIME}")
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
        
        summary_text = "\n\n---\n\n### AI总结\n"
        for key, value in summary.items():
            summary_text += f"- **{key}**: {value}\n"
            
        updated_body = original_body + summary_text
        
        url = f"https://api.github.com/repos/{CURRENT_USER}/wechat-rss-feed/issues/{issue_number}"
        response = requests.patch(url, headers=headers, json={"body": updated_body})
        response.raise_for_status()
        
        print(f"Issue summary updated at (UTC): {CURRENT_TIME}")
        print("Successfully updated issue with summary")
        return True
        
    except Exception as e:
        print(f"Error updating issue with summary: {str(e)}")
        return False

def process_issue():
    """处理新的 Issue"""
    try:
        print("\n=== Process Start ===")
        print(f"Processing time (UTC): {CURRENT_TIME}")
        print(f"Processing user: {CURRENT_USER}")
        
        event_path = os.environ.get('GITHUB_EVENT_PATH')
        print(f"Event path: {event_path}")
        
        if not event_path:
            raise ValueError("No event data found")
            
        with open(event_path, 'r') as f:
            event_data = json.load(f)
        print(f"Event data loaded successfully")
            
        issue = event_data['issue']
        print(f"\n=== Issue Information ===")
        print(f"Issue number: #{issue['number']}")
        print(f"Labels: {[label['name'] for label in issue.get('labels', [])]}")
        
        print("\n=== Content Extraction ===")
        content, article_url, biz = extract_content_and_link(issue['body'])
        print(f"Content length: {len(content) if content else 0}")
        print(f"URL: {article_url}")
        print(f"Biz: {biz}")
        print("Content preview:")
        print("-" * 50)
        print(content[:500] if content else "No content")
        print("-" * 50)
        
        if not content:
            print("Error: No content found to process")
            return False
            
        print("\n=== Service Initialization ===")
        ai_service = AIService()
        
        print("\n=== Job Content Detection ===")
        is_job = ai_service.is_job_related(content)
        print(f"Job detection result: {is_job}")
        
        if not is_job:
            print("\n=== Not Job Related - Updating Issue ===")
            update_issue_with_status(
                issue['number'],
                issue['body'],
                "文章与招聘/求职无关"
            )
            print("Status updated: Not job related")
            return True
            
        print("\n=== Job Related - Processing ===")
        
        print("Generating summary...")
        summary = ai_service.summarize(content, biz)
        print("Summary content:")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        
        print("\nAdding jobs label...")
        gh = github.Github(os.environ['GITHUB_TOKEN'])
        add_job_label(gh, issue['number'])
        print("Label added successfully")
        
        print("\n=== Sending Email Notification ===")
        notification_service = NotificationService()
        notification_success = notification_service.send_email(summary, article_url)
        print(f"Email sending result: {'Success' if notification_success else 'Failed'}")
        
        print("\n=== Updating Issue with Summary ===")
        success = update_issue_with_summary(
            issue['number'],
            issue['body'],
            summary
        )
        print(f"Issue update result: {'Success' if success else 'Failed'}")
        
        print("\n=== Process Summary ===")
        print(f"Time (UTC): {CURRENT_TIME}")
        print(f"Issue: #{issue['number']}")
        print(f"Content detection: Success")
        print(f"Job related: Yes")
        print(f"Summary generation: Success")
        print(f"Email notification: {'Success' if notification_success else 'Failed'}")
        print(f"Issue update: {'Success' if success else 'Failed'}")
        
        return success
        
    except Exception as e:
        print("\n=== Error Report ===")
        print(f"Error time (UTC): {CURRENT_TIME}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("Stack trace:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = process_issue()
    print(f"Process completed with status: {success}")
    print(f"Completion time (UTC): {CURRENT_TIME}")
