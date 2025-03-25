import feedparser
import json
import os
from datetime import datetime, timezone
from time import mktime

def load_last_update():
    """加载上次更新的时间"""
    try:
        with open('last_update.json', 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data['last_update'])
    except FileNotFoundError:
        # 如果文件不存在，创建一个初始文件
        initial_time = datetime.now(timezone.utc)
        save_last_update(initial_time)
        return initial_time

def save_last_update(update_time):
    """保存本次更新时间"""
    with open('last_update.json', 'w') as f:
        json.dump({'last_update': update_time.isoformat()}, f)

def check_updates():
    """检查RSS是否有更新"""
    feed_url = "https://michael180831.github.io/wechat-rss-feed/rss.xml"
    
    try:
        feed = feedparser.parse(feed_url)
        
        if len(feed.entries) == 0:
            print("No entries found in the feed")
            return False
        
        last_update = load_last_update()
        latest_entry = feed.entries[0]
        
        # 打印调试信息
        print(f"Feed URL: {feed_url}")
        print(f"Feed entries count: {len(feed.entries)}")
        print(f"Latest entry title: {latest_entry.get('title', 'No title')}")
        
        # 获取最新文章的发布时间
        if hasattr(latest_entry, 'published_parsed'):
            latest_time = datetime.fromtimestamp(
                mktime(latest_entry.published_parsed),
                tz=timezone.utc
            )
            
            print(f"Last update time: {last_update}")
            print(f"Latest entry time: {latest_time}")
            
            if latest_time > last_update:
                save_last_update(latest_time)
                return True
        else:
            print("No publication time found in the latest entry")
            
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