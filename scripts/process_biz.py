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
    try:
        # ... （原有代码）

        # 确保 processed_biz 是字典且初始化正确
        processed_biz = {}  # 确保初始化为空字典

        for biz in biz_list:
            # 添加空值检查和清理
            if not biz.strip():
                continue  # 跳过空行
                
            # 添加调试日志
            print(f"Processing biz: {biz}")
            variants = validate_and_fix_biz(biz)
            # 确保 variants 是列表且不为空
            if not isinstance(variants, list):
                variants = [biz]  # 默认包含原始值
            
            processed_biz[biz] = variants
            print(f"Generated {len(variants)} variants for {biz}")

        # 保存前验证数据结构
        if not isinstance(processed_biz, dict):
            raise TypeError("processed_biz 必须是字典")
        
        # 修改保存路径为绝对路径
        output_file_path = os.path.join(root_dir, 'processed_biz.json')  # 第 47 行
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(processed_biz, f, ensure_ascii=False, indent=2)
        
        return processed_biz
            
    except FileNotFoundError:
        print(f"Error: biz.txt not found at {biz_file_path}")
        return {}
    except Exception as e:
        print(f"Error processing biz file: {str(e)}")
        return {}

if __name__ == "__main__":
    process_biz_file()
