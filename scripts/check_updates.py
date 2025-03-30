import json
import os
from datetime import datetime
import pytz
import requests
import time
import random
from bs4 import BeautifulSoup
from send_email import send_email
from article_parser import extract_article_info, is_newer_article

def load_account_info():
    """加载公众号配置信息"""
    try:
        with open('wechat_accounts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_account_info(accounts):
    """保存公众号配置信息"""
    with open('wechat_accounts.json', 'w', encoding='utf-8') as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

def get_beijing_time():
    """获取北京时间"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    utc_time = datetime.now(pytz.utc)
    beijing_time = utc_time.astimezone(beijing_tz)
    return beijing_time

def get_latest_article_by_biz(biz):
    """获取公众号最新文章，使用搜狗微信搜索"""
    try:
        # 构建搜索URL (这里使用搜狗微信搜索为例)
        search_url = f"https://weixin.sogou.com/weixin?type=1&query=wechat_biz:{biz}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试找到最新文章链接
            article_link = soup.select_one('.txt-box h3 a')
            if article_link:
                article_url = article_link.get('href')
                # 搜狗链接通常是重定向链接，需要进一步处理
                if article_url and not article_url.startswith('http'):
                    article_url = 'https://weixin.sogou.com' + article_url
                    
                # 尝试提取文章发布时间
                time_element = soup.select_one('.s-p')
                publish_time = time_element.get_text().strip() if time_element else None
                
                title = article_link.get_text().strip()
                
                return {
                    'url': article_url,
                    'title': title,
                    'publish_time': publish_time
                }
        
        print(f"[WARNING] 未能获取公众号(biz={biz})的最新文章信息")
        return None
    
    except Exception as e:
        print(f"[ERROR] 获取最新文章失败: {str(e)}")
        return None

def get_account_name(biz, accounts, processed_biz_data):
    """获取公众号名称，包括变体处理"""
    if biz in accounts:
        return accounts[biz]["name"]
    
    for original_biz, variants in processed_biz_data.items():
        if biz in variants and original_biz in accounts:
            base_name = accounts[original_biz]["name"]
            variant_index = variants.index(biz) + 1
            return f"{base_name}{variant_index}"
    
    return f"未知公众号({biz})"

def check_article_update(account_info, article_info):
    """检查文章是否更新"""
    if not article_info:
        return False
        
    stored_article = account_info.get('latest_article', {})
    stored_title = stored_article.get('title')
    stored_url = stored_article.get('url')
    
    # 如果标题和URL都不同，视为更新
    if article_info['title'] != stored_title or article_info['url'] != stored_url:
        print(f"[更新] 检测到 {account_info['name']} 有新文章: {article_info['title']}")
        # 更新存储的文章信息
        account_info['latest_article'] = {
            'title': article_info['title'],
            'publish_time': article_info.get('publish_time', 'null'),
            'url': article_info['url'],
            'detected_at': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
        }
        return True
    
    return False

def format_update_message(account_info):
    """格式化更新消息"""
    account_name = account_info["name"]
    latest_article = account_info.get("latest_article", {})
    
    title = latest_article.get("title", "未知标题")
    publish_time = latest_article.get("publish_time", "null")
    detected_at = latest_article.get("detected_at", "null")
    url = latest_article.get("url", "")
    
    return (
        f"公众号名称：{account_name}\n"
        f"文章标题：{title}\n"
        f"文章发布时间：{publish_time}\n"
        f"检测时间：{detected_at}\n"
        f"文章链接：{url}\n"
        "-------------------"
    )

def main():
    try:
        with open('processed_biz.json', 'r', encoding='utf-8') as f:
            processed_biz_data = json.load(f)
            # 添加类型检查和空字典处理
            if not isinstance(processed_biz_data, dict):
                raise ValueError(
                    "processed_biz.json 必须为字典格式，请重新运行 process_biz.py 生成"
                )
            if not processed_biz_data:
                raise ValueError("processed_biz.json 内容为空，请检查 biz.txt 输入")
        
        accounts = load_account_info()
        current_time = get_beijing_time()
        check_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 记录有更新的公众号
        updated_accounts = []
        update_messages = []
        
        # 检查所有公众号
        for original_biz, variants in processed_biz_data.items():
            print(f"[DEBUG] 正在检查公众号 BIZ: {original_biz}")
            
            # 如果这个biz不在accounts中，可能需要初始化
            if original_biz not in accounts:
                accounts[original_biz] = {
                    "name": f"公众号({original_biz[:8]}...)",
                    "latest_article": {}
                }
            
            # 获取这个公众号的最新文章
            article_info = get_latest_article_by_biz(original_biz)
            if not article_info:
                print(f"[DEBUG] 未能获取公众号(biz={original_biz})的最新文章")
                continue
            
            # 检查是否有更新
            account_info = accounts[original_biz]
            if check_article_update(account_info, article_info):
                updated_accounts.append(account_info['name'])
                update_msg = format_update_message(account_info)
                update_messages.append(update_msg)
            
            # 避免请求过于频繁
            time.sleep(random.uniform(2, 5))
        
        # 保存更新后的账号信息
        save_account_info(accounts)
        
        # 如果有更新，发送邮件通知
        if update_messages:
            print(f"[INFO] 检测到 {len(updated_accounts)} 个公众号有更新，准备发送邮件通知")
            email_subject = f"微信公众号更新通知 - {check_time}"
            email_body = (
                f"检测时间：{check_time}\n"
                f"更新公众号数量：{len(updated_accounts)}\n"
                "-------------------\n" +
                "\n\n".join(update_messages)
            )
            send_email(subject=email_subject, body=email_body, is_error=False)
            print("[INFO] 邮件通知发送成功")
        else:
            print("[INFO] 没有检测到公众号更新")
        
        return True
        
    except Exception as e:
        print(f"主函数执行出错: {str(e)}")
        error_body = f"执行时间：{get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}\n错误信息：{str(e)}"
        send_email(
            subject="微信公众号监控系统错误",
            body=error_body,
            is_error=True
        )
        return False

if __name__ == "__main__":
    main()
