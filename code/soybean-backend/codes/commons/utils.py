import pymssql
import pandas as pd
import csv
import os
import shutil
# import pyodbc
import time
import chardet
import re
import yaml
import logging
from datetime import timedelta,datetime
import json
import random

def filter_text_and_keep_delimiters(text):
    '''
    内分泌科“出院时情况”删掉 血压/心率/毛糖
    '''
    # 使用正则表达式按逗号或句号分割文本，同时保留分隔符
    segments = re.split(r'([。，,、])', text)
    
    # 初始化一个空列表来存储最终保留的文本段
    filtered_segments = []
    print(segments)    
    # 遍历所有分割后的段落，包括分隔符
    for i in range(0, len(segments), 2):
        segment = segments[i] + (segments[i + 1] if i + 1 < len(segments) else '')
        # 检查当前段落是否包含"血压"或"mmhg"
        if '血压' in segment and 'mmhg' in segment.lower():
            continue
        if '心率' in segment and '次/分' in segment.lower():
            continue
        if ('血糖' in segment or '毛糖' in segment) and 'mmol' in segment.lower():
            continue

        filtered_segments.append(segment)
    
    # 将过滤后的文本段合并为一个字符串
    filtered_text = ''.join(filtered_segments)
    if len(filtered_text) == 0:
        filtered_text = '神清，精神可。'
    else:
        if filtered_text[-1] == '，':
            filtered_text = filtered_text[:-1] + '。'
    return filtered_text

def get_data_lengths(tokenizer,data):
    '''
    拿到指令长度(tokens)
    '''
    model_type = str(type(tokenizer))
    if 'ChatGLM' in model_type:
        input_ids = tokenizer.build_chat_input(data['instruction'])['input_ids'][0].tolist()
        answer = tokenizer.encode(data['output'],add_special_tokens=False)
        input_ids.extend(answer)
        input_ids.append(tokenizer.eos_token_id)
        length = len(input_ids)
    else:
        messages = [
        {"role": "user", "content": data['instruction']}
        ]
        enc = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True
        )
        length = len(enc)
    return length


def wenshu_is_24(wenshu):
    '''
    判断是不是24小时入出院
    '''
    if '24小时内' in wenshu['文书名'] or '出入院记录' in wenshu['文书名'] or '入出院记录' in wenshu['文书名']:
        return True
    return False

def standardize_date_day(date_str):
    """
    Standardize different date formats to time_cyxj common format 'YYYY-MM-DD HH:MM'.

    Args:
    date_str (str): The date string in varied formats.

    Returns:
    str: The standardized date string.
    """
    # Define the formats to be standardized
    format_1 = '%Y年%m月%d日'
    format_2 = '%Y.%m.%d'
    format_3 = '%Y-%m-%d'
    date_str = str(date_str)
    # Try to parse and standardize the date string
    try:
        if '年' in date_str:
            return datetime.strptime(date_str, format_1).strftime('%Y-%m-%d')
        elif '.' in date_str:
            return datetime.strptime(date_str, format_2).strftime('%Y-%m-%d')
        elif '-' in date_str:
            return datetime.strptime(date_str, format_3).strftime('%Y-%m-%d')
        else:
            return f"Error format of {date_str}"
    except ValueError as e:
        return f"Error: {str(e)}"

def get_date_to_day_from_regrex(text):
    '''
    用正则获取时间，允许时间中间出现空格，规则是 4个数字x 1-2个数字x(带0和不带0) 1-2个数字(带0和不带0) 日或空(中文时间会有日，符号时间就是空)
    '''
    date_pattern = r"(\d{4}) *[^0-9] *(\d{1,2}) *[^0-9] *(\d{1,2}) *(?:日)?"
    dates = re.findall(date_pattern, text)
    try:
        trips = dates[0]
        return_str = '{}-{}-{}'.format(trips[0],trips[1],trips[2])
        return return_str
    except:
        return 'regrex find date error'

def standardize_datetime(date_str: str) -> str:
    """
    (高精度版本)
    将多种格式的日期时间字符串标准化为 'YYYY-MM-DD HH:MM:SS'。
    """
    if not isinstance(date_str, str) or not date_str.strip():
        return "Error: Input is not a valid string."

    # 预处理：替换常见中文符号和文字
    processed_str = date_str.strip().replace('：', ':').replace('年', '-').replace('月', '-').replace('日', ' ')
    processed_str = processed_str.replace('.', '-')
    processed_str = re.sub(r'\s+', ' ', processed_str).strip() # 合并多余空格

    # 定义可能的格式列表，从最长（最精确）到最短
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H-%M-%S', # 兼容破折号分隔
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
    ]

    for fmt in formats:
        try:
            dt_obj = datetime.strptime(processed_str, fmt)
            # 统一输出为我们需要的标准格式
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
            
    return f"Error: Could not parse date '{date_str}'"

def get_datetime_from_regex(text: str) -> str:
    """
    (高精度版本)
    用正则从文本中获取完整的日期时间字符串 (YYYY-MM-DD HH:MM:SS)。
    """
    if not isinstance(text, str):
        return 'input text is not a string'
        
    # 正则表达式解释:
    # (\d{4}[-年./]\d{1,2}[-月./]\d{1,2}日?)  - 匹配日期部分，如 2023-01-05, 2023.1.5, 2023年1月5日
    # (\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?    - 这是一个可选部分 (? ... )?
    #   \s+                               - 匹配日期和时间之间的一个或多个空格
    #   \d{1,2}:\d{1,2}                    - 匹配 HH:MM
    #   (?::\d{1,2})?                      - 匹配可选的 :SS 部分 (?:...) 表示非捕获组
    date_pattern = r"(\d{4}[-年./]\d{1,2}[-月./]\d{1,2}日?(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?)"
    
    match = re.search(date_pattern, text)
    
    if match:
        # 返回匹配到的完整日期时间字符串
        return match.group(1)
    else:
        return 'regex find date error'
        
# ------------------------转换指令数据的处理代码---------------------
def process_wenshu_for_ins(wenshu_list):
    ''' 处理文书
    1.删掉无用字段 如 最后修改时间......
    2.时间裁剪到天
    '''
    drop_keys = []
    for wenshu in wenshu_list:
        for drop_key in drop_keys:
            wenshu.pop(drop_key)
        wenshu['时间'] = wenshu['时间'].split(' ')[0]
        # 部分出院记录中，入院与出院时间解析错误，额外处理一下
        if '出院记录' in wenshu['文书名'] and not wenshu_is_24(wenshu) and '出院日期' not in wenshu['内容'].keys():
            print('ori_wenshu:{}'.format(json.dumps(wenshu,ensure_ascii=False,indent=4)))
            try:
                ori_text = wenshu['内容']['入院日期']
                if '出院日期' not in ori_text:
                    print('没有变化,没找到出院日期')
                    continue
                start_index = None
                print('存在入院日期字段！！！')
                wenshu['内容']['入院日期'] = ori_text[:ori_text.index('出院日期')].strip()
                wenshu['内容']['出院日期'] = ori_text[ori_text.index('出院日期')+len('出院日期:'):].strip()
                print('成功处理后文书:\n{}'.format(json.dumps(wenshu,ensure_ascii=False,indent=4)))
            except:
                print('查找并分析错误:\n{}'.format(json.dumps(wenshu,ensure_ascii=False,indent=4)))
                

        # 处理一下包含人名的情况
        # flag = False
        # key_maps = {}
        # for now_key in wenshu['内容'].keys():
        #     lac_res = lac.run(u'{}'.format(now_key))
        #     per_indexes = [index for index, element in enumerate(lac_res[1]) if element == 'PER']
        #     new_key = now_key
        #     # 找到人名
        #     if len(per_indexes) != 0:
        #         per_names = [lac_res[0][per_index] for per_index in per_indexes]
        #         print('在原字段"{}"中找到人名:{}'.format(now_key,per_names))
        #         for per_name in per_names:
        #             new_key = new_key.replace(per_name,'')
        #     # 去掉TM等内容
        #     new_key = new_key.replace('TM员工名称TM','').strip()
        #     if new_key != now_key:
        #         flag = True
        #     # 获得字段映射
        #     key_maps[now_key] = new_key
        # if flag:
        #     # 更新
        #     wenshu_content = wenshu['内容']
        #     new_dict = {key_maps[key]:wenshu_content[key] for key in wenshu_content.keys()}
        #     wenshu['内容'] = new_dict

    return wenshu_list

def process_yizhu_for_ins(yizhu_list):
    ''' 处理医嘱
    1.把删除状态的医嘱去掉
    2.医嘱时间裁剪到天
    3.医嘱详情里，删掉医嘱时间，把空的value删掉
    '''
    processed_data = []
    for yizhu in yizhu_list:
        # 删掉id
        del yizhu['医嘱id']
        # 时间裁剪
        yizhu['医嘱时间'] = yizhu['医嘱时间'].split(' ')[0]
        # 创建一个新的医嘱详情列表，用于存放筛选后的元素
        filtered_details = []
        for detail in yizhu['医嘱详情']:
            # 检查 '状态' 字段是否为 '删除'，如果不是，则加入新的列表
            if '状态' in detail.keys() and detail['状态'] == '删除' or '作废' in detail['医嘱项名称']:
                continue
            
            # 删掉住院流水号和医嘱时间
            del detail['住院流水号']
            del detail['医嘱时间']

            # 检测需要删除的key
            delete_keys = []
            for k,v in detail.items():
                if v == '':
                    delete_keys.append(k)
            for delete_key in delete_keys:
                del detail[delete_key]
            filtered_details.append(detail)

        # 将筛选后的医嘱详情列表替换原来的 '医嘱详情' 字段
        yizhu['医嘱详情'] = filtered_details
        processed_data.append(yizhu)

    # 删除 '医嘱详情' 字段为空的字典元素
    return [item for item in processed_data if item['医嘱详情']]

def process_zhenduan_for_ins(zhenduan_list):
    ''' 处理诊断
    1. 时间分割
    2. 如果类型为空，把类型字段删掉
    3. 如果名称为空，这条数据跳过
    '''
    columns = ['诊断时间','诊断名称','诊断类型']
    processed_zhenduans = []
    for zhenduan in zhenduan_list:
        # 名称为空，跳过
        if zhenduan['诊断名称'].strip() == '':
            continue
        # 时间裁剪到天
        zhenduan['诊断时间'] = zhenduan['诊断时间'].split(' ')[0]
        zhenduan = {k:zhenduan[k] for k in columns}
        processed_zhenduans.append(zhenduan)
    return processed_zhenduans

def process_bingli_for_ins(bingli_list):
    ''' 处理病理
    1. 时间分割
    2. 把空的字段删掉
    '''
    columns = ['临床诊断','病理类型','病理诊断结果','镜下所见','肉眼所见','免疫组化','报告内容']
    processed_binglis = []
    for bingli in bingli_list:
        new_bingli = {}
        new_bingli['检查时间'] = bingli['检查时间'].split(' ')[0]
        new_bingli['报告时间'] = bingli['报告时间'].split(' ')[0]
        for k in columns:
            if bingli[k].strip() != '':
                new_bingli[k] = bingli[k]
        processed_binglis.append(new_bingli)
    return processed_binglis

def extract_datetime_from_text(text: str) -> str:
    """
    使用正则表达式从一段文本中提取第一个看起来像日期的部分。
    """
    if not isinstance(text, str):
        return ""
        
    # 这个正则表达式可以匹配 YYYY-MM-DD HH:MM:SS 以及其他常见变体
    # 例如: '入院时间:2023-05-10 14:30'
    match = re.search(
        r'(\d{4}[-年./]\d{1,2}[-月./]\d{1,2}日?(\s+\d{1,2}:\d{1,2}(:\d{1,2})?)?)', 
        text
    )
    if match:
        return match.group(1) # 返回匹配到的整个日期时间字符串
    return ""

def find_ruyuan_time(i,data):
    '''
    **args**
    i:数据的index
    data:DataFrame的一行

    **功能**
    1. 通过得到的规则，遍历文书并拿到入院时间
    2. 如果入院时间和出院小结中的不一样，直接修改

    **处理逻辑**
    1. 先拿到出院小结中的入院时间
    2. 拿到出院记录中的入院时间
    3. 查找文书中的入院时间
    4. 比较文书中的和出院小结中的，如果匹配则直接结束
    5. 因为有时候出院小结中的存在错误，如果不匹配，再拿出院记录中的时间再匹配一次
    6. 如果全都是error，就找不到。如果是存在符合规则的，但是时间不同，修改一下出院小结中的时间，防止错误数据导致幻觉(耳鼻喉科---index225,文书中查找到的是2020-12-11，但是出院记录和出院小结中的都是2020-12-10)
    7. 最终返回 ||文书中的入院时间|| ||小结中的入院时间|| ||能否找到||
    '''
    ori_index = i
    zylsh = data.iat[0]
    # ----------------------------从出院小结中查找----------------------------
    hulijilu_list = data.iat[7]
    time_cyxj_raw = ""
    for hulijilu in hulijilu_list:
        if hulijilu['护理记录名'] == '出院小结(死亡小结)':
            try:
                time_cyxj_raw = hulijilu['内容']['基本信息']['入院时间']
            except KeyError:
                pass # 字段不存在则跳过
            break
    # ----------------------------从入院文书中查找----------------------------
    wenshu_list = data.iat[5]
    # 文书中的"入院时间"，比如"入院评估单"、"入院记录"等，用一个list保存
    wenshu_time_in_raw = []
    # 出院记录的"入院时间"，可能存在多个来源，比如"出院记录"、"乳腺外科出院记录"，用一个list保存
    now_times_in_record_raw  = []
    for wenshu in wenshu_list:
        # 在出院记录或24小时记录中查找入院时间
        if ('出院记录' in wenshu['文书名'] and not wenshu_is_24(wenshu)) or wenshu_is_24(wenshu):
            try:
                text = wenshu['内容'].get('入院日期') or wenshu['内容'].get('姓名')
                if text:
                    time_in_record = extract_datetime_from_text(text)
                    if time_in_record:
                        now_times_in_record_raw.append((time_in_record, wenshu['文书名']))
            except KeyError:
                continue

        # 在其他入院文书中查找
        search_map = {
            '新入院评估单': ['一、基本信息'],
            '入院告知书': ['患者信息'],
            '告未成年患者监护人书': ['患者信息'],
            '入院记录': ['患者一般情况', '病人信息'],
            '入院录': ['病人信息']
        }
        
        for doc_name, fields in search_map.items():
            if doc_name in wenshu['文书名']:
                for field in fields:
                    try:
                        text = wenshu['内容'][field]
                        time_in = extract_datetime_from_text(text)
                        if time_in:
                            wenshu_time_in_raw.append((time_in, wenshu['文书名']))
                            break # 找到一个就不用再找这个文书的其他字段了
                    except (KeyError, TypeError):
                        continue
    # 此处得到了三类入院数据
    # time_cyxj             出院小结中的入院时间
    # wenshu_time_in        病历文书中的入院时间
    # now_times_in_record   出院记录中的入院时间
    # ----------------------------分析是否匹配----------------------------
    # 出院小结时间分割到天
    # 标准化所有找到的时间
    time_cyxj_std = standardize_datetime(str(time_cyxj_raw))
    
    wenshu_times_std = {standardize_datetime(t[0]) for t in wenshu_time_in_raw}
    # 移除错误结果，只保留有效时间
    wenshu_times_std = {t for t in wenshu_times_std if not t.startswith('Error')}

    record_times_std = {standardize_datetime(t[0]) for t in now_times_in_record_raw}
    record_times_std = {t for t in record_times_std if not t.startswith('Error')}

    # 决策逻辑：
    # 1. 如果文书中有统一且有效的时间，采纳它。
    if len(wenshu_times_std) == 1:
        final_time = wenshu_times_std.pop()
        return wenshu_time_in_raw, final_time, True
    
    # 2. 如果出院小结的时间有效，并且在文书时间或出院记录时间中得到验证，采纳它。
    if not time_cyxj_std.startswith('Error'):
        if time_cyxj_std in wenshu_times_std or time_cyxj_std in record_times_std:
            return wenshu_time_in_raw, time_cyxj_std, True

    # 3. 如果出院记录中有统一且有效的时间，采纳它。
    if len(record_times_std) == 1:
        final_time = record_times_std.pop()
        return wenshu_time_in_raw, final_time, True

    # 4. 如果都无法确定，返回失败。
    return wenshu_time_in_raw, "", False



def find_chuyuan_time(i,data):
    '''
    **args**
    i:数据的index
    data:DataFrame的一行

    **功能**
    1. 通过判断医嘱是否能推理出出院时间，若不能，返回"无法判断"
    2. 拿到 出院记录/出院小结 中的出院时间，这是真实出院时间，以对检查、检验、病理进行mask
    '''
    zylsh = data.iat[0]
    yizhu_list = data.iat[3]
    wenshu_list =  data.iat[5]
    hulijilu_list = data.iat[7]
    # ----------------------------从出院小结中查找----------------------------
    time_cyxj_raw = ''
    for hulijilu in hulijilu_list:
        if hulijilu['护理记录名'] == '出院小结(死亡小结)':
            try:
                time_cyxj_raw = hulijilu['内容']['基本信息']['出院时间']
            except KeyError:
                pass
            break
    # 从出院记录中查找
    # 出院记录的"出院时间"，可能存在多个来源，比如"出院记录"、"乳腺外科出院记录"，用一个list保存
    wenshu_time_out_raw  = []
    # ----------------------------从出院记录中查找----------------------------
    for wenshu in wenshu_list:
        if ('出院记录' in wenshu['文书名'] and not wenshu_is_24(wenshu)) or \
           wenshu_is_24(wenshu) or \
           '呼吸日间病房护理记录' in wenshu['文书名']:
            try:
                # 尝试从'出院日期'字段或'姓名'字段所在的文本中提取
                text = wenshu['内容'].get('出院日期') or wenshu['内容'].get('姓名')
                if text:
                    time_out = extract_datetime_from_text(text)
                    if time_out:
                         wenshu_time_out_raw.append((time_out, wenshu['文书名']))
            except KeyError:
                continue

    # ----------------------------从医嘱中查找----------------------------
    res_chuyuan_flow_ok = False # 标记出院流程是否清晰
    for yizhu in yizhu_list:
        # 查找具体的出院医嘱，而不仅仅是"出院"二字
        if '出院' in yizhu['医嘱详情'][0]['医嘱项名称'] and yizhu['医嘱详情'][0]['医嘱项名称'] != '出院':
            res_chuyuan_flow_ok = True
            break
    # ----------------------------分析是否匹配----------------------------
    # 出院时间统计规则
    # 出院小结中的出院日期，用作匹配
    # 文书中，查找出院记录的出院日期
    # 查找医嘱中和出院相关的信息(可能有多个，有的作废，有的已结束等等)

    time_cyxj_std = standardize_datetime(str(time_cyxj_raw))
    
    wenshu_times_std = {standardize_datetime(t[0]) for t in wenshu_time_out_raw}
    wenshu_times_std = {t for t in wenshu_times_std if not t.startswith('Error')}

    res_chuyuan_time = ''
    data_is_normal = True
    
    # 决策逻辑
    # 1. 优先采纳出院小结的时间，如果它是有效的
    if not time_cyxj_std.startswith('Error'):
        res_chuyuan_time = time_cyxj_std
    # 2. 如果小结时间无效，但文书中有唯一确定的时间，采纳文书时间
    elif len(wenshu_times_std) == 1:
        res_chuyuan_time = wenshu_times_std.pop()
    # 3. 如果两者都无效，则无法确定时间
    else:
        res_chuyuan_time = '9999-99-99 00:00:00' # 使用一个清晰的“未找到”标记
        data_is_normal = False # 标记数据异常

    # 如果时间找到了，但出院流程医嘱不清晰，也标记为异常
    if res_chuyuan_time != '9999-99-99 00:00:00' and not res_chuyuan_flow_ok:
        data_is_normal = False
        
    return (time_cyxj_raw, wenshu_time_out_raw), res_chuyuan_time, res_chuyuan_flow_ok, data_is_normal


# ----------------------------------------------------------
# 把候选项加上双引号，拼接成字符串
def transfer_choices_to_str(out_keys,use_Chinese = True):
    out_keys = ['“{}”'.format(time_cyxj) for time_cyxj in out_keys]
    join_str = random.choice(['，','、'])
    if use_Chinese:
        out_keys_str = join_str.join(out_keys[:-1]) + random.choice(['和','以及','与',join_str]) + out_keys[-1]
    else:
        out_keys_str = join_str.join(out_keys)
    return out_keys_str
# 把检验为空的行都删掉(构造检验相关任务时需要预先处理一下)
def drop_empty_jianyan_rows(row):
    if len(row.iat[11]) != 0:
        return True
    return False

def group_by_thousand(input_dict):
    '''
    把dict中的key变成以1000为一个范围
    '''
    grouped_dict = {}
    for key, value in input_dict.items():
        # 计算键属于哪个区间（例如，1500的键属于1区间，2500的键属于2区间）
        group = f"{(key // 1000) * 1000}-{(key // 1000 + 1) * 1000 -1}"
        # 将值累加到相应区间
        if group in grouped_dict:
            grouped_dict[group] += value
        else:
            grouped_dict[group] = value
    grouped_dict = {k:grouped_dict[k] for k in sorted(grouped_dict.keys(), key = lambda x:int(x.split('-')[0]))}
    return grouped_dict
    
def transfer_value(val):
    '''
    load dataframe后，字符串转json
    '''
    if val == '':
        return []
    else:
        return json.loads(val)

def json_to_text(value:dict,tab_num = 0, empty_skip = True):
    '''
    json转text
    '''
    text_str = ''
    for key in value.keys():
        # 如果是嵌套
        if type(value[key]) == dict:
            text_str = text_str + tab_num * '\t' + str(key) + '\n' + json_to_text(value[key], tab_num + 1, empty_skip)
        elif type(value[key]) == list:
            text_str = text_str + tab_num * '\t' + str(key) + '\n'
            for v_item in value[key]:
                text_str = text_str + json_to_text(v_item, tab_num + 1, empty_skip) + '\n'
        # 不是嵌套
        elif value[key] != None:
            if empty_skip and value[key] == '':
                continue
            text_str = text_str + tab_num * '\t' + '{}:{}\n'.format(str(key),str(value[key]))
    return text_str

def has_empty_key(value:dict):
    '''
    是否有空值的key
    '''
    find_flag = False
    for key in value.keys():
        # 如果是嵌套
        if type(value[key]) == dict:
            find_flag = find_flag | has_empty_key(value[key])
        elif type(value[key]) == list:
            for v_item in value[key]:
                find_flag = find_flag | has_empty_key(v_item)
        # 不是嵌套
        elif value[key] != None:
            if value[key] == '':
                return True
    return find_flag

def get_every_nums(total,num_people):
    base = total // num_people
    
    # 使用取模运算来计算多余的分数
    remainder = total % num_people
    
    # 创建一个列表，包含每个人的分数
    distribution = [base for _ in range(num_people)]
    
    # 分配多余的分数
    for i in range(remainder):
        distribution[i] += 1
    return distribution

def get_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file,encoding='utf-8')        
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

def get_pattern_and_replace_datas(path):
    """
    加载护理额外脱敏的分析结果
    """
    re_compiles = []
    replace_datas = []
    with open(path,'r',encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            original,replace = line.split('-->')
            replace = 'TM'+replace+'TM'
            original_splits = original.split(',')
            if len(original_splits) == 1:
                re_pattern = re.compile(r'(<{}(?: [^>/]*?)?>).*?<'.format(original_splits[0]))
            else:
                mates = '(?:'+'|'.join(original_splits)+')'
                re_pattern = re.compile(r'(<{}(?: [^>/]*?)?>).*?<'.format(mates))
            re_compiles.append(re_pattern)
            replace_datas.append(replace)
    return re_compiles,replace_datas

def get_pattern_admission_and_bed():
    """
    文书脱敏住院号和床号
    """
    re_compiles = []
    replace_datas = []
    re_compiles.append(re.compile(r'(住院号(?::|：|&nbsp;| ){1,2}<[^>]*?>)[A-Za-z0-9]+<'))
    replace_datas.append('TM住院号IDTM')
    re_compiles.append(re.compile(r'(床[号位](?::|：|&nbsp;| ){1,2}<[^>]*?>)[\+0-9A-Za-z床]+<'))
    replace_datas.append('TM床号IDTM')
    return re_compiles,replace_datas
    

def get_pattern_and_replace_datas_2():
    """
    自定义护理额外脱敏
    """
    re_compiles = []
    replace_datas = []
    re_compiles.append(re.compile(r'住院号(?::|：|&nbsp;| ){1,2}[A-Za-z0-9]+ '))
    replace_datas.append('住院号：TM住院号IDTM ')
    re_compiles.append(re.compile(r'床 *[号位](?::|：|&nbsp;| ){1,2}[\+0-9A-Za-z床]+ '))
    replace_datas.append('床号：TM床号IDTM ')
    return re_compiles,replace_datas

def get_pattern_and_replace_datas_3():
    """
    自定义护理额外脱敏
    """
    re_compiles = []
    replace_datas = []
    re_compiles.append(re.compile(r'(住院号(?::|：|&nbsp;| ){1,2}<.*?<Text>)[A-Za-z0-9]+(</Text>.*?<InnerValue>)[A-Za-z0-9]+(</InnerValue>)'))
    replace_datas.append('TM住院号IDTM')
    re_compiles.append(re.compile(r'(床 *[号位](?::|：|&nbsp;| ){1,2}<.*?<Text>)[\+0-9A-Za-z床]+(</Text>.*?<InnerValue>)[\+0-9A-Za-z床]+(</InnerValue>)'))
    replace_datas.append('TM床号IDTM')
    return re_compiles,replace_datas

def get_time(fmt='%Y-%m-%d %H:%M:%S'):
    """
    获取当前时间
    """
    ts = time.time()
    ta = time.localtime(ts)
    t = time.strftime(fmt, ta)
    return t

# 加载yaml
def load_config(config_file):
    encoding = detect_encoding(config_file)
    with open(config_file, "r", encoding=encoding['encoding']) as f:
        return yaml.safe_load(f)
    
# 链接数据库
def connect_db(config_file,driver="{SQL Server}"):
    db_configs = load_config(config_file)
    # ip
    sql_host = db_configs['sql_host']
    # 端口(默认1433)
    sql_port = db_configs['sql_port']
    # 用户
    sql_user = db_configs['sql_user']
    # 密码
    sql_passwd = db_configs['sql_passwd']
    # 数据库名
    sql_database = db_configs['sql_database']
    connect_sentence = 'DRIVER={};SERVER={},{};DATABASE={};ENCRYPT=no;UID={};PWD={};'.format(driver,sql_host,sql_port,sql_database,sql_user,sql_passwd)
    return pyodbc.connect(connect_sentence)

# 检测文件编码
def detect_encoding(file):
    res_to_detest = b'' 
    with open(file, 'rb') as f:
        for line_idx,line in enumerate(f.readlines()):
            if line_idx == 10:
                break
            res_to_detest += line
    result = chardet.detect(res_to_detest)
    if result['encoding'] == 'GB2312':
        result['encoding'] = 'GB18030'
    return result

# 加载excel或者csv
def load_excel_csv(file,columns=5,head=None):
    converters = {col:str for col in range(columns)}
    if file.endswith('csv'):
        result = detect_encoding(file)
        print('以{}编码格式加载csv文件:{}'.format(result['encoding'],file))
        ###############################################################################
        # 尝试读取文件的第一行以确定列数   yc添加
        with open(file, 'r', encoding=result['encoding']) as f:  
            first_line = f.readline().strip()  
            # 如果第一行是空的，则假设文件是空的  
            if not first_line:  
                return pd.DataFrame()  # 返回一个带有默认列名的空DataFrame  
        ################################################################################
        try:
            datas = pd.read_csv(file,header=head,converters=converters,encoding=result['encoding'],sep=',')
        except:
            datas = pd.read_csv(file,header=head,converters=converters,encoding=result['encoding'],sep='\t')
    else:
        print('加载excel文件:{}'.format(file))
        datas = pd.read_excel(file,header=head,converters=converters)
    if head!= None:
        datas.columns = list(range(len(datas.columns)))
    return datas

# 字典树相关
#########################################################
# 字典树替换函数
def build_dictonarys(lists):
    dicts = {}
    for name in lists:
        now_dict = dicts
        for word in name:
            if word not in now_dict:
                now_dict[word] = {}
            now_dict = now_dict[word]
        now_dict['end'] = 'end'
    return dicts

def trie_search(text,dicts,idx):
    res = -1
    for index in range(idx,len(text)):
        word = text[index]
        # 出现end，说明当前是一个需要查找的名字的结尾，先存起来，因为要找到最长
        if 'end' in dicts.keys():
            res = index-idx
        # 当前字符不在现在的树中，返回
        if word not in dicts.keys():
            return res
        # 在树中，继续查找
        else:
            dicts = dicts[word]
    if 'end' in dicts.keys():
        return len(text) - idx
    else:
        return res
def find_idx_and_trie_replace(text,dicts,replace_name):
    idx_list = []
    idx = 0
    while idx < len(text):
        # 字典树search
        idx_length = trie_search(text,dicts,idx)
        if(idx_length != -1):
            idx_list.append((idx,idx+idx_length))
            idx = idx + idx_length -1
        idx += 1
    new_text = ''
    idx = 0
    for id_tuple in idx_list:
        new_text += text[idx:id_tuple[0]] + replace_name
        idx = id_tuple[1]
    new_text += text[idx:]
    return new_text

def find_idx(text,dicts):
    idx = 0
    while idx < len(text):
        # 字典树search
        idx_length = trie_search(text,dicts,idx)
        if(idx_length != -1):
            return True
        idx += 1
    return False

#########################################################
def execute_sql_file(sql_file,cursor,mode='multi',depart_id=None,log=None):
    encoding = detect_encoding(sql_file)
    if mode == 'line':
        # 一行一行读取
        with open(sql_file,'r',encoding=encoding['encoding']) as f:
            for line in f.readlines():
                if line.strip() == '':
                    continue
                if '{}' in line:
                    line = line.format(depart_id)
                if log == None:
                    print('execute:{}'.format(line.strip()))
                else:
                    log.info('execute:{}'.format(line.strip()))

                try:
                    cursor.execute(line)
                    if log == None:
                        print('success')
                    else:
                        log.info('success')
                except Exception as e:
                    if log == None:
                        print('error:{}'.format(e))
                    else:
                        log.info('error:{}'.format(e))
    elif mode == 'multi':
        # 读取到分号就执行
        sql_sentence = ''
        with open(sql_file,'r',encoding=encoding['encoding']) as f:
            for line in f.readlines():
                line = line.strip()
                if '{}' in line:
                    line = line.format(depart_id)
                sql_sentence = sql_sentence.strip() + ' ' + line
                if sql_sentence.endswith(';'):
                    if log == None:
                        print('execute:{}'.format(sql_sentence))
                    else:
                        log.info('execute:{}'.format(sql_sentence))
                    try:
                        cursor.execute(sql_sentence)
                        if log == None:
                            print('success')
                        else:
                            log.info('success')
                    except Exception as e:
                        if log == None:
                            print('error:{}'.format(e))
                        else:
                            log.info('error:{}'.format(e))
                    sql_sentence = ''
    else:
        raise ValueError('读取sql的模式错误')

# 向新服务器中插入表
def share_datas(from_conn,to_cursor,table_name,sql_file):
    datas = pd.read_sql('SELECT * FROM {}'.format(table_name), from_conn)
    with open(sql_file,'r') as f:
        for line in f:
            line = line.strip() 
            if not '?' in line:
                to_cursor.execute(line)
            else:
                for i in range(datas.shape[0]):
                    to_cursor.execute(line,tuple(datas.iloc[i]))

def insert_datas_from_files(cursor,sql_file,ids,log):
    with open(sql_file,'r') as f:
        for line in f:
            line = line.strip() 
            log.info('execute:{}'.format(line))
            if not '?' in line:
                cursor.execute(line)
            else:
                for id in ids:
                    cursor.execute(line,(id))
