import json
import os
from datetime import datetime
import pytz
import requests
from send_email import send_email
from article_parser import extract_article_info

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
    utc_time = datetime.utcnow()
    beijing_time = utc_time.replace(tzinfo=pytz.utc).astimezone(beijing_tz)
    return beijing_time

def get_account_name(biz, accounts, processed_biz_data):
    """获取公众号名称，包括变体处理"""
    # 检查是否是原始biz
    if biz in accounts:
        return accounts[biz]["name"]
    
    # 检查是否是某个原始biz的变体
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
                account_info['latest_article'].update(article_info)
                account_info['latest_article']['url'] = article_url
                return True
    except Exception as e:
        print(f"更新文章信息时出错: {str(e)}")
    return False

def main():
    try:
        # 读取处理过的biz文件
        with open('processed_biz.json', 'r', encoding='utf-8') as f:
            processed_biz_data = json.load(f)
        
        # 读取公众号信息
        accounts = load_account_info()
        
        # 更新变体信息
        for original_biz, variants in processed_biz_data.items():
            if original_biz in accounts:
                accounts[original_biz]["variants"] = variants
        
        current_time = get_beijing_time()
        check_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        update_messages = []
        
        # 检查所有公众号（包括变体）
        checked_accounts = set()
        for original_biz, variants in processed_biz_data.items():
            # 处理原始biz
            if original_biz not in checked_accounts:
                account_info = accounts[original_biz]
                account_name = account_info["name"]
                
                # 构建基本信息
                update_msg = [
                    f"公众号：{account_name}",
                    f"识别码：{original_biz}"
                ]
                
                # 添加最新文章信息
                latest_article = account_info.get('latest_article', {})
                if latest_article and latest_article.get('publish_time'):
                    update_msg.extend([
                        f"最新文章：{latest_article.get('title', '无标题')}",
                        f"发布时间：{latest_article.get('publish_time', '未知')}",
                        f"文章链接：{latest_article.get('url', '未知')}"
                    ])
                
                # 如果有变体，添加变体信息
                if variants:
                    variant_info = []
                    for i, variant in enumerate(variants, 1):
                        variant_name = f"{account_name}{i}"
                        variant_info.append(f"变体{i}：{variant} ({variant_name})")
                    if variant_info:
                        update_msg.append("变体信息：")
                        update_msg.extend(variant_info)
                
                update_msg.append("-------------------")
                update_messages.append("\n".join(update_msg))
                checked_accounts.add(original_biz)
        
        # 保存更新后的账号信息
        save_account_info(accounts)
        
        # 发送通知邮件
        if update_messages:
            email_body = (
                f"检查时间：{check_time}\n\n"
                "本次检查的公众号：\n\n" +
                "\n\n".join(update_messages)
            )
            send_email(
                subject=f"微信公众号检查报告 - {check_time}",
                body=email_body,
                is_error=False
            )
        
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
