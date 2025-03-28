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

# 修改 process_biz_file 函数中的路径逻辑：
def process_biz_file():
    try:
        # 原代码：root_dir = os.path.dirname(script_dir)
        # 改为直接使用当前工作目录（适配 GitHub Actions）
        biz_file_path = os.path.join(os.getcwd(), 'biz.txt')  # 直接定位当前目录下的 biz.txt
        output_file_path = os.path.join(os.getcwd(), 'processed_biz.json')
        
        print(f"当前工作目录: {os.getcwd()}")
        print(f"尝试读取文件: {biz_file_path}")
        
        with open(biz_file_path, 'r', encoding='utf-8') as f:
            # 添加严格过滤逻辑
            biz_list = [line.strip() for line in f if line.strip()]
            if not biz_list:
                raise ValueError("biz.txt 文件内容为空")
                
        print(f"成功读取 {len(biz_list)} 条 biz 记录")
        processed_biz = {}
        for biz in biz_list:
            # 过滤无效字符（如不可见字符）
            biz = biz.strip().replace('\ufeff', '')  # 处理 BOM 字符
            if not biz:
                continue
                
            # 生成变体并确保类型安全
            variants = validate_and_fix_biz(biz)
            if not isinstance(variants, list):
                variants = [biz]  # 强制转为列表
                
            processed_biz[biz] = variants
        
        # 若处理结果为空，写入空字典而非列表
        if not processed_biz:
            processed_biz = {"default": ["MzI5MjAxNjM4MA=="]}  # 示例占位数据
        
        # 保存文件前打印最终数据结构
        print(f"生成的 processed_biz 类型: {type(processed_biz)}")
        print(f"示例数据: {list(processed_biz.items())[:1]}")
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(processed_biz, f, ensure_ascii=False, indent=2)
        
        return processed_biz
    except Exception as e:
        print(f"严重错误: {str(e)}")
        # 返回空字典而非其他类型
        return {}

if __name__ == "__main__":
    process_biz_file()
