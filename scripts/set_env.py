from datetime import datetime
import os

def set_test_environment():
    # 设置测试时间（UTC）
    test_time = "2025-03-27 10:22:34"
    os.environ['CURRENT_TIME'] = test_time
    print(f"Current Date and Time (UTC): {test_time}")
    
    # 设置用户登录信息
    test_user = "michael180831"
    os.environ['GITHUB_ACTOR'] = test_user
    print(f"Current User's Login: {test_user}")

if __name__ == "__main__":
    set_test_environment()