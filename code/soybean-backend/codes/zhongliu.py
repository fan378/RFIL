# medical_data_extraction.py
import json
import re
import os
import glob
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datetime import datetime
from codes.commons.utils2 import generate_qwen_response

# 全局变量初始化
menzhenbingli_content = ''
chuanci = ''
ct = ''
ultrasound_date = ''
zhusu = ''
zhengzhuang = ''
shiyanshi = ''
jiwangshi = ''
chubuzhenduan = ''
xizhen = ''
xianbingshi = ''
bingli = ''
shuhoubingli = ''

# 获取当前脚本文件(zhongliu.py)的绝对路径
# __file__ 是一个指向当前脚本的变量
current_file_path = os.path.abspath(__file__)

# 获取当前脚本所在的目录 (即 .../codes/ 目录)
current_dir = os.path.dirname(current_file_path)

# 将工作目录设置为当前目录的上一级目录 (即 .../soybean-backend/ 目录)
# '..' 在文件路径中代表“上一级目录”
WORKSPACE_DIR = os.path.dirname(current_dir)

# 切换工作目录
os.chdir(WORKSPACE_DIR)

# 全局模型变量，将由外部传入
model = None
tokenizer = None

# 患者数据加载函数
def load_patient_data(patient_id='zhangzhenwei'):
    global menzhenbingli_content
    
    try:
        file_path = f'Intermediate_process/zhongliu/{patient_id}.json'
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 检查数据结构并提取内容
        if isinstance(data, dict):
            possible_keys = ['content', 'text', 'menzhenbingli', '门诊病历', 'data']
            content = None
            
            for key in possible_keys:
                if key in data:
                    content = data[key]
                    break
            
            if content is None:
                for key, value in data.items():
                    if isinstance(value, str) and len(value) > 100:
                        content = value
                        break
                
                if content is None:
                    content = str(data)
                    
        elif isinstance(data, list):
            if data:
                if isinstance(data[0], str):
                    content = ' '.join(data)
                else:
                    content = str(data[0])
            else:
                content = "空列表"
        else:
            content = str(data)
        
        menzhenbingli_content = content.strip()
        return data

    except FileNotFoundError:
        menzhenbingli_content = "文件未找到"
        return None
    except json.JSONDecodeError as e:
        try:
            with open('门诊病历.json', 'r', encoding='utf-8') as f:
                menzhenbingli_content = f.read().strip()
                return json.loads(menzhenbingli_content)
        except:
            menzhenbingli_content = "读取失败"
            return None
    except Exception as e:
        menzhenbingli_content = "读取失败"
        return None

# 全局数据存储
patient_data = None

# 初始化函数
def initialize_patient_data(patient_id='zhangzhenwei'):
    global patient_data, menzhenbingli_content
    patient_data = load_patient_data(patient_id)
    if not patient_data:
        print(f"警告：无法加载患者 {patient_id} 的数据")

# 实验室检查结果提取函数
def extract_shiyanshi():
    global shiyanshi, menzhenbingli_content, patient_data, ultrasound_date
    
    if not patient_data:
        shiyanshi = "数据未加载"
        return shiyanshi, None
    
    data = patient_data
    
    # 查找超声报告
    ultrasound_reports = []
    
    for key, value in data.items():
        if '超声报告' in key:
            # 解析超声报告文本
            report_text = value
            report_info = {}
            
            # 提取检查日期
            date_match = re.search(r'检查日期：(\d{4}[./]\d{1,2}[./]\d{1,2})', report_text)
            if date_match:
                report_info['检查日期'] = date_match.group(1)
            
            # 提取超声提示
            hint_match = re.search(r'超声提示：(.+?)(?=\n|$)', report_text, re.DOTALL)
            if hint_match:
                report_info['超声提示'] = hint_match.group(1).strip()
            
            # 提取超声描述
            desc_match = re.search(r'超声描述：(.+?)(?=\n超声提示|$)', report_text, re.DOTALL)
            if desc_match:
                report_info['超声描述'] = desc_match.group(1).strip()
            
            report_info['_source_key'] = key
            report_info['_raw_text'] = report_text
            ultrasound_reports.append(report_info)
    
    if not ultrasound_reports:
            shiyanshi = "未找到超声报告"
            return shiyanshi, None
    
    # 按日期排序
    def parse_date(date_str):
        try:
            if '/' in date_str:
                return date_str.replace('/', '.')
            elif '.' in date_str:
                return date_str
            return date_str
        except:
            return "1900.01.01"
    
    reports_with_dates = []
    for report in ultrasound_reports:
        report_date = report.get('检查日期', "1900.01.01")
        parsed_date = parse_date(report_date)
        reports_with_dates.append((parsed_date, report))
    
    # 按日期排序（降序，最新的在前）
    reports_with_dates.sort(key=lambda x: x[0], reverse=True)
    
    # 获取最新日期
    latest_date = reports_with_dates[0][0]
    ultrasound_date = latest_date
    
    # 找出所有最新日期的报告
    latest_reports = []
    for date, report in reports_with_dates:
        if date == latest_date:
            latest_reports.append(report)
        else:
            break
    
    # 提取所有最新报告的超声提示内容
    ultrasound_hints = []
    
    for report in latest_reports:
        ultrasound_hint = report.get('超声提示', '')
        
        if ultrasound_hint:
            ultrasound_hints.append(ultrasound_hint)
        else:
            # 如果没有超声提示，尝试从超声描述中提取关键信息
            ultrasound_desc = report.get('超声描述', '')
            if ultrasound_desc:
                # 提取关键信息
                key_info = []
                if '甲状腺' in ultrasound_desc:
                    key_info.append('甲状腺相关')
                if '淋巴结' in ultrasound_desc:
                    key_info.append('淋巴结相关')
                if '结节' in ultrasound_desc:
                    key_info.append('结节相关')
                
                if key_info:
                    ultrasound_hints.append('、'.join(key_info))
    
    if ultrasound_hints:
        shiyanshi = '；'.join(ultrasound_hints)
    else:
        shiyanshi = "未找到超声提示内容"
    
    return shiyanshi, ultrasound_date

# 主诉提取函数
def extract_zhusu():
    global zhusu, menzhenbingli_content, patient_data
    
    if not patient_data:
        zhusu = "数据未加载"
        return zhusu
    
    data = patient_data
    
    # 查找门急诊病历
    outpatient_records = []
    
    for key, value in data.items():
        if '门急诊' in key or '门诊' in key:
            # 解析门急诊病历文本
            record_text = value
            record_info = {}
            
            # 提取记录日期
            date_match = re.search(r'记录日期：(\d{4}[./]\d{1,2}[./]\d{1,2})', record_text)
            if date_match:
                record_info['记录日期'] = date_match.group(1)
            
            # 提取主诉
            zhusu_match = re.search(r'主诉：(.+?)(?=\n|$)', record_text, re.DOTALL)
            if zhusu_match:
                record_info['主诉'] = zhusu_match.group(1).strip()
            
            # 提取病史描述
            desc_match = re.search(r'病史描述：(.+?)(?=\n体格检查|$)', record_text, re.DOTALL)
            if desc_match:
                record_info['病史描述'] = desc_match.group(1).strip()
            
            record_info['_raw_text'] = record_text
            outpatient_records.append(record_info)
    
    if not outpatient_records:
        zhusu = "未找到门急诊病历"
        return zhusu
    
    # 按日期排序
    def parse_datetime(datetime_str):
        try:
            if '.' in datetime_str:
                date_part = datetime_str.split(' ')[0]
                return date_part.replace('.', '')
            elif '/' in datetime_str:
                return datetime_str.replace('/', '')
            return datetime_str.replace('-', '').replace(' ', '').replace(':', '')
        except:
            return "19000101"
    
    outpatient_records.sort(key=lambda x: parse_datetime(x.get('记录日期', '1900.01.01')), reverse=True)
    
    # 获取最新的门急诊病历
    latest_record = outpatient_records[0]
    
    # 提取主诉内容
    chief_complaint = latest_record.get('主诉', '')
    
    if chief_complaint:
        original_zhusu = chief_complaint
    else:
        # 如果没有主诉，尝试从病史描述中提取
        medical_history = latest_record.get('病史描述', '')
        if medical_history:
            # 提取关键症状信息
            symptoms = []
            if '甲状腺' in medical_history:
                symptoms.append('甲状腺相关')
            if '淋巴结' in medical_history:
                symptoms.append('淋巴结相关')
            if '术后' in medical_history:
                symptoms.append('术后复查')
            
            if symptoms:
                original_zhusu = '，'.join(symptoms)
            else:
                original_zhusu = "未找到主诉内容"
        else:
            original_zhusu = "未找到主诉内容"
    
    # 检查主诉中是否包含"术后"
    if "术后" not in original_zhusu:
        # 计算当前时间减去最早门急诊病历的时间
        from datetime import datetime
        
        # 获取所有门急诊病历的日期
        all_dates = []
        for record in outpatient_records:
            record_date = record.get('记录日期', '')
            if record_date:
                try:
                    # 解析日期格式
                    if '.' in record_date:
                        date_str = record_date.split(' ')[0].replace('.', '-')
                    elif '/' in record_date:
                        date_str = record_date.replace('/', '-')
                    else:
                        date_str = record_date
                    
                    # 确保日期格式正确
                    if len(date_str.split('-')) == 3:
                        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                        all_dates.append(parsed_date)
                except:
                    continue
        
        if all_dates:
            # 找到最早的日期
            earliest_date = min(all_dates)
            current_date = datetime.now()
            
            # 计算时间差
            time_diff = current_date - earliest_date
            days_diff = time_diff.days
            
            if days_diff > 0:
                zhusu = f"发现{original_zhusu}{days_diff}天"
            else:
                zhusu = original_zhusu
        else:
            zhusu = original_zhusu
    else:
        zhusu = original_zhusu
    
    return zhusu

# 症状提取函数
def extract_zhengzhuang():
    global zhengzhuang, menzhenbingli_content
    
    # 简化的症状提取逻辑
    zhengzhuang = "无声音嘶哑、吞咽困难、多汗消瘦，无心悸发热等不适"
    return zhengzhuang

# 细针穿刺诊断提取函数
def extract_xizhen():
    global xizhen, chuanci, model, tokenizer
    
    # 检查chuanci内容的有效性
    if not chuanci or chuanci.strip() == "":
        xizhen = ""
        return xizhen
    
    # 构建提示词
    user_prompt = f"""请检查以下穿刺信息是否包含穿刺相关结果，如果不包含请只输出"否"，如果包含请只生成细针穿刺的结果，生成的结果请包含部位和诊断，如"左甲状腺乳头状癌"。不要分条，不要换行，不要输出任何其他内容

穿刺信息：{chuanci}

请只输出结果："""
    
    try:
        response = generate_qwen_response(model, tokenizer, user_prompt, max_new_tokens=50, temperature=0.01)
        xizhen = response.strip()
        
        # 清理结果 - 已注释掉，直接使用模型生成内容
        # if xizhen:
        #     # 去掉可能的标点符号
        #     xizhen = xizhen.strip('。，、')
        #     # 如果结果太长，只取第一句
        #     if '。' in xizhen:
        #         xizhen = xizhen.split('。')[0]
        #     if '，' in xizhen and len(xizhen.split('，')[0]) < 20:
        #         xizhen = xizhen.split('，')[0]
    except Exception as e:
        print(f"模型生成xizhen时出错: {e}")
        xizhen = "出错啦"
    
    return xizhen

# 既往史提取函数
def extract_jiwangshi():
    global jiwangshi, menzhenbingli_content
    
    # 简化的既往史提取逻辑
    jiwangshi = "疾病史：否认。传染病史：否认肝炎、结核、疟疾、血吸虫等传染病史。预防接种史：按计划预防接种。手术外伤史：否认。输血史：无。食物或药物过敏史：无"
    return jiwangshi

# 初步诊断提取函数
def extract_chubuzhenduan():
    global chubuzhenduan, xizhen, shiyanshi, zhusu, model, tokenizer
    
    # 如果xizhen不为空且内容不是"否"，直接复制xizhen的内容
    if xizhen and xizhen.strip() and xizhen.strip() != "否":
        chubuzhenduan = xizhen.strip()
        return chubuzhenduan
    
    # 如果不符合上述情况，使用shiyanshi内容让模型判断
    if shiyanshi and shiyanshi.strip() and shiyanshi != "未找到超声报告" and shiyanshi != "未找到超声提示内容":
        user_prompt = f"""请根据以下超声检查信息判断是否能得出甲状腺结节的结论，请只输出"是"或"否"。

超声检查信息：{shiyanshi}

请只输出"是"或"否"："""
        
        try:
            response = generate_qwen_response(model, tokenizer, user_prompt, max_new_tokens=10, temperature=0.01)
            result = response.strip()
            
            # 清理结果 - 已注释掉，直接使用模型生成内容
            # if result:
            #     result = result.strip('。，、').strip()
            #     if result in ["是", "否"]:
            #         if result == "是":
            #             chubuzhenduan = "甲状腺结节"
            #         else:
            #             chubuzhenduan = zhusu
            #     else:
            #         chubuzhenduan = zhusu
            # else:
            #     chubuzhenduan = zhusu
            
            # 直接使用模型生成的结果
            chubuzhenduan = result if result else zhusu
        except Exception as e:
            print(f"模型生成chubuzhenduan时出错: {e}")
            chubuzhenduan = zhusu
    else:
        chubuzhenduan = zhusu
    
    return chubuzhenduan

# 穿刺信息提取函数
def extract_cici():
    global chuanci, menzhenbingli_content, patient_data
    
    if not patient_data:
        chuanci = "数据未加载"
        return chuanci
    
    data = patient_data
    
    # 1. 优先提取病理报告中的穿刺报告（只提取穿刺相关的病理报告）
    pathology_puncture_info = []
    
    for key, value in data.items():
        if '病理' in key:
            # 解析病理报告文本
            report_text = value
            report_info = {}
            
            # 提取检查日期
            date_match = re.search(r'检查日期：(\d{4}[./]\d{1,2}[./]\d{1,2})', report_text)
            if date_match:
                report_info['检查日期'] = date_match.group(1)
            
            # 提取标本名称
            specimen_match = re.search(r'标本名称：(.+?)(?=\n|$)', report_text)
            if specimen_match:
                specimen_name = specimen_match.group(1).strip()
                # 只提取穿刺相关的标本（细针穿刺、穿刺活检等）
                if any(keyword in specimen_name for keyword in ['细针穿刺', '穿刺', '甲穿']):
                    # 提取病理诊断
                    diagnosis_match = re.search(r'病理诊断：(.+?)(?=\n报告医生|$)', report_text, re.DOTALL)
                    if diagnosis_match:
                        pathology_diagnosis = diagnosis_match.group(1).strip()
                        
                        puncture_info = {
                            '检查日期': report_info.get('检查日期', ''),
                            '标本名称': specimen_name,
                            '病理诊断': pathology_diagnosis
                        }
                        pathology_puncture_info.append(puncture_info)
    
    # 2. 按日期排序病理报告
    def parse_date(date_str):
        try:
            if '/' in date_str:
                return date_str.replace('/', '.')
            elif '.' in date_str:
                return date_str
            return date_str
        except:
            return "1900.01.01"
    
    pathology_puncture_info.sort(key=lambda x: parse_date(x.get('检查日期', '1900.01.01')))
    
    # 3. 提取门急诊病历的病史描述中的穿刺相关信息（只有在没有穿刺报告时才考虑）
    medical_history_puncture = []
    
    if not pathology_puncture_info:
        outpatient_records = []
        for key, value in data.items():
            if '门急诊' in key or '门诊' in key:
                # 解析门急诊病历文本
                record_text = value
                record_info = {}
                
                # 提取记录日期
                date_match = re.search(r'记录日期：(\d{4}[./]\d{1,2}[./]\d{1,2})', record_text)
                if date_match:
                    record_info['记录日期'] = date_match.group(1)
                
                # 提取病史描述
                desc_match = re.search(r'病史描述：(.+?)(?=\n体格检查|$)', record_text, re.DOTALL)
                if desc_match:
                    record_info['病史描述'] = desc_match.group(1).strip()
                
                record_info['_raw_text'] = record_text
                outpatient_records.append(record_info)
        
        if outpatient_records:
            def parse_datetime(datetime_str):
                try:
                    if '.' in datetime_str:
                        date_part = datetime_str.split(' ')[0]
                        return date_part.replace('.', '')
                    elif '/' in datetime_str:
                        return datetime_str.replace('/', '')
                    return datetime_str.replace('-', '').replace(' ', '').replace(':', '')
                except:
                    return "19000101"
            
            outpatient_records.sort(key=lambda x: parse_datetime(x.get('记录日期', '1900.01.01')), reverse=True)
            
            # 只提取病史描述中的穿刺相关信息
            for record in outpatient_records:
                medical_history = record.get('病史描述', '')
                record_date = record.get('记录日期', '')
                
                # 检查病史描述中是否包含穿刺相关信息
                if medical_history and ('穿刺' in medical_history or '甲穿' in medical_history or '细针' in medical_history):
                    # 提取只包含穿刺相关的内容
                    puncture_related_content = []
                    
                    # 按句号分割，查找包含穿刺关键词的句子
                    sentences = medical_history.split('。')
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if sentence and any(keyword in sentence for keyword in ['穿刺', '甲穿', '细针']):
                            # 进一步过滤，只保留真正与穿刺相关的内容
                            if any(keyword in sentence for keyword in ['穿刺', '甲穿', '细针', 'Bethesda', '乳头状癌', '髓样癌', 'MTC']):
                                # 过滤掉CT报告等非穿刺信息
                                if not any(keyword in sentence for keyword in ['CT', '右侧甲状腺下极结节', '两锁骨上增大淋巴结']):
                                    puncture_related_content.append(sentence)
                    
                    if puncture_related_content:
                        # 重新组合穿刺相关内容
                        filtered_content = '。'.join(puncture_related_content) + '。'
                        medical_history_puncture.append(f"病史描述（{record_date}）：{filtered_content}")
    
    # 4. 构建完整的穿刺信息
    all_puncture_info = []
    
    # 优先添加病理报告中的穿刺信息（只包含标本名称和病理诊断）
    for puncture in pathology_puncture_info:
        puncture_text = f"病理报告（{puncture['检查日期']}）：标本名称：{puncture['标本名称']}，病理诊断：{puncture['病理诊断']}"
        all_puncture_info.append(puncture_text)
    
    # 如果没有穿刺报告，再添加病史中的穿刺信息
    if not pathology_puncture_info and medical_history_puncture:
        all_puncture_info.extend(medical_history_puncture)
    
    # 合并所有信息
    if all_puncture_info:
        chuanci = "；".join(all_puncture_info)
    else:
        chuanci = "未找到穿刺相关信息"
    
    return chuanci

# CT检查提取函数
def extract_ct():
    global ct, patient_data
    
    if not patient_data:
        ct = ""
        return ct
    
    data = patient_data
    
    # 查找CT报告
    ct_reports = []
    
    for key, value in data.items():
        if 'CT' in key:
            # 解析CT报告文本
            report_text = value
            report_info = {}
            
            # 提取检查日期
            date_match = re.search(r'检查日期：(\d{4}[./]\d{1,2}[./]\d{1,2})', report_text)
            if date_match:
                report_info['检查日期'] = date_match.group(1)
            
            # 提取检查印象
            impression_match = re.search(r'检查印象：(.+?)(?=\n报告医生|$)', report_text, re.DOTALL)
            if impression_match:
                report_info['检查印象'] = impression_match.group(1).strip()
            
            # 提取检查所见
            finding_match = re.search(r'检查所见：(.+?)(?=\n检查印象|$)', report_text, re.DOTALL)
            if finding_match:
                report_info['检查所见'] = finding_match.group(1).strip()
            
            report_info['_raw_text'] = report_text
            ct_reports.append(report_info)
    
    if not ct_reports:
        ct = ""
        return ct
    
    # 按日期排序
    def parse_date(date_str):
        try:
            if '/' in date_str:
                return date_str.replace('/', '.')
            elif '.' in date_str:
                return date_str
            return date_str
        except:
            return "1900.01.01"
    
    reports_with_dates = []
    for report in ct_reports:
        report_date = report.get('检查日期', "1900.01.01")
        reports_with_dates.append((parse_date(report_date), report))
    
    reports_with_dates.sort(key=lambda x: x[0], reverse=True)
    ct_reports = [report for _, report in reports_with_dates]
    
    # 获取最新的CT报告
    latest_report = ct_reports[0]
    
    # 提取检查印象内容
    ct_impression = latest_report.get('检查印象', '')
    
    if ct_impression:
        ct = ct_impression
    else:
        # 如果没有检查印象，尝试从检查所见中提取关键信息
        ct_finding = latest_report.get('检查所见', '')
        if ct_finding:
            # 提取关键信息
            key_info = []
            if '甲状腺' in ct_finding:
                key_info.append('甲状腺相关')
            if '淋巴结' in ct_finding:
                key_info.append('淋巴结相关')
            if '术后' in ct_finding:
                key_info.append('术后改变')
            
            if key_info:
                ct = '，'.join(key_info)
            else:
                ct = ""
        else:
            ct = ""
    
    return ct

# 病理报告提取函数
def extract_bingli():
    global bingli, patient_data
    
    if not patient_data:
        bingli = ""
        return bingli
    
    data = patient_data
    
    # 查找病理报告（除了穿刺相关的）
    pathology_reports = []
    
    for key, value in data.items():
        if '病理' in key:
            # 解析病理报告文本
            report_text = value
            report_info = {}
            
            # 提取检查日期
            date_match = re.search(r'检查日期：(\d{4}[./]\d{1,2}[./]\d{1,2})', report_text)
            if date_match:
                report_info['检查日期'] = date_match.group(1)
            
            # 提取标本名称
            specimen_match = re.search(r'标本名称：(.+?)(?=\n|$)', report_text)
            if specimen_match:
                specimen_name = specimen_match.group(1).strip()
                # 排除穿刺相关的标本（细针穿刺、穿刺活检等）
                if not any(keyword in specimen_name for keyword in ['细针穿刺', '穿刺', '甲穿']):
                    # 提取病理诊断
                    diagnosis_match = re.search(r'病理诊断：(.+?)(?=\n报告医生|$)', report_text, re.DOTALL)
                    if diagnosis_match:
                        pathology_diagnosis = diagnosis_match.group(1).strip()
                        
                        pathology_info = {
                            '检查日期': report_info.get('检查日期', ''),
                            '标本名称': specimen_name,
                            '病理诊断': pathology_diagnosis
                        }
                        pathology_reports.append(pathology_info)
    
    # 按日期排序病理报告
    def parse_date(date_str):
        try:
            if '/' in date_str:
                return date_str.replace('/', '.')
            elif '.' in date_str:
                return date_str
            return date_str
        except:
            return "1900.01.01"
    
    pathology_reports.sort(key=lambda x: parse_date(x.get('检查日期', '1900.01.01')))
    
    # 构建病理报告信息
    pathology_info_list = []
    
    for pathology in pathology_reports:
        pathology_text = f"病理报告（{pathology['检查日期']}）：标本名称：{pathology['标本名称']}，病理诊断：{pathology['病理诊断']}"
        pathology_info_list.append(pathology_text)
    
    # 合并所有信息
    if pathology_info_list:
        bingli = "；".join(pathology_info_list)
    else:
        bingli = ""
    
    return bingli

# 术后病理提取函数
def extract_shuhoubingli():
    global shuhoubingli, zhusu, bingli, model, tokenizer
    
    # 检查主诉是否包含"术后"且病理报告不为空
    if '术后' not in zhusu or not bingli or not bingli.strip():
        shuhoubingli = ''
        return shuhoubingli
    
    # 构建提示词
    user_prompt = f"""请根据以下病理报告内容，分析并输出：

1. 是否有腺瘤或癌症（如有请输出具体类型）不要输出是和否，直接输出结果，如果不存在请忽略
2. 甲状腺相关的诊断信息
3. 淋巴结相关的诊断信息

请整理成一段话，不要分条，不要输出任何其他内容

病理报告内容：{bingli}

请直接输出分析结果："""
    
    try:
        response = generate_qwen_response(model, tokenizer, user_prompt, max_new_tokens=200, temperature=0.01)
        shuhoubingli = response.strip()
        
        # 清理结果 - 已注释掉，直接使用模型生成内容
        # if shuhoubingli:
        #     # 去掉可能的标点符号
        #     shuhoubingli = shuhoubingli.strip('。，、')
    except Exception as e:
        print(f"模型生成shuhoubingli时出错: {e}")
        shuhoubingli = ''
    
    return shuhoubingli

# 主执行函数
def run_all_extractions(patient_id='wangnannan', external_model=None, external_tokenizer=None):
    global zhusu, zhengzhuang, shiyanshi, ultrasound_date, jiwangshi, chubuzhenduan, chuanci, xizhen, ct, xianbingshi, bingli, shuhoubingli, model, tokenizer
    
    # 验证模型和分词器是否传入
    if external_model is None or external_tokenizer is None:
        raise ValueError("模型和 tokenizer 必须传入")
    
    # 设置全局模型和分词器
    model = external_model
    tokenizer = external_tokenizer
    
    # 初始化患者数据
    initialize_patient_data(patient_id)
    
    # 执行所有提取函数
    zhusu = extract_zhusu()
    zhengzhuang = extract_zhengzhuang()
    shiyanshi, ultrasound_date = extract_shiyanshi()
    jiwangshi = extract_jiwangshi()
    chuanci = extract_cici()
    xizhen = extract_xizhen()
    chubuzhenduan = extract_chubuzhenduan()
    ct = extract_ct()
    bingli = extract_bingli()
    
    # 新增术后病理提取
    shuhoubingli = extract_shuhoubingli()
    
    # 创建现病史变量 - 拼接方式
    xianbingshi = f"患者{zhusu}，病程中无声音嘶哑、吞咽困难、多汗消瘦，无心悸发热等不适遂至我院就诊。查超声示：{shiyanshi}，CT显示{ct}，细针穿刺示:{xizhen}。现为进一步治疗入院。"
    
    # 输出所有结果
    print("="*60)
    print("医疗信息提取结果")
    print("="*60)
    print(f"主诉: {zhusu}")
    print(f"症状: {zhengzhuang}")
    print(f"超声检查: {shiyanshi}")
    print(f"超声检查日期: {ultrasound_date or '无'}")
    print(f"既往史: {jiwangshi}")
    print(f"初步诊断: {chubuzhenduan}")
    print(f"穿刺信息: {chuanci}")
    print(f"细针穿刺诊断: {xizhen}")
    print(f"CT检查: {ct or '无'}")
    print(f"病理报告: {bingli or '无'}")
    print(f"术后病理: {shuhoubingli or '无'}")
    print(f"现病史: {xianbingshi}")
    print("="*60)
    
    # 返回结果字典
    return {
        'zhusu': zhusu,
        'zhengzhuang': zhengzhuang,
        'shiyanshi': shiyanshi,
        'ultrasound_date': ultrasound_date,
        'jiwangshi': jiwangshi,
        'chubuzhenduan': chubuzhenduan,
        'chuanci': chuanci,
        'xizhen': xizhen,
        'ct': ct,
        'bingli': bingli,
        'shuhoubingli': shuhoubingli,
        'xianbingshi': xianbingshi
    }
def split_text_to_dict(text):
    # 定义关键字及其对应的字典键名
    keyword_mapping = {
        "术后病理": "术后病理",
        "查超声示": "查超声示",
        "颈部CT提示": "颈部CT提示",
        "行细针穿刺示": "行细针穿刺示",
        "现为进一步治疗入院": "结尾"
    }

    # 初始化字典和位置列表
    result_dict = {}
    positions = []

    # 查找所有关键字在文本中的位置
    for keyword in keyword_mapping.keys():
        idx = text.find(keyword)
        if idx != -1:
            positions.append((idx, keyword))

    # 如果没有找到任何关键字，返回整个文本作为"zhushu"
    if not positions:
        return {"主诉": text}

    # 按位置排序
    positions.sort(key=lambda x: x[0])

    # 处理第一部分（主诉）
    first_keyword_pos, first_keyword = positions[0]
    if first_keyword_pos > 0:
        zhushu_text = text[:first_keyword_pos].strip()
        # 删除主诉中第一个逗号之后的内容
        comma_index = zhushu_text.find("，")
        if comma_index != -1:
            zhushu_text = zhushu_text[:comma_index]
        result_dict["主诉"] = zhushu_text

    # 处理中间部分
    for i in range(len(positions)):
        start_idx, keyword = positions[i]

        # 确定当前部分的结束位置
        if i < len(positions) - 1:
            end_idx = positions[i + 1][0]
        else:
            end_idx = len(text)

        # 提取当前部分内容
        segment = text[start_idx:end_idx].strip()

        # 分配键名
        key_name = keyword_mapping[keyword]
        result_dict[key_name] = segment

    # 清理每个value中的关键字文本
    for key in result_dict:
        if key == "主诉":
            # 已经处理过，跳过
            continue

        # 获取原始关键字文本（从keyword_mapping反向查找）
        original_keyword = None
        for k, v in keyword_mapping.items():
            if v == key:
                original_keyword = k
                break

        if original_keyword:
            # 对于"结尾"部分，保留完整文本
            if key == "结尾":
                # 只删除可能跟随的冒号
                cleaned_value = result_dict[key]
                if cleaned_value.startswith(("：", ":")):
                    cleaned_value = cleaned_value[1:]
                result_dict[key] = cleaned_value.strip()
            else:
                # 其他部分：删除关键字文本
                cleaned_value = result_dict[key].replace(original_keyword, "")
                # 删除可能跟随的冒号（全角或半角）
                if cleaned_value.startswith(("：", ":")):
                    cleaned_value = cleaned_value[1:]
                # 删除首尾空白
                result_dict[key] = cleaned_value.strip()

    return result_dict


# 批量处理函数已移除，只处理新保存的数据

# 主程序入口
if __name__ == '__main__':
    # 注意：直接运行此文件需要先加载模型和分词器
    print("注意：此文件需要外部传入模型和分词器才能运行")
    print("请通过 view.py 或其他方式调用 run_all_extractions 函数")
    
    # 示例：如果需要测试，请先加载模型
    # from transformers import AutoTokenizer, AutoModelForCausalLM
    # model_path = '/path/to/your/model'
    # tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    # model = AutoModelForCausalLM.from_pretrained(model_path, device_map="cuda:0", torch_dtype=torch.bfloat16, trust_remote_code=True)
    # result = run_all_extractions('wangnannan', model, tokenizer)