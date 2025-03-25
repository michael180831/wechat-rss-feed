import os
import requests
import json
from typing import Optional

class AIService:
    """AI服务接口"""
    def summarize(self, text: str) -> str:
        """
        调用 AI 服务总结文本
        这里需要根据实际使用的 AI 服务来实现
        """
        # TODO: 实现实际的 AI 调用
        return "待实现实际的 AI 调用"

def extract_content(body: str) -> Optional[str]:
    """从 Issue 正文中提取需要总结的内容"""
    try:
        # 查找原文内容部分
        content_start = body.find("## 原文内容")
        if content_start == -1:
            return None
        
        content = body[content_start + len("## 原文内容"):].strip()
        return content
    except Exception as e:
        print(f"Error extracting content: {str(e)}")
        return None

def update_issue_with_summary(issue_number: int, original_body: str, summary: str):
    """更新 Issue，添加 AI 总结"""
    try:
        url = f"https://api.github.com/repos/michael180831/wechat-rss-feed/issues/{issue_number}"
        
        # 在原文之前添加总结
        new_body = f"""# AI 总结
{summary}

---
{original_body}"""
        
        headers = {
            "Authorization": f"token {os.environ.get('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "body": new_body,
            "labels": ["rss-update", "processed"]  # 更新标签
        }
        
        response = requests.patch(url, json=data, headers=headers)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error updating issue: {str(e)}")
        return False

def process_issue():
    """处理新的 Issue"""
    try:
        # 从环境变量获取 Issue 信息
        event_path = os.environ.get('GITHUB_EVENT_PATH')
        if not event_path:
            raise ValueError("No event data found")
            
        with open(event_path, 'r') as f:
            event_data = json.load(f)
            
        issue = event_data['issue']
        
        # 提取需要总结的内容
        content = extract_content(issue['body'])
        if not content:
            print("No content found to summarize")
            return False
            
        # 调用 AI 服务进行总结
        ai_service = AIService()
        summary = ai_service.summarize(content)
        
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

if __name__ == "__main__":
    success = process_issue()
    # 使用新的GitHub Actions输出语法
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f"success={str(success).lower()}", file=fh)
    
    print(f"Issue processing completed. Success: {success}")