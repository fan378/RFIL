import re
import json
import os
import logging
import openai
from datetime import datetime
from collections import OrderedDict
from codes.commons.frontend_constants import *
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from FlagEmbedding import BGEM3FlagModel

LOGGER_NAME = "interaction_log"

def setup_global_logger(log_file_name: str):
    """
    【最终版-静默模式】配置一个全局的日志记录器。
    日志目录固定为 "Intermediate_process/temp/"，并且只输出到文件，不在控制台打印。

    Args:
        log_file_name (str): 包含日期的日志文件名, 例如 "interaction_log_2023-10-27.log"。
    """
    # 日志目录固定为固定路径
    log_dir = os.path.join("Intermediate_process", "temp")

    # 按名称获取logger实例
    global LOGGER_NAME
    LOGGER_NAME = log_file_name
    logger = logging.getLogger(LOGGER_NAME)
    
    # 设置日志级别
    logger.setLevel(logging.INFO)
    
    # 通过检查logger是否已有handlers，防止重复配置
    if not logger.handlers:
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 使用传入的文件名和固定的目录，组合成完整路径
        log_path = os.path.join(log_dir, log_file_name)
        
        # 创建文件处理器 (只保留这一种处理器)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        
        # 创建日志格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - \n%(message)s\n'
        )
        file_handler.setFormatter(formatter)
        
        # 只将文件处理器添加到logger
        logger.addHandler(file_handler)
        
        print(f"全局日志记录器 '{LOGGER_NAME}' 已配置完成，日志将静默保存在: {log_path}")

def generate_qwen_response(
    model, 
    tokenizer, 
    user_prompt: str, 
    system_prompt: str = "你是一个专业的电子病历总结专家，请你科学、专业的态度，严格基于给定病理文书的信息来回答问题。",
    max_new_tokens: int = 8192,
    temperature: float = 0.01
) -> str:
    """
    使用指定的Qwen模型和分词器，为给定的用户输入生成一次性响应。
    这是一个无状态的函数，不维护历史记录。

    Args:
        model: 已加载的 AutoModelForCausalLM 模型对象。
        tokenizer: 已加载的 AutoTokenizer 分词器对象。
        user_prompt (str): 用户的输入，即您想要模型处理的核心指令和内容。
        system_prompt (str): 系统提示词，用于设定模型的角色和行为。
        max_new_tokens (int): 模型生成的最大token数量。
        temperature (float): 生成的温度，值越小越确定。

    Returns:
        str: 模型生成的文本响应。
    """
    
    # 1. 构建消息列表，每次调用都是一个全新的对话
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # 2. 应用聊天模板，这是官方推荐的、最可靠的输入格式化方式
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False
    )

    # 3. 将格式化后的文本进行分词，并移动到模型所在的设备
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    # 4. 调用模型生成函数进行推理
    # 使用 **inputs 解包，可以将 input_ids 和 attention_mask 等都传入
    response_ids = model.generate(
        **inputs, 
        max_new_tokens=max_new_tokens,
        temperature=temperature
    )

    # 5. 从返回的ID中，切分出新生成的部分
    # response_ids[0] 包含了输入和输出的所有ID，需要去掉输入部分
    output_ids = response_ids[0][len(inputs.input_ids[0]):]

    # 6. 将新生成的ID解码成字符串
    response = tokenizer.decode(output_ids, skip_special_tokens=True)

    # 7. **【核心修改】** 获取全局logger并记录日志
    try:
        # 按名称获取全局logger实例
        logger = logging.getLogger(LOGGER_NAME)
        
        # 健壮性检查：确认logger是否被有效配置过（即有handler）
        if logger.hasHandlers():
            log_message = (
                f"--- Qwen Model Interaction Log ---\n"
                f"[System Prompt]:\n{system_prompt}\n\n"
                f"[User Prompt]:\n{user_prompt}\n\n"
                f"[Model Response]:\n{response}\n"
                f"------------------------------------"
            )
            logger.info(log_message)
    except Exception as e:
        # 如果日志记录失败，打印错误但不要让主程序崩溃
        print(f"警告：记录日志时发生错误 - {e}")

    return response

def chat_with_api(model, user_prompt, system_prompt="你是一个专业的电子病历总结专家，请你科学、专业的态度，严格基于给定病理文书的信息来回答问题。", max_tokens=4096, temperature=0.01):
    if model == "pretrained":
        model_name="Qwen3-8B-Generate"
        client = openai.OpenAI(
        api_key="emr",
        base_url="http://172.20.137.188:8054/v1"
        )
    else:
        model_name="Qwen3-4B-Post"
        client = openai.OpenAI(
        api_key="emr",
        base_url="http://172.20.137.188:8047/v1"
    )

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.9,
        extra_body={
            "stop_token_ids": [151644, 151645, 151643],
            "chat_template_kwargs": {"enable_thinking": False},
        },
    )
    # response = completion.choices[0].message.content
    response = completion.choices[0].message.reasoning_content
    try:
        # 按名称获取全局logger实例
        logger = logging.getLogger(LOGGER_NAME)
        
        # 健壮性检查：确认logger是否被有效配置过（即有handler）
        if logger.hasHandlers():
            log_message = (
                f"--- Qwen Model Interaction Log ---\n"
                f"[System Prompt]:\n{system_prompt}\n\n"
                f"[User Prompt]:\n{user_prompt}\n\n"
                f"[Model Response]:\n{response}\n"
                f"------------------------------------"
            )
            logger.info(log_message)
    except Exception as e:
        # 如果日志记录失败，打印错误但不要让主程序崩溃
        print(f"警告：记录日志时发生错误 - {e}")
    return response


def read_json(json_path):
    with open(json_path, 'r',encoding='utf8') as f:
        data = json.load(f)
    return data

def save_json(json_path, data):
    with open(json_path, 'w',encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
import re
import copy

def split_medical_data_doctor(original_data):
    processed = []
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}')  # 匹配日期开头

    for item in original_data:
        item = item.strip()
        # 处理描述型数据（按句号切分）
        if date_pattern.match(item):
            parts = [p.strip() for p in item.split('。') if p.strip()]
            processed.append(parts)
        # 处理指标型数据（按两个以上空格切分）
        else:
            parts = re.split(r'\s{2,}', item)  # 匹配两个及以上连续空格
            cleaned = [p.strip() for p in parts if p.strip()]
            processed.append(cleaned)
    return processed


def split_medical_data_patient(original_data):
    processed = []
    #date_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+(.*)')

    for item in original_data:
        item = item.strip()
        #current_group = []

        # ========= 处理描述型数据 =========
        if re.search(r'。', item) and not re.search(r'[;\t]', item):
            parts = [p.strip() + '。' for p in item.split('。') if p.strip()]
            if parts and parts[-1].endswith('。') and not item.endswith('。'):
                parts[-1] = parts[-1][:-1]
            processed.append(parts)
            continue

        # ========= 处理指标型数据 =========
        # 按分号/制表符切分
        raw_parts = re.split(r'[;\t\n]+', item)
        cleaned_parts = [p.strip() for p in raw_parts if p.strip()]

        # 分离首项日期
        '''if cleaned_parts:
            first_part = cleaned_parts[0]
            match = date_pattern.match(first_part)
            if match:
                date = match.group(1)
                remaining = match.group(2)
                current_group.append(date)
                if remaining:
                    current_group.append(remaining)
                current_group.extend(cleaned_parts[1:])
            else:
                current_group = cleaned_parts.copy()'''

        processed.append(cleaned_parts)

    return processed
def split_medical_data_source(original_data):
    processed = []
    #date_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+(.*)')

    for item in original_data:
        if isinstance(item, str):
            processed.append(item)
        if isinstance(item, list):
            if len(item)==0:
                processed.append(item)
            else:
                item = item[0].strip()
            #current_group = []

             # ========= 处理描述型数据 =========
            # ========= 处理指标型数据 =========
            # 按分号/制表符切分
                raw_parts = re.split(r'[;\t]+', item)
                cleaned_parts = [p.strip() for p in raw_parts if p.strip()]
                processed.append(cleaned_parts)
    return processed

def process_format(ori_datas):
    final_format = {
        '患者基本信息': {
            '住院号': '基本信息---住院号',
            '床号': '基本信息---床号',
            '入院时间': '基本信息---入院时间',
            '出院时间': '基本信息---出院时间',
            '科室': '基本信息---科别',
            '姓名': '基本信息---姓名',
            '年龄': '基本信息---年龄',
            '性别': '基本信息---性别',
            '低压(BP低)': '生命体征---BP低',
            '高压(BP高)': '生命体征---BP高',
            '脉搏(P)': '生命体征---P',
            '呼吸(R)': '生命体征---R',
            '体温(T)': '生命体征---T',
            '入院诊断': '基本信息---入院诊断',
            '入院时简要病史': '入院时简要病史',
            '体检摘要': '体检摘要'
        },
        '住院期间医疗情况': '住院期间医疗情况',
        '出院诊断': '基本信息---出院诊断',
        '病程与治疗情况': '病程与治疗情况',
        '出院后用药建议': '出院后用药建议',
        '出院时情况': '出院时情况',
    }

    split_colums = ['入院时简要病史','体检摘要','住院期间医疗情况', '病程与治疗情况', '出院后用药建议', '出院时情况']

    for key, value in final_format.items():
        if isinstance(value, dict):
            for sub_key, path in value.items():
                path_parts = path.split('---')
                data = ori_datas
                for part in path_parts:
                    data = data.get(part, "")
                    if isinstance(data, list):
                        if len(data)>=1:
                            data=data[0]
                if sub_key in split_colums:
                    data = re.split(r'(?<=[。\n])', data)
                    if data[-1].strip() == '':
                        data = data[:-1]
                final_format[key][sub_key] = data
                
        elif isinstance(value, str):
            path_parts = value.split('---')
            data = ori_datas
            for part in path_parts:
                data = data.get(part, "")
                if isinstance(data, list):
                    if len(data)>=1:
                        data=data[0]
            if key in split_colums and key != '住院期间医疗情况':
                data = re.split(r'(?<=[。\n])', data)
                if data[-1].strip() == '':
                    data = data[:-1]
            elif key == '住院期间医疗情况':
                temps = re.split(r'(?=\d{4}-\d{2}-\d{2})', data)
                data = [s for s in temps if s]
            final_format[key] = data
    return final_format

def process_source(source):
    for key, value in Each_filed_source_names['患者基本信息'].items():
        source[key] = {}
        for book in value:
            if book in source['患者基本信息']:
                source[key][book] = source['患者基本信息'][book]
    del source['患者基本信息']
    
    temp = {}
    for book in source['住院期间医疗情况']:
        if book in Each_filed_source_names['住院期间医疗情况']:
            temp[book] = source['住院期间医疗情况'][book]
    source['住院期间医疗情况'] = temp
    
    return source

from openai import OpenAI
def process_pattern(source,patient,model,tokenizer):
    client = OpenAI(
        api_key="sk-d9511b84b7374916938eaa9531432ab5",
        base_url="https://api.deepseek.com/v1"

    )

    new_source_pattern = source_pattern
    for field in ['住院号', '床号', '入院时间', '出院时间', '科室', '姓名', '性别', '入院时间','出院时间','入院时简要病史','体检摘要','入院诊断']:
        new_source_pattern[field] = [patient['患者基本信息'][field]]
    
    for field,value in transfer_format.items():
        new_source_pattern[field] = [patient['患者基本信息'][value]]
    
    for field in ['病程与治疗情况', '出院后用药建议', '出院时情况', '出院诊断']:
        new_source_pattern[field] = [patient[field]]
    
    for field in ['病程与治疗情况', '出院后用药建议', '出院时情况','入院时简要病史','体检摘要']:
        result = []
        for item in new_source_pattern[field][0]:
            result.append([item])
        new_source_pattern[field]= result
    
    # 住院期间医疗情况
    new_source_pattern['住院期间医疗情况'] = []
    for item in source['住院期间医疗情况']['简化过滤检验'].split('\n'):
        new_source_pattern['住院期间医疗情况'].append([item])
    for item in source['住院期间医疗情况']['全部检查'].split('\n\n'):
        new_source_pattern['住院期间医疗情况'].append([item])

    # 年龄
    new_source_pattern['年龄'] = [f"年龄:{patient['患者基本信息']['年龄']}"]

    # gpt 溯源
    for field in ['病程与治疗情况', '出院后用药建议', '出院时情况','入院时简要病史','体检摘要']:
        if field in ['病程与治疗情况', '出院后用药建议', '出院时情况']:
            colums1 = patient[field]
        else:
            colums1 = patient['患者基本信息'][field]

        new_prompt = gpt_prompt.format( 
            json.dumps(colums1, ensure_ascii=False), 
            json.dumps(source[field], ensure_ascii=False)
        )

        try:
            # 使用远程 API
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": new_prompt}],
                model="deepseek-chat",
            )
            response_content = chat_completion.choices[0].message.content

            # 使用本地模型
            # response_content = generate_qwen_response(model, tokenizer, new_prompt)
        
            # 
            new_source_pattern[field] = eval(response_content)
        except Exception as e:
            print(e)
            pass


    return new_source_pattern

    
def split_text_with_regex(text: str):
    if not isinstance(text, str) or not text.strip(): return []
    text = re.sub(r'[\n\t\r]+', '\n', text).strip()
    text = re.sub(r'([。！？])', r'\1\n', text)
    return [s.strip() for s in text.split('\n') if s and s.strip()]
def process_pattern_new(source,patient):

    new_source_pattern = source_pattern
    try:
        os.environ["CUDA_VISIBLE_DEVICES"] = "1"
        path = "/root/nas/llm_models/bge-m3"
        model = BGEM3FlagModel(path, use_fp16=True) 
        print(f"BGE-M3 模型从 '{path}' 加载成功！")
    except Exception as e:
        print(f"错误: 无法加载模型。请检查路径 '{path}'。")
        print(f"具体错误: {e}")
        model = None
    for field in ['住院号', '床号', '入院时间', '出院时间', '科室', '姓名', '性别', '入院时间','出院时间','入院时简要病史','体检摘要','入院诊断']:
        new_source_pattern[field] = [patient['患者基本信息'][field]]
    
    for field,value in transfer_format.items():
        new_source_pattern[field] = [patient['患者基本信息'][value]]
    
    for field in ['病程与治疗情况', '出院后用药建议', '出院时情况', '出院诊断']:
        new_source_pattern[field] = [patient[field]]
    
    for field in ['病程与治疗情况', '出院后用药建议', '出院时情况','入院时简要病史','体检摘要']:
        result = []
        for item in new_source_pattern[field][0]:
            result.append([item])
        new_source_pattern[field]= result
    
    # 住院期间医疗情况
    new_source_pattern['住院期间医疗情况'] = []
    if '简化过滤检验' in source['住院期间医疗情况']:
        for item in source['住院期间医疗情况']['简化过滤检验'].split('\n'):
            new_source_pattern['住院期间医疗情况'].append([item])
    else:
        new_source_pattern['住院期间医疗情况'].append([])
    if '全部检查' in source['住院期间医疗情况']:
        for item in source['住院期间医疗情况']['全部检查'].split('\n\n'):
            new_source_pattern['住院期间医疗情况'].append([item])
    else:
        new_source_pattern['住院期间医疗情况'].append([])

    # 年龄
    new_source_pattern['年龄'] = [f"年龄:{patient['患者基本信息']['年龄']}"]
    #  溯源
    
    for field in ['病程与治疗情况', '出院后用药建议', '出院时情况','入院时简要病史','体检摘要']:
        if field in ['病程与治疗情况', '出院后用药建议', '出院时情况']:
            colums1 = patient[field]
        else:
            colums1 = patient['患者基本信息'][field]
        source_1 = source[field]
        source_1 = list(source_1.values())
        matche_list = []
        for items in colums1:
            matche = []
            for item in source_1:
                source_2 = split_text_with_regex(item)
                for k in source_2:
                    strence = []
                    strence.append(items)
                    strence.append(k)
                    matche.append(strence)
            #计算相似度
            scores_dict = model.compute_score(matche, batch_size=32)
            arr = list(scores_dict.values())[0]

            # # 将所有文本展平为一维列表
            # all_texts = [text for pair in matche for text in pair]
            
            # # 获取所有文本的嵌入向量
            # client = openai.OpenAI(
            #         api_key="emr",
            #         base_url="http://172.20.137.188:19198/v1"
            #         )
            # response = client.embeddings.create(
            #     model="bge-m3",
            #     input=all_texts
            # )
            
            # # 提取嵌入向量
            # embeddings = [np.array(data.embedding) for data in response.data]
            
            # # 计算每对文本的相似度
            # similarity_scores = []
            # for i in range(0, len(embeddings), 2):
            #     # 确保有足够元素
            #     if i+1 < len(embeddings):
            #         # 计算当前对的余弦相似度
            #         sim = cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0]
            #         similarity_scores.append(sim)
            #scores_dict = model.compute_score(matche, batch_size=32)
            # arr = list(similarity_scores)
            # print(arr)
            max_value = max(arr)
            max_index = arr.index(max_value)
            # print(matche[max_index][1])
            matche_list.append([matche[max_index][1]])
            # print(f"处理字段 {field} 的匹配结果: {matche[max_index][1]}，相似度: {max_value:.4f}")
        new_source_pattern[field] = matche_list
    return  new_source_pattern
#patient_data = read_json("patient.json")
#source_data = read_json("source.json")
#t=process_pattern_new(source_data,patient_data)
#print(t)
#save_json("source_pattern.json", t )



def re_source(source_pattern):
    for key, patient_value in source_pattern.items():
        # 字段名已转化，所以可以直接匹配
        patient_values1 = split_medical_data_source(patient_value)
        source_pattern[key] = patient_values1
    return source_pattern



def jaccard_similarity(text1: str, text2: str) -> float:
    """计算两个文本的 Jaccard 相似度"""
    set1, set2 = set(text1), set(text2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union else 0

def overlap_similarity(str_a, str_b):
    """计算两个字符串的重叠度 = (公共字符数 / str_a 的总字符数)"""
    set_a=''.join(str_a)
    set_b=''.join(str_b)
    set_a = re.sub(r'[:\s]', '', set_a)
    set_b = re.sub(r'[:\s]', '', set_b)
    set_a = set(set_a)  # 字符串 A 的字符集合
    set_b = set(set_b)  # 字符串 B 的字符集合
    overlap_count = len(set_a & set_b)  # 计算重叠的字符数
    total_count = len(set_a)  # 计算字符串 A 的总字符数
    total_count1 = len(set_b)
    
    return overlap_count / total_count if total_count > 0 else 0  # 避免除零

def flatten_dict(d, parent_key="", transfer_format={}):
    """递归展平字典，并应用字段名转换"""
    items = {}
    for k, v in d.items():
        # 获取转换后的字段名
        new_key = transfer_format.get(k, k)  # 如果字段在转换规则中，使用转换后的名称；否则使用原字段名
        
        if isinstance(v, dict):
            # 如果是字典，递归展平
            items.update(flatten_dict(v, new_key, transfer_format))
        else:
            # 如果是值，直接存储
            items[new_key] = v
    return items

def find_best_matches(patient_data: dict, doctor_data: dict):
    """匹配 patient_data 和 doctor_data，去掉中间层级"""
    matches = {}

    # 预处理，去掉中间层级，直接展平字典并应用字段名转换
    flat_patient = flatten_dict(patient_data, transfer_format=inverted_transfer_format)
    flat_doctor = flatten_dict(doctor_data, transfer_format=inverted_transfer_format)

    for key, patient_value in flat_patient.items():
        # 字段名已转化，所以可以直接匹配
        if isinstance(patient_value, str) and key in flat_doctor:
            matches[f"病人-{key}"] = f"医生-{key}"  # 直接对应字段名称
        elif isinstance(patient_value, list) and key in flat_doctor:
            doctor_values = flat_doctor[key]
            if isinstance(doctor_values, str):
                doctor_values = doctor_values.split("\n")  # 确保转换为列表

            if not isinstance(doctor_values, list):
                continue  # 确保 doctor_values 是列表
            for i, pat_text in enumerate(patient_value):
                best_match = None
                highest_similarity = 0
                
                for j, doc_text in enumerate(doctor_values):
                    similarity = overlap_similarity(pat_text, doc_text)
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        best_match = j
                
                if best_match is not None:
                    matches[f"病人-{key}-{i}"] = f"医生-{key}-{best_match}"
    
    return matches



def find_best_matches_ceshi(patient_data: dict, doctor_data: dict):
    """匹配 patient_data 和 doctor_data，去掉中间层级"""
    matches = {}

    # 预处理，去掉中间层级，直接展平字典并应用字段名转换
    flat_patient = flatten_dict(patient_data, transfer_format=inverted_transfer_format)
    flat_doctor = flatten_dict(doctor_data, transfer_format=inverted_transfer_format)
    patient_data_new= copy.deepcopy(patient_data)
    doctor_data_new = copy.deepcopy(doctor_data)
    for key, patient_value in flat_patient.items():
        # 检查检查无信息判断
        if key == "住院期间医疗情况" and patient_value == ['无']:
            doctor_values1 = split_medical_data_doctor(doctor_values)
            doctor_data_new["住院期间医疗情况"] = doctor_values1
            patient_data_new["住院期间医疗情况"] = [["无"]]
            continue

        # 字段名已转化，所以可以直接匹配
        if isinstance(patient_value, str) and key in flat_doctor:
            matches[f"病人-{key}"] = f"医生-{key}"  # 直接对应字段名称
        elif isinstance(patient_value, list) and key in flat_doctor:
            doctor_values = flat_doctor[key]
            if isinstance(doctor_values, str):
                doctor_values = doctor_values.split("\n")  # 确保转换为列表
            if not isinstance(doctor_values, list):
                continue  # 确保 doctor_values 是列表
            doctor_values1 = split_medical_data_doctor(doctor_values)#修改原数组部分为二维数组
            patient_values1 = split_medical_data_patient(patient_value)
            doctor_data_new[key] = doctor_values1
            patient_data_new[key] = patient_values1
            #先匹配大段，在匹配大段中的每一元素
            in_doctor = []  # 记录已匹配的doctor
            for i, pat_text in enumerate(patient_values1):

                best_match = None
                highest_similarity = 0

                for j, doc_text in enumerate(doctor_values1):
                    similarity = overlap_similarity(pat_text, doc_text)
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        best_match = j

                for i1, pat_text1 in enumerate(pat_text):
                    best_match1 = None
                    highest_similarity1 = 0
                    for j1, doc_text1 in enumerate(doctor_values1[best_match]):

                        similarity1 = overlap_similarity(pat_text1, doc_text1)
                        if similarity1 > highest_similarity1:
                            highest_similarity1 = similarity1
                            best_match1 = j1
                   # if highest_similarity1 < 0.9:
                   #     best_match1 = 999999
                    #匹配指标性数据要求较高的相似度
                    if best_match is not None and best_match1 is not None:
                        if best_match == 0 and key == '住院期间医疗情况':
                            if highest_similarity1>=0.95:
                                matches[f"病人-{key}-{i}-{i1}"] = f"医生-{key}-{best_match}-{best_match1}"
                                in_doctor.append(doctor_values1[best_match][best_match1])
                            else:
                                matches[f"病人-{key}-{i}-{i1}"] = "patient_None"#未匹配的生成文本
                        else:
                            if highest_similarity1>=0.7:
                                matches[f"病人-{key}-{i}-{i1}"] = f"医生-{key}-{best_match}-{best_match1}"
                                in_doctor.append(doctor_values1[best_match][best_match1])
                            else:
                                matches[f"病人-{key}-{i}-{i1}"] = "patient_None"
                    #if highest_similarity1 >= 0.95:
                    #   print(patient_values1[i][i1],doctor_values1[best_match][best_match1])
            for j, doc_text in enumerate(doctor_values1):
                for j1, doc_text1 in enumerate(doc_text):
                    if doc_text1 not in in_doctor:
                        matches[f"医生-{key}-{j}-{j1}"] = "doctor_None"
                        #print(doctor_values1[j][j1])
    patient_data_new["患者基本信息"]["入院时简要病史"] = patient_data_new["入院时简要病史"]
    patient_data_new["患者基本信息"]["体检摘要"] = patient_data_new["体检摘要"]
    doctor_data_new["患者基本信息"]["入院时简要病史"] = doctor_data_new["入院时简要病史"]
    doctor_data_new["患者基本信息"]["体检摘要"] = doctor_data_new["体检摘要"]
    patient_data_new.pop("入院时简要病史")
    doctor_data_new.pop("体检摘要")
    return matches,patient_data_new,doctor_data_new

def find_jianyanjiancha(patient, source_pattern):
    patient_new = patient["住院期间医疗情况"]
    source = source_pattern["住院期间医疗情况"]

    patient2 = []
    for i, d in enumerate(patient_new):
        patient1 = []
        for j, x in enumerate(d):
            flag = False
            for i_source, d_source in enumerate(source):
                for j_source, x_source in enumerate(d_source):
                    if len(x) != 0:
                        if x[:-1] in x_source:
                            patient1.append(source[i_source][j_source])
                            flag = True
                            break
                    else:
                        flag = True
                if flag:
                    break
            if flag != True:
                if len(patient)!=0:
                    patient1.append(patient1[0])
        patient2.append(patient1)#重塑source——pattern
    source_pattern["住院期间医疗情况"] = patient2
    return source_pattern


# 辅助函数，用于将数字转换为中文序号
def to_chinese_numeral(n):
    """将整数转换为中文序号，如 1->一, 2->二, 11->十一。"""
    if not isinstance(n, int) or n < 1:
        return ""
    
    numerals = {
        1: '一', 2: '二', 3: '三', 4: '四',
        5: '五', 6: '六', 7: '七', 8: '八', 9: '九'
    }
    if n < 10: return numerals.get(n, '')
    s = str(n)
    if len(s) == 2:
        ten, one = int(s[0]), int(s[1])
        res = '十' if ten == 1 else numerals.get(ten, '') + '十'
        if one > 0: res += numerals.get(one, '')
        return res
    return str(n)

def parse_emr_to_dict(emr_text: str) -> dict:
    """
    【最终版 - 保证顺序】
    将分段的EMR文本解析为字典，智能处理重复标题，并严格保持原始顺序。

    - **特性1**: 如果文本中出现重复的标题，会自动为所有同名标题添加中文序号前缀
               (例如 "第一次手术记录", "第二次手术记录")。
    - **特性2**: 严格保持所有段落在原始文本中的出现顺序。
    - **特性3**: 忽略 "科室类别" 等特定标题。
    - **特性4**: 忽略内容为空（或只有'无'）的段落。

    Args:
        emr_text: 包含完整电子病历的字符串。

    Returns:
        一个有序字典 (OrderedDict)，键是经过处理后的唯一标题，值是该分段的完整内容。
    """
    pattern = re.compile(r'^###\s*(.+?)\s*:$', re.MULTILINE)
    matches = list(pattern.finditer(emr_text))

    if not matches:
        return OrderedDict()

    # --- 【核心修改】第一阶段：预扫描，统计所有标题的出现次数 ---
    title_total_counts = {}
    for match in matches:
        key = match.group(1).strip()
        if key == "科室类别":
            continue
        title_total_counts[key] = title_total_counts.get(key, 0) + 1

    # --- 第二阶段：生成字典，并根据预扫描结果进行重命名 ---
    emr_dict = OrderedDict()
    # 用于在生成时，追踪当前标题是第几次出现
    title_current_counts = {} 

    for i, match in enumerate(matches):
        original_key = match.group(1).strip()
        
        if original_key == "科室类别":
            continue

        # 更新当前标题的出现计数
        current_count = title_current_counts.get(original_key, 0) + 1
        title_current_counts[original_key] = current_count
        
        final_key = original_key
        # 检查这个标题是不是一个需要重命名的重复标题
        if title_total_counts.get(original_key, 0) > 1:
            # 如果是，就根据当前是第几次出现来添加序号
            final_key = f"第{to_chinese_numeral(current_count)}次{original_key}"

        # 确定内容范围 (逻辑不变)
        content_start_pos = match.end()
        content_end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(emr_text)
        value = emr_text[content_start_pos:content_end_pos].strip()

        # 只有在内容有效时才添加到字典
        if value and value.lower() != '无':
            emr_dict[final_key] = value
                
    # --- 特殊逻辑后处理 (保持不变) ---
    # 处理您之前提到的“最后一个在院评估单”这种情况
    # 因为我们现在有了序号，所以键名会是 "第N次在院评估单"
    # 我们需要一个更健壮的方式来处理
    keys_to_delete = []
    last_eval_key = None
    in_hospital_eval_key = None
    for k in emr_dict.keys():
        if "最后一个在院评估单" in k:
            last_eval_key = k
        if "在院评估单" in k and "最后一个" not in k:
            in_hospital_eval_key = k
    
    if last_eval_key and in_hospital_eval_key:
        if not emr_dict[last_eval_key].strip() and emr_dict[in_hospital_eval_key].strip():
            emr_dict[last_eval_key] = emr_dict[in_hospital_eval_key]
        keys_to_delete.append(in_hospital_eval_key)

    for k in keys_to_delete:
        if k in emr_dict:
            del emr_dict[k]

    return emr_dict