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
        return datetime.fromtimestamp(0, tz=timezone.utc)

def save_last_update(update_time):
    """保存本次更新时间"""
    with open('last_update.json', 'w') as f:
        json.dump({'last_update': update_time.isoformat()}, f)

def check_updates():
    """检查RSS是否有更新"""
    feed_url = "https://michael180831.github.io/wechat-rss-feed/rss.xml"
    feed = feedparser.parse(feed_url)
    
    if not feed.entries:
        print("No entries found in the feed")
        return False
    
    last_update = load_last_update()
    latest_entry = feed.entries[0]
    
    # 获取最新文章的发布时间
    try:
        latest_time = datetime.fromtimestamp(
            mktime(latest_entry.published_parsed),
            tz=timezone.utc
        )
    except AttributeError:
        print("Could not parse publication time")
        return False
    
    if latest_time > last_update:
        save_last_update(latest_time)
        return True
        
    return False

if __name__ == "__main__":
    has_updates = check_updates()
    # 设置GitHub Actions输出
    print(f"::set-output name=has_updates::{str(has_updates).lower()}")