import requests
from datetime import datetime, timezone
import os
import base64
import json
from send_email import send_notification_email
from process_biz import process_biz_file

def load_accounts():
    """加载需要监控的公众号列表"""
    try:
        # 首先处理biz.txt生成processed_biz.json
        processed_biz = process_biz_file()
        if not processed_biz:
            print("No valid biz entries found")
            return []
        
        # 获取所有可能的biz变体
        all_variants = []
        for variants in processed_biz.values():
            all_variants.extend(variants)
        
        return list(set(all_variants))  # 去重
    except Exception as e:
        print(f"Error loading accounts: {e}")
        return []

def get_original_biz(variant, processed_biz):
    """根据变体找到原始的biz值"""
    for original, variants in processed_biz.items():
        if variant in variants:
            return original
    return variant

def check_update(biz):
    """检查单个公众号是否有更新"""
    try:
        url = "https://mp.weixin.qq.com/mp/profile_ext"
        params = {
            "__biz": base64.b64decode(biz).decode('utf-8'),
            "action": "home",
            "scene": "124"
        }
        
        response = requests.get(url, params=params)
        return response.status_code == 200
    except Exception as e:
        print(f"Error checking account {biz}: {e}")
        return False

def create_notification(updated_accounts, processed_biz):
    """创建更新通知"""
    try:
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        title = f"检测到公众号更新 - {current_time}"
        
        # 将变体biz转换为原始biz
        original_updated_accounts = [
            get_original_biz(account, processed_biz)
            for account in updated_accounts
        ]
        original_updated_accounts = list(set(original_updated_accounts))  # 去重
        
        # 创建通知内容
        body = f"""
# 公众号更新提醒

## 检测时间
{current_time}

## 更新公众号
{chr(10).join([f'- {account}' for account in original_updated_accounts])}

## 提示
请访问对应公众号查看最新内容
"""
        
        # 创建GitHub Issue
        url = "https://api.github.com/repos/michael180831/wechat-rss-feed/issues"
        headers = {
            "Authorization": f"token {os.environ.get('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": title,
            "body": body,
            "labels": ["update-detected"]
        }
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            # 发送邮件通知
            return send_notification_email(title, original_updated_accounts)
        return False
            
    except Exception as e:
        print(f"Error creating notification: {e}")
        return False

def main():
    """主程序"""
    try:
        # 获取处理后的biz数据
        processed_biz = process_biz_file()
        if not processed_biz:
            print("No accounts found to monitor")
            return False

        # 检查所有biz变体
        updated_accounts = []
        for original_biz, variants in processed_biz.items():
            for variant in variants:
                if check_update(variant):
                    updated_accounts.append(variant)
                    # 如果找到一个有效的变体，就跳过该biz的其他变体
                    break
            
        if updated_accounts:
            return create_notification(updated_accounts, processed_biz)
        
        print("No updates found")
        return False
        
    except Exception as e:
        print(f"Error in main process: {e}")
        return False

if __name__ == "__main__":
    has_updates = main()
    # 输出结果供GitHub Actions使用
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f"has_updates={str(has_updates).lower()}", file=fh)
    print(f"Update check completed. Has updates: {has_updates}")
