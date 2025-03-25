import json
import os
import sys

def validate_and_fix_biz(biz):
    """
    验证和修复 biz 参数
    - 替换可能混淆的字符 (0,O,o)
    - 返回所有可能的有效组合
    """
    # 原始 biz
    variants = {biz}
    
    # 找出所有可能需要替换的位置
    positions = []
    for i, char in enumerate(biz):
        if char in '0Oo':
            positions.append(i)
    
    # 生成所有可能的组合
    for pos in positions:
        char = biz[pos]
        new_variants = set()
        for variant in variants:
            if char == '0':
                new_variants.add(variant[:pos] + 'O' + variant[pos+1:])
                new_variants.add(variant[:pos] + 'o' + variant[pos+1:])
            elif char == 'O':
                new_variants.add(variant[:pos] + '0' + variant[pos+1:])
                new_variants.add(variant[:pos] + 'o' + variant[pos+1:])
            elif char == 'o':
                new_variants.add(variant[:pos] + '0' + variant[pos+1:])
                new_variants.add(variant[:pos] + 'O' + variant[pos+1:])
        variants.update(new_variants)
    
    return list(variants)

def process_biz_file():
    """
    处理 biz.txt 文件，生成所有可能的有效 biz 组合
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    biz_file_path = os.path.join(root_dir, 'biz.txt')
    output_file_path = os.path.join(root_dir, 'processed_biz.json')

    try:
        print(f"Looking for biz.txt at: {biz_file_path}")
        
        with open(biz_file_path, 'r', encoding='utf-8') as f:
            # 读取并清理每一行
            biz_list = [line.strip() for line in f if line.strip()]
        
        print(f"Found {len(biz_list)} biz entries")
        
        # 处理每个 biz
        processed_biz = {}
        for biz in biz_list:
            variants = validate_and_fix_biz(biz)
            processed_biz[biz] = variants
            print(f"Processed biz: {biz} -> {len(variants)} variants")
        
        # 保存处理结果
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(processed_biz, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully saved processed biz to: {output_file_path}")
        return processed_biz
            
    except FileNotFoundError:
        print(f"Error: biz.txt not found at {biz_file_path}")
        return {}
    except Exception as e:
        print(f"Error processing biz file: {str(e)}")
        return {}

if __name__ == "__main__":
    process_biz_file()