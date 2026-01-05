import os
import json
import re
from constants import local_i18n

# 目标文件夹路径
target_folders = ["../static/assets","../templates/assets"]  # 修改为你的文件夹路径

def flatten_dict(d, parent_key="", sep="."):
    """将嵌套字典展开为扁平化字典"""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep))
        else:
            items[new_key] = v
    return items

# 扁平化 i18n 配置
flat_i18n = flatten_dict(local_i18n)
# print(flat_i18n)

def replace_keys_in_file(file_path, replacements):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换 tt("xxx.yyy.zzz") 形式
    def replace_tt(match):
        key = match.group(1)  # 获取 key，如 system.updateConfirm
        return f'tt("{replacements.get(key, key)}")'  # 仅替换引号内内容
    
    content = re.sub(r'tt\("([\w.]+)"\)', replace_tt, content)

    # 替换 xxx.yyy.zzz 形式（不带括号的）
    for key, value in replacements.items():
        pattern = rf'\b{re.escape(key)}\b'  # 确保完整匹配 key
        content = re.sub(pattern, f'{value}', content)  # 统一替换为字符串格式

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

# 遍历文件夹中的所有 .js 文件
from pathlib import Path
for target_folder in target_folders:
    # for root, _, files in os.walk(target_folder):
    #     for file_name in files:
    #         if file_name.endswith(".js"):  # 只处理 .js 文件
    #             file_path = os.path.join(root, file_name)
    #             replace_keys_in_file(file_path, flat_i18n)
    for file_path in Path(target_folder).rglob("*.js"):  # 递归查找所有 .js 文件
        replace_keys_in_file(str(file_path), flat_i18n)

print("替换完成！")
