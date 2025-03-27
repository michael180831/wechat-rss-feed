import os
from dotenv import load_dotenv
from check_updates import main
from process_biz import process_biz_file

def test_workflow():
    load_dotenv()
    processed_biz = process_biz_file()
    print(f"Processed biz entries: {len(processed_biz)}")
    result = main()
    print(f"Update check result: {result}")

if __name__ == "__main__":
    test_workflow()