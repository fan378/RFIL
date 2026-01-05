# -*- coding: utf-8 -*-
import pandas as pd
import json
import os
import re
import argparse
import random
import string
from faker import Faker
from bs4 import BeautifulSoup, NavigableString
from tqdm import tqdm
from collections import defaultdict

# ==============================================================================
# SECTION 1: 辅助函数 (保持不变)
# ==============================================================================
# (此部分与之前版本相同，为简洁省略)
def generate_random_zhuyuanhao():
    random_val = random.random()
    if random_val <= 0.5:
        return 'z' + ''.join(random.choices('0123456789', k=random.randint(4, 6)))
    elif random_val <= 0.7:
        return 'zyh' + ''.join(random.choices('0123456789', k=random.randint(4, 6)))
    elif random_val <= 0.9:
        return random.choice(string.ascii_uppercase) + '-' + ''.join(random.choices('0123456789', k=random.randint(4, 6)))
    else:
        return 'hosp' + ''.join(random.choices('0123456789', k=random.randint(4, 6)))

def generate_random_chuanghao():
    choice = random.randint(1, 4)
    if choice == 1:
        content = ''.join(random.choices('0123456789', k=random.randint(2, 5)))
    elif choice == 2:
        return 'RICU'
    elif choice == 3:
        letters = ''.join(random.choices(string.ascii_uppercase, k=random.randint(1, 2)))
        numbers = ''.join(random.choices('0123456789', k=random.randint(1, 2)))
        content = letters + numbers
    else:
        content = '+' + ''.join(random.choices('0123456789', k=random.randint(2, 4)))
    if random.random() < 0.1:
        content += "床"
    return content

def generate_random_name(fake):
    if random.random() < 0.8:
        return fake.name()
    else:
        number = random.randint(0, 9999)
        return f"测试病人{number:04}"

def end_with_underline(key):
    return re.search(r'_\d$', key) is not None
# ==============================================================================
# SECTION 2: 数据加载与解析函数 (已修改)
# ==============================================================================
def parse_html_content(html_string):
    """
    健壮的HTML/XML解析器，修复了NoneType错误。
    """
    if not isinstance(html_string, str) or not html_string.strip().startswith('<'):
        return {'文本': html_string}
    
    soup = BeautifulSoup(html_string, 'lxml')
    content_dict = {}
    
    # 策略1：寻找带有 'token="label"' 的SPAN标签作为键
    labels = soup.find_all('span', attrs={'token': 'label'})
    for label in labels:
        key = label.get_text(strip=True).replace(':', '').strip()
        
        # 健壮地寻找值：遍历后续所有兄弟节点，直到找到第一个有意义的文本
        value = ''
        node = label.next_sibling
        while node:
            if isinstance(node, NavigableString) and node.strip():
                value = node.strip()
                break
            # 如果是标签，则深入查找其文本
            elif hasattr(node, 'get_text') and node.get_text(strip=True):
                 value = node.get_text(strip=True)
                 break
            node = node.next_sibling

        if key: # 即使值为空也记录下来
            content_dict[key] = value

    if not content_dict:
        text = soup.get_text(strip=True, separator='\n')
        content_dict = {'解析文本': text if text else html_string}
        
    return content_dict

def robust_read_csv(filepath, column_names=None):
    """
    最终版健壮CSV读取函数。
    """
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        # print(f"警告: 文件不存在或为空 {filepath}。")
        # 返回一个带有正确列的空DataFrame，以便于合并
        return pd.DataFrame(columns=column_names) if column_names else pd.DataFrame()
            
    try:
        header_option = 'infer' if column_names is None else None
        # engine='python' 更灵活，能处理更复杂的情况
        df = pd.read_csv(filepath, dtype=str, header=header_option, names=column_names, on_bad_lines='skip', engine='python')
        return df.fillna('')
    except Exception as e:
        print(f"错误: 读取 {filepath} 时发生严重错误: {e}")
        return pd.DataFrame(columns=column_names) if column_names else pd.DataFrame()

# ==============================================================================
# SECTION 3: 核心处理与生成函数 (与V4基本一致)
# ==============================================================================
def create_golden_json(data_dir, output_path, tuomin_fixes_path, transfer_keys_path):
    random.seed(2023)
    fake = Faker('zh_CN')

    # 1. 加载规则文件
    try:
        with open(tuomin_fixes_path, 'r', encoding='utf-8') as f:
            tuomin_fixes = [line.strip().split('-->') for line in f if '-->' in line]
        with open(transfer_keys_path, 'r', encoding='utf-8') as f:
            transfer_keys = [line.strip() for line in f]
    except FileNotFoundError as e:
        print(f"错误: 找不到规则文件 - {e}。")
        return

    # 2. **锚点文件加载**
    print("步骤 1/5: 加载锚点文件 wenshu.csv...")
    WENSHU_COLS = ['zylsh', '内容', '文书名', '时间'] 
    df_wenshu = robust_read_csv(os.path.join(data_dir, 'wenshu.csv'), column_names=WENSHU_COLS)
    
    if df_wenshu.empty or 'zylsh' not in df_wenshu.columns:
        print("致命错误: wenshu.csv 为空或处理后仍缺少 'zylsh' 列。无法继续。")
        return

    patient_zylsh = df_wenshu['zylsh'].iloc[0]
    print(f"已确定处理的患者ID: {patient_zylsh}")

    # 3. **条件性加载其他CSV**
    print("步骤 2/5: 条件性加载其他CSV文件...")
    dfs_map = {'wenshu': df_wenshu[df_wenshu['zylsh'] == patient_zylsh]}

    # ### TODO ### 检查并为所有无列头的CSV定义列名
    # 示例：假设hulijilu也无列头
    HULIJILU_COLS = ['zylsh', '内容', '护理记录名', '时间', '录入日期', '最后修改日期'] # 假设它有更多列
    
    other_csvs = ['bingli', 'yizhu', 'hulijilu', 'jiancha', 'jianyan', 'zhenduan', 'tizheng']
    for name in other_csvs:
        col_names = None
        if name == 'hulijilu':
            col_names = HULIJILU_COLS
        # if name == 'bingli':
        #     col_names = BINGLI_COLS # 如果bingli也无列头，在这里定义
        
        df = robust_read_csv(os.path.join(data_dir, f'{name}.csv'), column_names=col_names)
        if not df.empty and 'zylsh' in df.columns:
            dfs_map[name] = df[df['zylsh'] == patient_zylsh]
        else:
            dfs_map[name] = pd.DataFrame()
            
    # 4. **执行内容解析**
    print("步骤 3/5: 执行HTML内容解析...")
    if 'wenshu' in dfs_map and not dfs_map['wenshu'].empty:
        dfs_map['wenshu']['内容'] = dfs_map['wenshu']['内容'].apply(parse_html_content)
    if 'hulijilu' in dfs_map and not dfs_map['hulijilu'].empty:
        # 假设护理记录的内容也在'内容'列
        if '内容' in dfs_map['hulijilu'].columns:
            dfs_map['hulijilu']['内容'] = dfs_map['hulijilu']['内容'].apply(parse_html_content)

    # 5. **组装、清洗和脱敏**
    print(f"步骤 4/5: 为患者 {patient_zylsh} 组装、清洗和脱敏数据...")
    golden_data = {'zylsh': patient_zylsh}
    
    for category, df in dfs_map.items():
        if not df.empty:
            golden_data[category] = df.to_dict('records')
        else:
            golden_data[category] = []
            
    desensitization_map = {
        'TM患者名称TM': generate_random_name(fake),
        'TM住院号IDTM': generate_random_zhuyuanhao(),
        'TM床号IDTM': generate_random_chuanghao(),
    }

    def recursive_clean_and_fix(data):
        if isinstance(data, dict):
            if '文书名' in data and data['文书名'] in transfer_keys and '内容' in data and isinstance(data['内容'], dict):
                processed_str = ' '.join([f"{k} {v}" for k, v in data['内容'].items()])
                data['内容'] = {'文本': processed_str.strip()}
            new_dict = {}
            for k, v in data.items():
                new_v = recursive_clean_and_fix(v)
                if end_with_underline(k):
                    new_k = k[:-2]
                    if new_k in new_dict and isinstance(new_dict[new_k], str) and isinstance(new_v, str):
                        new_dict[new_k] += f"\n{new_v}"
                    else:
                        new_dict[new_k] = new_v
                else:
                    new_dict[k] = new_v
            return new_dict
        elif isinstance(data, list):
            return [recursive_clean_and_fix(item) for item in data]
        elif isinstance(data, str):
            for placeholder, value in desensitization_map.items():
                data = data.replace(placeholder, value)
            for old, new in tuomin_fixes:
                data = data.replace(old, new)
            return data
        else:
            return data

    cleaned_golden_data = recursive_clean_and_fix(golden_data)

    cyxj_data = {}
    if 'hulijilu' in cleaned_golden_data and cleaned_golden_data['hulijilu']:
        for record in cleaned_golden_data['hulijilu']:
            record_name = record.get("文书名", record.get("护理记录名", ""))
            if record and '出院小结' in record_name:
                cyxj_data = {patient_zylsh: record.get("内容", {})}
                break
    cleaned_golden_data['cyxj'] = cyxj_data

    print(f"步骤 5/5: 保存黄金JSON文件到 {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_golden_data, f, ensure_ascii=False, indent=4)
    
    print("处理完成！")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从8个CSV文件生成一个预处理好的'黄金JSON'文件, 严格复刻 process_and_merge 流程。")
    parser.add_argument('--csv_dir', type=str, required=True, help="包含8个原始CSV文件的目录路径。")
    parser.add_argument('--output_path', type=str, default='preprocessed_patient.json', help="输出的黄金JSON文件名及路径。")
    parser.add_argument('--rules_dir', type=str, default='codes/出院小结及子字段', help="包含'脱敏修复.txt'和'transfer_keys.txt'的规则文件目录。")
    
    args = parser.parse_args()
    
    # 检查路径
    tuomin_fixes_file = os.path.join(args.rules_dir, '脱敏修复.txt')
    transfer_keys_file = os.path.join(args.rules_dir, 'transfer_keys.txt')

    if not os.path.exists(args.csv_dir):
        print(f"错误: 输入目录不存在: {args.csv_dir}")
    elif not os.path.exists(tuomin_fixes_file) or not os.path.exists(transfer_keys_file):
        print(f"错误: 规则文件目录不正确或缺少文件: {args.rules_dir}")
    else:
        create_golden_json(args.csv_dir, args.output_path, tuomin_fixes_file, transfer_keys_file)