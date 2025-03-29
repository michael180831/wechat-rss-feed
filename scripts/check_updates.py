import json
import os
from datetime import datetime
import pytz
import requests
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

def update_article_info(account_info, article_url):
    """更新文章信息"""
    try:
        response = requests.get(article_url)
        if response.status_code == 200:
            article_info = extract_article_info(response.text)
            if article_info:
                # 检查是否为更新的文章
                current_publish_time = article_info.get('publish_time')
                stored_publish_time = account_info.get('latest_article', {}).get('publish_time')
                
                if current_publish_time and is_newer_article(current_publish_time, stored_publish_time):
                    account_info['latest_article'] = {
                        'title': article_info['title'],
                        'publish_time': current_publish_time,
                        'url': article_url,
                        'detected_at': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    return True
    except Exception as e:
        print(f"更新文章信息时出错: {str(e)}")
    return False

def format_update_message(account_info):
    """仅包含公众号名称和发布时间"""
    account_name = account_info["name"]
    latest_article = account_info.get("latest_article", {})
    
    publish_time = latest_article.get("publish_time", "null")
    detected_at = latest_article.get("detected_at", "null")
    
    return (
        f"公众号名称：{account_name}\n"
        f"文章发布时间：{publish_time}\n"
        f"检测时间：{detected_at}\n"
        "-------------------"
    )

# 修改 main 函数中的加载逻辑：
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
        # ... （原有代码）
        
        accounts = load_account_info()
        current_time = get_beijing_time()
        check_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 记录有更新的公众号
        updated_accounts = []
        update_messages = []
        
        # 检查所有公众号
        for original_biz, variants in processed_biz_data.items():
            matched_biz = original_biz
            if original_biz not in accounts:
                for variant in variants:
                    if variant in accounts:
                        matched_biz = variant
                        break
            
            if matched_biz in accounts:
                account_info = accounts[matched_biz]
                article_url = account_info.get('latest_article', {}).get('url')
                
                # 关键修改：仅在更新时记录
                if article_url and update_article_info(account_info, article_url):
                    updated_accounts.append(account_info['name'])
                    update_msg = format_update_message(account_info)
                    update_messages.append(update_msg)
        
        save_account_info(accounts)
        
        # 关键修改：仅在有更新时发送邮件
        if update_messages:
            email_subject = f"微信公众号更新通知 - {check_time}"
            email_body = (
                f"检测时间：{check_time}\n"
                f"更新公众号数量：{len(updated_accounts)}\n"
                "-------------------\n" +
                "\n\n".join(update_messages)
            )
            send_email(subject=email_subject, body=email_body, is_error=False)
        
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
