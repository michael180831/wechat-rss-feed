import feedparser
import json
import os
import requests
from datetime import datetime, timezone
from time import mktime

def get_valid_biz_list():
    """获取所有可能的有效 biz 组合"""
    try:
        with open('processed_biz.json', 'r', encoding='utf-8') as f:
            biz_data = json.load(f)
        all_variants = set()
        for variants in biz_data.values():
            all_variants.update(variants)
        return list(all_variants)
    except FileNotFoundError:
        print("processed_biz.json not found")
        return []
    except Exception as e:
        print(f"Error reading processed_biz.json: {str(e)}")
        return []

def load_last_update():
    """加载上次更新的时间"""
    try:
        with open('last_update.json', 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data['last_update'])
    except FileNotFoundError:
        initial_time = datetime.now(timezone.utc)
        save_last_update(initial_time)
        return initial_time

def save_last_update(update_time):
    """保存本次更新时间"""
    with open('last_update.json', 'w') as f:
        json.dump({'last_update': update_time.isoformat()}, f)

def create_update_issue(latest_entry):
    """创建更新通知的 Issue"""
    try:
        url = "https://api.github.com/repos/michael180831/wechat-rss-feed/issues"
        
        title = f"RSS更新: {latest_entry.get('title', '新文章')}"
        content = latest_entry.get('description', '')
        
        body = f"""
# 新文章更新

## 文章信息
- 标题: {latest_entry.get('title', '')}
- 链接: {latest_entry.get('link', '')}
- 发布时间: {latest_entry.get('published', '')}
- 作者: {latest_entry.get('author', '')}

## 原文内容
{content}
"""
        
        headers = {
            "Authorization": f"token {os.environ.get('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": title,
            "body": body,
            "labels": ["rss-update", "pending-summary"]  # 添加标签以标识需要处理
        }
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            print("Successfully created issue for update")
            return True
        else:
            print(f"Failed to create issue. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error creating issue: {str(e)}")
        return False

def check_updates():
    """检查RSS是否有更新"""
    feed_url = "https://michael180831.github.io/wechat-rss-feed/rss.xml"
    
    try:
        valid_biz_list = get_valid_biz_list()
        print(f"Loaded {len(valid_biz_list)} valid biz variants")
        
        feed = feedparser.parse(feed_url)
        
        if len(feed.entries) == 0:
            print("No entries found in the feed")
            return False
        
        last_update = load_last_update()
        latest_entry = feed.entries[0]
        
        if hasattr(latest_entry, 'published_parsed'):
            latest_time = datetime.fromtimestamp(
                mktime(latest_entry.published_parsed),
                tz=timezone.utc
            )
            
            if latest_time > last_update:
                issue_created = create_update_issue(latest_entry)
                if issue_created:
                    save_last_update(latest_time)
                return issue_created
                
        return False
        
    except Exception as e:
        print(f"Error checking updates: {str(e)}")
        return False

if __name__ == "__main__":
    has_updates = check_updates()
    # 使用新的GitHub Actions输出语法
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f"has_updates={str(has_updates).lower()}", file=fh)
    
    print(f"Update check completed. Has updates: {has_updates}")