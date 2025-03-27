import re
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
import requests

def parse_datetime(date_str):
    """将中文日期时间字符串转换为datetime对象"""
    # 处理类似 "2025年03月27日 15:34" 的格式
    pattern = r"(\d{4})年(\d{2})月(\d{2})日\s+(\d{2}):(\d{2})"
    match = re.match(pattern, date_str)
    if match:
        year, month, day, hour, minute = map(int, match.groups())
        # 创建北京时间的datetime对象
        tz = pytz.timezone('Asia/Shanghai')
        return tz.localize(datetime(year, month, day, hour, minute))
    return None

def extract_article_info(html_content):
    """从文章HTML中提取信息"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取标题
        title = soup.find('h1', class_='rich_media_title')
        title = title.get_text().strip() if title else None
        
        # 提取发布时间
        publish_time_elem = soup.find('em', id='publish_time')
        publish_time = None
        if publish_time_elem:
            publish_time_str = publish_time_elem.get_text().strip()
            publish_time = parse_datetime(publish_time_str)
        
        return {
            "title": title,
            "publish_time": publish_time.strftime('%Y-%m-%d %H:%M:%S') if publish_time else None
        }
    except Exception as e:
        print(f"提取文章信息时出错: {str(e)}")
        return None
