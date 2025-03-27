import json
import os
from datetime import datetime
import requests
from send_email import send_email

def main():
    try:
        # 读取处理过的biz文件
        with open('processed_biz.json', 'r', encoding='utf-8') as f:
            processed_biz = json.load(f)

        updates_found = False
        error_messages = []

        # 检查每个公众号
        for biz in processed_biz:
            try:
                print(f"Checking account {biz}...")
                # 这里添加实际的检查逻辑
                # 暂时跳过实际检查，返回测试结果
                updates_found = True
            except Exception as e:
                error_msg = f"Error checking account {biz}: {str(e)}"
                print(error_msg)
                error_messages.append(error_msg)

        # 如果有错误，尝试发送错误报告
        if error_messages:
            try:
                error_report = "\n".join(error_messages)
                send_email(
                    subject="WeChat Monitor Error Report",
                    body=f"Errors occurred during check:\n{error_report}",
                    is_error=True
                )
            except Exception as e:
                print(f"Error sending email: {str(e)}")

        return updates_found

    except Exception as e:
        print(f"Error in main function: {str(e)}")
        return False

if __name__ == "__main__":
    main()