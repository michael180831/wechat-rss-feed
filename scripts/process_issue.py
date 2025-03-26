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
        self.app_id = os.environ.get('SPARK_APP_ID')
        self.api_key = os.environ.get('SPARK_API_KEY')
        self.api_secret = os.environ.get('SPARK_API_SECRET')
        print(f"Spark API credentials configured: {bool(self.app_id and self.api_key and self.api_secret)}")
        self.api_url = "wss://spark-api.xf-yun.com/v1.1/chat"

    def _call_spark_api(self, prompt: str) -> str:
        """调用星火API"""
        try:
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "header": {
                    "app_id": self.app_id,
                    "uid": "user"  # 可以是固定值
                },
                "parameter": {
                    "chat": {
                        "domain": "lite",
                        "temperature": 0.7,
                        "max_tokens": 1024,
                    }
                },
                "payload": {
                    "message": {
                        "text": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                }
            }
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            if result['header']['code'] == 0:
                content = result['payload']['choices']['text'][0]['content']
                return content
            else:
                print(f"API error: {result['header']['message']}")
                return ""
                
        except Exception as e:
            print(f"Error calling Spark API: {str(e)}")
            return ""

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
            
            response = self._call_spark_api(prompt)
            # 尝试解析JSON响应
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                print(f"Failed to parse AI response as JSON: {response}")
                return {"error": "无法解析响应"}
                
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return {"error": str(e)}

    def is_job_related(self, text: str) -> bool:
    """判断文章是否与招聘/求职相关"""
        try:
            print(f"Checking if text is job related. Text length: {len(text)}")
        
            # 第一层：关键词匹配
            print("Performing basic keyword check...")
            if not self._check_basic_keywords(text):
                print("Failed basic keyword check")
                return False
        
            # 第二层：AI深度分析
            print("Performing AI deep analysis...")
            is_job = self._ai_deep_analysis(text)
            print(f"AI deep analysis result: {is_job}")
        
            return is_job
        
    except Exception as e:
        print(f"Error checking job relevance: {str(e)}")
        return False
        
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
        
        # 检查是否包含联系方式（使用正则表达式）
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
        
        # 提取最终判断结果
        if '最终判断: true' in response.lower():
            return True
        return False

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
