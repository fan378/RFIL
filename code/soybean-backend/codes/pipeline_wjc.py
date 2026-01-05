# 全部由模型生成
import os
import sys
import shutil
import numpy as np
from transformers import AutoTokenizer,AutoModelForCausalLM, AutoModel
from codes.commons.utils2 import generate_qwen_response, chat_with_api
import torch
import jsonlines
import json
import re
import uuid
from typing import List, Dict, Any
from datetime import datetime, timedelta
os.environ['CUDA_LAUNCH_BLOCKING'] = '6'

# 混合模式的“总结策略库”，同时使用摘要和原文
SUMMARY_STRATEGIES_HYBRID = {
    "患者基本信息": {
        "description": "生成JSON格式的患者信息。",
        "prompt_template": (
            "[原始病历全文]\n"
            "----------------\n"
            "{original_text}\n"
            "----------------\n\n"
            "[关键信息摘要]\n"
            "----------------\n"
            "{summary_text}\n"
            "----------------\n\n"
            "任务：请参考“关键信息摘要”和“原始病历全文”来抽取各字段信息，完成“患者基本信息”中[\"住院号\", \"床号\", \"入院时间\", \"出院时间\", \"科别\", \"科室\", \"姓名\", \"年龄\", \"性别\", \"低压(BP低)\", \"高压(BP高)\", \"脉搏(P)\", \"呼吸(R)\", \"体温(T)\", \"入院诊断\", \"入院时简要病史\", \"体检摘要\"]字段的填写。\n"
            "**输出指南：**\n{user_guidance}\n\n"
            "**核心格式要求 (必须遵守):**\n"
            "1.  最终输出**必须**是一个标准的、可以直接解析的JSON对象。\n"
            "2.  JSON对象**必须**包含以下所有字段：[\"住院号\", \"床号\", \"入院时间\", \"出院时间\", \"科别\", \"科室\", \"姓名\", \"年龄\", \"性别\", \"低压(BP低)\", \"高压(BP高)\", \"脉搏(P)\", \"呼吸(R)\", \"体温(T)\", \"入院诊断\", \"入院时简要病史\", \"体检摘要\"]。\n"
            "3.  对于找不到信息的字段，其值应为空字符串 `\"\"`。\n"
            "4.  **禁止**在最终输出中包含任何解释或Markdown代码块标记。"
        ),
    },
    "出院诊断": {
        "description": "生成结构化的出院诊断列表，并参考原文进行核实。",
        "prompt_template": (
            "[原始病历全文]\n"
            "----------------\n"
            "{original_text}\n"
            "----------------\n\n"
            "[关键信息摘要]\n"
            "----------------\n"
            "{summary_text}\n"
            "----------------\n\n"
            "任务：请以“关键信息摘要”为骨架，并参考“原始病历全文”来补充细节，确定患者“出院诊断”信息。\n"
            "**输出指南：**\n{user_guidance}\n\n"
            "**核心格式要求 (必须遵守):**\n"
            "1.  **必须**以纯文本格式直接输出诊断结论。\n"
            "2.  **绝对禁止**使用任何Markdown格式（如加粗、斜体、标题等）。\n"
            "**核心输出要求 (必须遵守):**\n"
            "请严格基于给定信息事实，不得出现“原始病历全文”以外的信息。"
        )
    },
    "病程与治疗情况": {
        "description": "将关键信息融合成一段连贯的病程描述，并用原文补充细节。",
        "prompt_template": (
            "[原始病历全文]\n"
            "----------------\n"
            "{original_text}\n"
            "----------------\n\n"
            "[关键信息摘要]\n"
            "----------------\n"
            "{summary_text}\n"
            "----------------\n\n"
            "任务：请以“关键信息摘要”为骨架，并参考“原始病历全文”来补充细节，输出“病程与治疗情况”信息。\n"
            "**输出指南：**\n{user_guidance}\n\n"
            "**核心格式要求 (必须遵守):**\n"
            "1.  **必须**将所有内容融合成一段连贯的文本。\n"
            "2.  **绝对禁止**使用列表、项目符号或任何Markdown格式。\n"
            "**核心输出要求 (必须遵守):**\n"
            "请严格基于给定信息事实，不得出现“原始病历全文”以外的信息。"
        )
    },
    "出院时情况": {
        "description": "总结患者出院时的身体状况，并用原文补充客观指标。",
        "prompt_template": (
            "[原始病历全文]\n"
            "----------------\n"
            "{original_text}\n"
            "----------------\n\n"
            "[关键信息摘要]\n"
            "----------------\n"
            "{summary_text}\n"
            "----------------\n\n"
            "任务：请客观地描述患者的出院状态。请基于“关键信息摘要”中的要点，撰写“出院时情况”字段。\n"
            "**输出指南：**\n{user_guidance}\n\n"
            "**核心格式要求 (必须遵守):**\n"
            "1.  **必须**以一行文本格式输出，无需任何形式的标题。\n"
            "**核心输出要求 (必须遵守):**\n"
            "请严格基于给定信息事实，不得出现“原始病历全文”以外的信息。"
        )
    },
    "出院后用药建议": {
        "description": "生成关于出院后用药和随访的建议，并参考原文核实细节。",
        "prompt_template": (
            "[原始病历全文]\n"
            "----------------\n"
            "{original_text}\n"
            "----------------\n\n"
            "[关键信息摘要]\n"
            "----------------\n"
            "{summary_text}\n"
            "----------------\n\n"
            "任务：请生成清晰、完整的患者出院医嘱。请以“关键信息摘要”为骨架，并参考“原始病历全文”来补充细节，输出“出院后用药建议”信息。\n"
            "**输出指南：**\n{user_guidance}\n\n"
            "**核心格式要求 (必须遵守):**\n"
            "1.  **必须**使用有序列表（1、, 2、, 3、 ...）组织输出。\n" 
            "2.  每一项都**必须**是完整的、直接的陈述句结论。\n"
            "3.  **绝对禁止**为每一项添加任何形式的加粗小标题或使用Markdown格式。\n"
        )
    },
    "default": {
        "description": "进行通用的信息总结。",
        "prompt_template": (
            "[原始病历全文]\n"
            "----------------\n"
            "{original_text}\n"
            "----------------\n\n"
            "[关键信息摘要]\n"
            "----------------\n"
            "{summary_text}\n"
            "----------------\n\n"
            "请基于以下“关键信息摘要”，并参考“原始病历全文”，生成一份相关的总结。"
        )
    }
}

def parse_test_items(details_text: str) -> List[Dict[str, str]]:
    """
    【全新增强版】解析具体的检验项目，处理所有已知复杂格式。
    - 兼容 "值,评估" 格式 (e.g., "25.0, 偏高")
    - 兼容 "只有评估" 格式 (e.g., "阴性", "正常")
    - 兼容 "评估(干扰项)值" 格式 (e.g., "阴性(-)", "阳性(+)383.10")
    - 兼容 "只有值和单位" 格式 (e.g., "6.5%")
    - 兼容 非数值型值 (e.g., "O", "+", "未见")
    - 兼容 特殊字符 (e.g., "::", "*", "^")
    """
    items = []
    # 统一分隔符，并处理可能由 `::` 产生的额外冒号
    details_text = details_text.replace('::', ':')
    item_parts = [part.strip() for part in re.split('[;；]', details_text) if part.strip()]

    # 定义评估关键词集合，用于快速查找
    EVALUATION_KEYWORDS = {'正常', '偏高', '偏低', '阳性', '阴性', '弱阳性'}

    for part in item_parts:
        if ':' not in part:
            continue
        
        name, rest_of_part = part.split(':', 1)
        name = name.strip()
        rest_of_part = rest_of_part.strip()

        item = {
            'name': name,
            'value': '',
            'unit': '',
            'evaluation': '',
            'value_unit': rest_of_part  # 原始的冒号后内容
        }
        
        value_unit_to_parse = rest_of_part
        evaluation_found = False

        # --- 策略1: 优先匹配最明确的 "值, 评估" 格式 ---
        if ',' in rest_of_part:
            possible_vu, possible_eval = rest_of_part.rsplit(',', 1)
            if possible_eval.strip() in EVALUATION_KEYWORDS:
                item['evaluation'] = possible_eval.strip()
                value_unit_to_parse = possible_vu.strip()
                evaluation_found = True

        # --- 策略2: 如果不符合策略1，再检查是否以评估词开头或完全是评估词 ---
        if not evaluation_found:
            # 清理字符串以便于匹配，例如 "阴性(-)" -> "阴性"
            temp_check_str = re.sub(r'[\(（].*?[\)）]', '', rest_of_part).strip()
            for keyword in EVALUATION_KEYWORDS:
                if temp_check_str.startswith(keyword):
                    item['evaluation'] = keyword
                    # 从原始字符串（保留括号等信息）中剥离关键词部分，剩下的是值和单位
                    # 这里使用原始的rest_of_part来计算，防止误删
                    remaining_part = rest_of_part[len(keyword):].strip()
                    # 清理开头可能存在的括号等干扰项
                    value_unit_to_parse = re.sub(r'^\s*[\(（].*?[\)）]\s*', '', remaining_part).strip()
                    break

        # --- 核心解析：分离数值和单位 ---
        if value_unit_to_parse:
            # 增强的正则表达式，以匹配科学计数法、特殊字符等
            # 匹配模式: (数值部分) (单位部分)
            # 数值部分可以包含: < > 数字 . - * ^ / 和 (+)
            # 单位部分是剩余的所有内容
            value_match = re.match(r'^([<>\d.\-*×\^/]+(?:\s*\([\+\-]\))?)\s*(.*)', value_unit_to_parse)

            if value_match:
                item['value'] = value_match.group(1).strip()
                item['unit'] = value_match.group(2).strip()
            else:
                # 如果正则不匹配（例如值是 "O", "+", "未见" 等非数值），则将整个部分视为值
                item['value'] = value_unit_to_parse
                item['unit'] = ''
        
        # 对于那种只有评估词的情况 (e.g., "尿蛋白:阴性")
        # 此时 value_unit_to_parse 会变为空字符串, item['value'] 也为空
        # 我们将评估结果本身赋给 value，使其不为空
        if not item['value'] and item['evaluation']:
            item['value'] = item['evaluation']

        items.append(item)

    return items

def parse_examinations(exam_text: str) -> List[Dict[str, str]]:
    """解析检查信息"""
    examinations = []
    # 按空行分割不同的检查记录
    exam_blocks = re.split(r'\n\s*\n', exam_text.strip())

    for block in exam_blocks:
        if not block.strip():
            continue

        exam = {}
        lines = block.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('报告时间:'):
                exam['report_time'] = line.replace('报告时间:', '').strip()
            elif line.startswith('描述:'):
                exam['description'] = line.replace('描述:', '').strip()
            elif line.startswith('图像所见:'):
                exam['image_findings'] = line.replace('图像所见:', '').strip()
            elif line.startswith('图像分析:'):
                exam['image_analysis'] = line.replace('图像分析:', '').strip()

        # 只有当exam不为空 且 必须包含'report_time'时才添加
        if exam and 'report_time' in exam:
            examinations.append(exam)

    return examinations

def parse_lab_tests(lab_text: str) -> List[Dict[str, Any]]:
    """解析检验信息"""
    lab_tests = []
    lines = lab_text.strip().split('\n')

    for line in lines:
        if not line.strip():
            continue

        # 更灵活的匹配，处理多个空格和tab字符
        # 先分割报告时间部分
        if '报告时间:' in line and '检验详情:' in line:
            parts = line.split('检验详情:', 1)
            if len(parts) == 2:
                time_part = parts[0].replace('报告时间:', '').strip()
                details_text = parts[1].strip()

                # 解析检验详情
                test_items = parse_test_items(details_text)

                lab_test = {
                    'report_time': time_part,
                    'test_items': test_items,
                    'raw_details': details_text
                }

                lab_tests.append(lab_test)

    return lab_tests

def extract_medical_data(data_text: str, file_path: str) -> tuple:
    """
    从固定格式的医疗数据中抽取检查信息和检验信息
    """
    examinations = []
    lab_tests = []

    # 抽取全部检查信息
    exam_section = re.search(r'###全部检查:\s*\n(.*?)(?=###|$)', data_text, re.DOTALL)
    if exam_section:
        exam_text = exam_section.group(1)
        examinations = parse_examinations(exam_text)
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                exam_text = json.load(f)["住院期间医疗情况"]["全部检查"]
            examinations = parse_examinations(exam_text)
        except:
            print("无检查数据")


    # 抽取简化过滤检验信息
    lab_section = re.search(r'###简化过滤检验:\s*\n(.*?)(?=###|$)', data_text, re.DOTALL)
    if lab_section:
        lab_text = lab_section.group(1)
        lab_tests = parse_lab_tests(lab_text)
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lab_text = json.load(f)["住院期间医疗情况"]["简化过滤检验"]
            lab_tests = parse_lab_tests(lab_text)
        except:
            print("无检验数据")

    return examinations, lab_tests

def process_medical_data_by_config(
    examinations: List[Dict[str, Any]], 
    lab_tests: List[Dict[str, Any]], 
    config: Dict[str, Any]
    ) -> str:
    """
    根据一个结构化的配置对象，对传入的检查和检验数据进行筛选、过滤和格式化。

    该函数的核心流程是：
    1. 根据配置，对检验和检查数据分别进行内容筛选（如关键词、状态）。
    2. 对筛选后的结果再进行时间维度的过滤（如最新、最早、日期范围）。
    3. 将最终结果格式化为统一的字符串输出。

    Args:
        examinations (List[Dict]): 经过解析的检查信息列表。
        lab_tests (List[Dict]): 经过解析的检验信息列表。
        config (Dict): 一个包含所有处理指令的配置字典。

    Returns:
        str: 经过处理和格式化后的最终字符串。如果没有符合条件的数据，则返回 "无"。
    """

    # --- 1. 内部帮助函数 (Helper Functions) ---
    # 这些函数封装了单一、具体的功能，使得主流程更清晰。

    def _filter_by_time(data: list, time_config: dict) -> list:
        """
        通用的时间过滤器，根据提供的时间配置对数据列表进行筛选。
        
        Args:
            data (list): 待筛选的数据列表，每个元素都应有 'report_time' 键。
            time_config (dict): 时间配置，如 {"type": "latest"} 或 {"type": "date_range", ...}。

        Returns:
            list: 经过时间筛选后的数据列表。
        """
        # 如果没有数据、没有时间配置或配置为"all"，则直接返回原始数据
        if not data or not time_config or time_config.get("type") == "all":
            return data
        
        # 为每条记录添加一个临时的 datetime 对象 '_dt' 以便排序和比较
        for item in data:
            try:
                item['_dt'] = datetime.strptime(item['report_time'], '%Y-%m-%d %H:%M:%S')
            except (ValueError, KeyError):
                # 如果时间格式错误或缺少 'report_time' 键，则标记为None
                item['_dt'] = None 
        
        # 只处理那些具有有效时间的记录
        valid_data = [item for item in data if item['_dt']]
        if not valid_data:
            return []

        filter_type = time_config.get("type")

        # 返回时间最晚的一条记录
        if filter_type == "latest":
            return [max(valid_data, key=lambda x: x['_dt'])]
        
        # 返回时间最早的一条记录
        if filter_type == "earliest":
            return [min(valid_data, key=lambda x: x['_dt'])]
        
        # 返回最近N天内的记录（基于数据中最新的时间点）
        if filter_type == "recent_days":
            days = int(time_config.get("days", 7))
            latest_time_in_data = max(item['_dt'] for item in valid_data)
            cutoff_date = latest_time_in_data - timedelta(days=days)
            return [item for item in valid_data if item['_dt'] >= cutoff_date]
        
        # 返回指定日期范围内的记录
        if filter_type == "date_range":
            start_date_str = time_config.get("start_date")
            end_date_str = time_config.get("end_date")
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
            # 结束日期包含当天，所以时间设为 23:59:59
            end_date = datetime.strptime(end_date_str + " 23:59:59", '%Y-%m-%d %H:%M:%S') if end_date_str else None
            return [item for item in valid_data if (not start_date or item['_dt'] >= start_date) and (not end_date or item['_dt'] <= end_date)]
        
        return valid_data

    def _filter_lab_tests(reports: list, filter_config: dict) -> list:
        """
        根据关键词和状态（正常/异常）筛选检验项目。
        重要：此函数会保留报告的结构，但只包含其中匹配的检验项目。
        
        Args:
            reports (list): 检验报告列表。
            filter_config (dict): 检验筛选配置，如 {"keywords": ["血小板"], "status": "abnormal"}。

        Returns:
            list: 筛选后的检验报告列表，如果一个报告中所有项目都不匹配，则该报告被移除。
        """
        status_filter = filter_config.get("status", "all")
        keywords_filter = [kw.casefold() for kw in filter_config.get("keywords", [])] # 关键词转为小写以实现不区分大小写匹配
        
        filtered_reports = []
        abnormal_evals = {"偏高", "偏低", "阳性"} # 定义哪些评估属于 "异常"

        # 遍历每一份检验报告
        for report in reports:
            matching_items = []
            # 遍历报告中的每一个检验项目
            for item in report.get('test_items', []):
                evaluation = item.get('evaluation', '')
                # 检查状态是否匹配 (all, abnormal, normal, high, low)
                status_match = (status_filter == "all" or 
                                (status_filter == "abnormal" and evaluation in abnormal_evals) or 
                                (status_filter == "normal" and evaluation not in abnormal_evals) or 
                                (status_filter == "high" and evaluation == "偏高") or 
                                (status_filter == "low" and evaluation == "偏低"))
                if not status_match:
                    continue
                
                # 检查关键词是否匹配
                item_name_lower = item.get('name', '').casefold()
                keyword_match = (not keywords_filter or any(kw in item_name_lower for kw in keywords_filter))
                if not keyword_match:
                    continue
                
                # 如果状态和关键词都匹配，则保留此项目
                matching_items.append(item)
            
            # 如果该报告中有任何匹配的项目，则创建一个新的报告副本，只包含这些匹配项
            if matching_items:
                new_report = report.copy()
                new_report['test_items'] = matching_items
                filtered_reports.append(new_report)
                
        return filtered_reports

    def _filter_examinations(exams: list, filter_config: dict) -> list:
        """
        根据关键词筛选检查报告。
        
        Args:
            exams (list): 检查报告列表。
            filter_config (dict): 检查筛选配置, 如 {"keywords": ["CT", "结节"]}。

        Returns:
            list: 筛选后的检查报告列表。
        """
        keywords = [kw.casefold() for kw in filter_config.get("keywords", [])]
        if not keywords:
            return exams
        
        # 如果检查的'description'字段包含任何一个关键词，则保留该检查报告
        return [exam for exam in exams if any(kw in exam.get('description', '').casefold() for kw in keywords)]

    def _format_lab_output(lab_results: list, output_config: dict) -> str:
        """
        将筛选后的检验数据格式化为最终的字符串。
        
        Args:
            lab_results (list): 待格式化的检验报告列表。
            output_config (dict): 输出格式配置，如 {"include_time": True, "time_sort_order": "desc"}。

        Returns:
            str: 格式化后的字符串。
        """
        include_time = output_config.get("include_time", True)
        sort_order = output_config.get("time_sort_order", "asc")
        output_parts = []

        for report in lab_results:
            time_str = report['report_time']
            item_strs = []
            for item in report.get('test_items', []):
                # 将 "偏高", "偏低" 等评估结果映射为直观的符号
                eval_map = {"偏高": "↑", "偏低": "↓", "阳性": "阳性"}
                symbol = eval_map.get(item.get('evaluation', ''), '')
                value_unit_str = item.get('value_unit', '').strip()
                item_strs.append(f"{item['name']}:{value_unit_str}{symbol}")
            
            if item_strs:
                # 根据配置决定是否在输出中包含报告时间
                if include_time:
                    output_parts.append(f"{time_str};{';'.join(item_strs)};")
                else:
                    # 如果不包含时间，则直接将各项结果拼接
                    output_parts.extend([s + ';' for s in item_strs])
        
        # 如果包含时间，则按指定顺序对整个报告进行排序
        if include_time:
            output_parts.sort(reverse=(sort_order == "desc"))
            
        return "".join(output_parts)

    def _format_exam_output(exam_results: list, output_config: dict) -> str:
        """
        将筛选后的检查数据格式化为最终的字符串。
        
        Args:
            exam_results (list): 待格式化的检查报告列表。
            output_config (dict): 输出格式配置。

        Returns:
            str: 格式化后的字符串。
        """
        include_time = output_config.get("include_time", True)
        sort_order = output_config.get("time_sort_order", "asc")
        output_parts = []

        for exam in exam_results:
            # 使用 .get() 安全地访问键，防止因数据不完整（如缺少'report_time'）而导致程序崩溃
            time_str = exam.get('report_time', '时间未知')
            desc = exam.get('description', '无描述')
            analysis = exam.get('image_analysis', '无分析结果')
            exam_str = f"{desc}:{analysis}"
            
            if include_time:
                output_parts.append(f"{time_str};{exam_str};")
            else:
                output_parts.append(f"{exam_str};")
        
        # 如果包含时间，则按指定顺序对整个报告进行排序
        if include_time:
            output_parts.sort(reverse=(sort_order == "desc"))
            
        return "".join(output_parts)

    # --- 2. 主处理流程 (Main Processing Logic) ---
    
    final_lab_output = ""
    final_exam_output = ""

    # --- 处理检验信息 ---
    if 'lab_tests_config' in config:
        lab_config = config['lab_tests_config']
        # 创建一个副本进行处理，避免修改原始输入列表
        processed_labs = list(lab_tests) 
        
        # 关键处理顺序：先按内容筛选，再按时间筛选。
        # 这样确保了 'latest'/'earliest' 等操作是作用于符合内容条件的记录集合上。
        processed_labs = _filter_lab_tests(processed_labs, lab_config.get('filter', {}))
        processed_labs = _filter_by_time(processed_labs, lab_config.get('time_filter', {}))
        
        # 格式化最终结果
        final_lab_output = _format_lab_output(processed_labs, lab_config.get('output_format', {}))

    # --- 处理检查信息 ---
    if 'examinations_config' in config:
        exam_config = config['examinations_config']
        processed_exams = list(examinations)

        # 同样，先按内容筛选，再按时间筛选
        processed_exams = _filter_examinations(processed_exams, exam_config.get('filter', {}))
        processed_exams = _filter_by_time(processed_exams, exam_config.get('time_filter', {}))
        
        # 格式化最终结果
        final_exam_output = _format_exam_output(processed_exams, exam_config.get('output_format', {}))
    
    # --- 拼接并返回最终结果 ---
    combined_output = final_lab_output + final_exam_output
    
    # 如果处理后没有任何输出，则返回 "无"
    return combined_output if combined_output else "无"

def process_medical_data(emr_text: str, config: Dict[str, Any], file_path: str) -> str:
    """
    处理医疗数据文本并返回格式化结果。

    Args:
        emr_text (str): 包含医疗数据的文本字符串，格式为“###全部检查:\n...###简化过滤检验:\n...”
        config (Dict[str, Any]): 配置字典，包含用户选择的过滤和输出选项。
        file_path (str): 若数据预处理未处理检验数据，则直接读取原json。

    Returns:
        str: 格式化后的结果字符串。
    """
    # 解析原始数据（文本格式）
    examinations, lab_tests = extract_medical_data(emr_text, file_path)

    # 处理并格式化数据
    return process_medical_data_by_config(examinations, lab_tests, config)

class DynamicRuleInterpreter:
    def __init__(self):
        """
        初始化一个轻量级的、功能完备的规则解释器。
        它负责管理规则的执行逻辑、动态上下文，并为不同类型的规则生成最优化的Prompt。
        """
        self.dynamic_context = {}
        self.all_rules_map = {}
        
        # 内置一个指令模板库，为每种操作类型量身定制指令
        self.prompt_templates = {
            "抽取": (
                "任务：请严格依据以上{basis_description}提供的文本内容，抽取出关于“{target}”的核心信息。\n\n"
                "**行为准则 (CRITICAL RULES):**\n"
                "1.  **必须**只从提供的文本中抽取，**绝对禁止**进行任何形式的推断、联想或使用外部知识。\n"
                "2.  如果文本中没有明确提到“{target}”，请回答“未在文本中找到相关信息”。\n"
                "3.  输出**必须**是简洁、客观的事实，不要添加任何解释性文字，如“根据上下文，...”。\n"
                "4.  确保输出为一行标准的文本。"
            ),
            "推理": (
                "任务：请严格基于以上{basis_description}提供的信息，对“{target}”进行逻辑推理，并得出结论。\n\n"
                "**行为准则 (CRITICAL RULES):**\n"
                "1.  你的所有推理过程和最终结论，其**全部依据都必须**来自于提供的文本。\n"
                "2.  **绝对禁止**引入任何文本中未包含的假设或外部医学知识。\n"
                "3.  结论必须是逻辑严密的、可以直接从原文推导出来的。\n"
                "4.  请将最终结论总结为一句或一段通顺的话，不要使用列表或项目符号。"
            ),
            "摘要": (
                "任务：请通读以上{basis_description}提供的所有文本，并概括出关于“{target}”的核心要点。\n\n"
                "**行为准则 (CRITICAL RULES):**\n"
                "1.  摘要中的每一个要点都**必须**能在原文中找到直接或间接的对应依据。\n"
                "2.  **绝对禁止**在摘要中加入任何原文未提及的新信息或个人观点。\n"
                "3.  请将所有要点浓缩成一句或一段连贯、精炼的陈述句。"
            ),
            "判断": (
                "任务：请严格依据以上{basis_description}提供的信息，对“{target}”进行判断。\n\n"
                "**行为准则 (CRITICAL RULES):**\n"
                "1.  你的判断**必须**完全基于提供的文本内容。\n"
                "2.  {options_text}\n"
                "3.  **绝对禁止**输出除了指定答案之外的任何其他文字。"
            ),
            "default": (
                "任务：请严格依据以上{basis_description}提供的文本，处理关于“{target}”的信息。你的回答必须完全基于所给文本，禁止任何形式的推测或补充。"
            )
        }
        print("动态规则解释器已初始化。")

    def _infer_role(self, rule_id: str) -> str:
        """
        根据一条规则是否被其他规则依赖，来动态推断其角色。
        如果任何其他规则的 'dependencies' 列表中包含此 rule_id，则它是中间过程。
        """
        for rule in self.all_rules_map.values():
            if rule_id in rule.get("dependencies", []):
                return "intermediate"
        return "final"

    def _generate_prompt(self, rule: dict, emr_data_dict: dict, full_emr_text: str) -> str:
        """
        最终版的Prompt生成器，使用内置的模板库为不同类型的规则动态构建最优指令。
        同时具备对无效source的回退机制。
        """
        
        # --- 第一部分：准备上下文和已知信息模块 ---
        source_blocks = []
        source_descriptions = []

        # rule的 "sources" 字段现在是一个列表
        source_keywords = rule.get("sources", [])

        # 获取所有可用的、唯一的病历章节标题
        available_emr_keys = list(emr_data_dict.keys())

        final_source_keys = []
        use_full_emr_fallback = False
    
        if not source_keywords and not rule.get("dependencies"):
            # 情况1：规则本身没有任何来源或依赖，强制回退
            print(f"警告：规则 '{rule.get('id', 'N/A')}' 没有任何来源或依赖。将强制使用“全部文书”。")
            use_full_emr_fallback = True
        elif source_keywords:
            # 情况2：规则有指定的sources，检查它们是否都有效
            # 只要有一个是“全部文书”，就直接用全部文书
            if "全部文书" in source_keywords:
                use_full_emr_fallback = True
            else:
                # 遍历每一个关键词进行匹配
                all_keywords_matched = True
                temp_matched_keys = []
                # 检查是否有任何一个key在emr_data_dict中找不到
                for keyword in source_keywords:
                    # 为当前关键词查找所有匹配的真实章节名
                    matches_for_keyword = [emr_key for emr_key in available_emr_keys if keyword in emr_key]
                    
                    if not matches_for_keyword:
                        # **触发回退！** 只要有一个关键词匹配失败
                        print(f"警告：规则 '{rule.get('id', 'N/A')}' 的关键词 '{keyword}' 未匹配到任何病历章节。触发回退机制！")
                        all_keywords_matched = False
                        break # 立刻停止匹配
                    else:
                        temp_matched_keys.extend(matches_for_keyword)
                if all_keywords_matched:
                    # 所有关键词都成功匹配，去重并保持顺序
                    final_source_keys = sorted(list(set(temp_matched_keys)), key=temp_matched_keys.index)
                else:
                    # 只要有一个失败，就触发回退
                    use_full_emr_fallback = True
        
        if use_full_emr_fallback:
            final_source_keys = ["全部文书"]

        # --- 根据预检查的结果，决定最终使用的source_keys ---
        for source_key in final_source_keys:
            source_text = ""
            # 检查是否是特殊指令 "全部文书"
            if source_key == "全部文书":
                source_text = full_emr_text
                source_description = f"“上下文（源自：全部文书）”"
                # 如果是全部文书，通常不再需要其他上下文
                source_blocks.append(f"{source_description.replace('“','').replace('”','')}:\n---\n{source_text}\n---")
                source_descriptions.append(source_description)
                break # 跳出循环，因为已经有了最全的上下文
            
            # 否则，是普通的病历章节
            elif source_key in emr_data_dict:
                source_text = emr_data_dict[source_key]
                if source_text:
                    source_description = f"“上下文（源自：{source_key}）”"
                    source_blocks.append(f"{source_description.replace('“','').replace('”','')}:\n---\n{source_text}\n---")
                    source_descriptions.append(source_description)
        
        # 将所有上下文块组合成一个大的字符串
        full_source_text_block = "\n\n".join(source_blocks) if source_blocks else ""

        # 检查并处理来自前序规则的依赖信息
        known_info_block = ""
        dependencies = rule.get("dependencies", [])
        if dependencies:
            known_info_parts = []
            for dep_id in dependencies:
                if dep_id in self.dynamic_context:
                    dep_rule = self.all_rules_map.get(dep_id, {})
                    dep_output = self.dynamic_context[dep_id].get("output", "")
                    known_info_parts.append(f"关于“{dep_rule.get('target', '未知目标')}”的信息是：“{dep_output}”")
            
            if known_info_parts:
                known_info_block = "已知信息：\n---\n" + "\n".join(known_info_parts) + "\n---"

        # --- 第二部分：动态构建任务指令 ---
        basis_parts = []
        if full_source_text_block:
            # 如果有多个来源，就用一个总称“上下文”
            if len(source_descriptions) > 1:
                basis_parts.append("多个“上下文”章节")
            elif len(source_descriptions) == 1:
                basis_parts.append(source_descriptions[0]) # 使用具体的来源描述
        if known_info_block:
            basis_parts.append("“已知信息”")
        
        if not basis_parts:
            return f"错误：规则 '{rule.get('id', 'N/A')}' 无效，因为它既没有指定有效的源章节，也没有有效的依赖项。"
            
        basis_description = "和".join(basis_parts)
        rule_type = rule.get("type", "default")
        target = rule.get("target", "")

        # 从模板库中获取对应类型的指令模板
        task_template = self.prompt_templates.get(rule_type, self.prompt_templates["default"])

        # 为“判断”类型准备 options_text
        options_text = ""
        if rule_type == "判断":
            options = rule.get("options")
            if options and isinstance(options, list):
                options_text = f"请严格从[{' / '.join(options)}]中选择一个作为答案，并且只回答这个选项词语本身。"
            else:
                options_text = "请做出判断，并用'是'或'否'来回答。"
        
        # 使用 .format() 填充模板
        task_instruction = task_template.format(
            basis_description=basis_description,
            target=target,
            options_text=options_text
        )

        # --- 第三部分：将所有模块组合成最终的Prompt ---
        prompt_sections = []
        if full_source_text_block:
            prompt_sections.append(full_source_text_block)
        if known_info_block:
            prompt_sections.append(known_info_block)
        
        prompt_sections.append(task_instruction)

        return "\n\n".join(prompt_sections)

    def execute_rule(self, rule: dict, emr_data_dict: dict, full_emr_text: str, model, tokenizer):
        """
        执行单条规则：生成Prompt -> 调用模型 -> 更新上下文。
        """
        rule_id = rule["id"]
        print(f"--- 正在执行规则: {rule_id} ({rule.get('type', '未知类型')}) ---")
        
        final_prompt = self._generate_prompt(rule, emr_data_dict, full_emr_text)
        print(f"动态生成的Prompt:\n{final_prompt}\n")

        if final_prompt.startswith("错误："):
            print(f"跳过规则执行：{final_prompt}")
            response = final_prompt
        else:
            # 调用外部独立的模型函数
            # response = generate_qwen_response(model, tokenizer, user_prompt=final_prompt)

            response = chat_with_api(model=model, user_prompt=final_prompt)
            print(f"模型返回结果: {response}\n")

        # 立即更新动态上下文，为后续依赖提供数据
        self.dynamic_context[rule_id] = {
            "output": response.strip(),
            "target": rule.get("target", "未知目标")
        }

    def run(self, user_defined_rules: list, emr_data_dict: dict, full_emr_text: str, model, tokenizer) -> dict:
        """
        主执行流程，负责调度整个规则链的执行，并返回带有角色信息的完整上下文。
        """
        # 重置状态
        self.dynamic_context = {}
        self.all_rules_map = {rule["id"]: rule for rule in user_defined_rules}
        
        # (生产环境建议) 在这里对 user_defined_rules 进行拓扑排序
        sorted_rules = user_defined_rules
        
        # 循环执行所有规则
        for rule in sorted_rules:
            self.execute_rule(rule, emr_data_dict, full_emr_text, model, tokenizer)

        # 所有规则执行完毕后，统一推断角色
        for rule_id in self.dynamic_context:
            self.dynamic_context[rule_id]["role"] = self._infer_role(rule_id)

        # 返回包含了所有结果和元信息的最终上下文
        return self.dynamic_context

def _run_rule_chain_for_facts(rules_for_field: list, field_name_prefix: str, emr_data_dict: dict, full_emr_text: str, model, tokenizer) -> dict:
    """
    一个可复用的辅助函数，负责执行一串规则并返回筛选后的最终事实。
    这是整个流程中的“规则执行引擎”。
    """
    if not rules_for_field:
        return {}

    # 1. 数据转换与依赖解析
    pre_processed_rules, rule_index_to_id_map = [], {}
    for i, rule_obj in enumerate(rules_for_field):
        rule_id = f"{field_name_prefix}_{i}_{uuid.uuid4().hex[:4]}"
        pre_processed_rules.append({"id": rule_id, "original_rule": rule_obj})
        rule_index_to_id_map[f"第{i+1}条逻辑规则"] = rule_id

    backend_rules = []
    for item in pre_processed_rules:
        rule_id, rule_obj = item["id"], item["original_rule"]
        dependencies, sources = [], []

        for record in rule_obj.get("sourceRecords", []):
            if record in rule_index_to_id_map:
                dependencies.append(rule_index_to_id_map[record])
            else:
                sources.append(record)
        
        backend_rules.append({
            "id": rule_id, 
            "type": rule_obj["label"], 
            "sources": sources,
            "target": rule_obj["fieldNames"], 
            "dependencies": dependencies
        })

    print(f"\n--- 为【{field_name_prefix}】转换并解析依赖后的后端规则 ---")
    print(json.dumps(backend_rules, indent=2, ensure_ascii=False))

    # 2. 执行规则链并推断角色
    interpreter = DynamicRuleInterpreter()
    final_context = interpreter.run(backend_rules, emr_data_dict, full_emr_text, model, tokenizer)
    
    print(f"\n--- 为【{field_name_prefix}】执行所有规则后，包含角色推断的最终上下文 ---")
    print(json.dumps(final_context, indent=2, ensure_ascii=False))

    # 3. 智能筛选，只保留角色为 'final' 的结果
    final_facts = {}
    print(f"\n--- 开始为【{field_name_prefix}】筛选用于总结的事实 ---")
    for rule_id, result in final_context.items():
        if result.get("role") == "final":
            print(f"采纳最终事实: '{result['target']}' (来自规则 {rule_id})")
            final_facts[result['target']] = result['output']
    
    print(f"\n--- 为【{field_name_prefix}】筛选后的最终事实 ---")
    print(json.dumps(final_facts, indent=2, ensure_ascii=False))

    return final_facts

def refine_and_validate_json(
    model,
    tokenizer,
    raw_text: str,
    system_prompt: str = "你是一个精确的数据格式转换工具，专门将文本修正为严格的JSON格式。") -> dict:
    """
    接收一段可能格式不正确的文本，并尽力将其转换为一个结构化的、字段完整的JSON字典。
    它会先尝试直接解析，如果失败，则调用模型进行修复。

    Args:
        model: 已加载的模型。
        tokenizer: 已加载的分词器。
        raw_text (str): 模型初步生成的、可能格式不正确的文本。
        system_prompt (str): 为修复任务设定的角色。

    Returns:
        dict: 一个保证格式正确且字段完整的Python字典。如果修复失败，会返回一个包含错误信息的字典。
    """
    print("\n--- 开始执行JSON格式校验与修复 ---")

    # 定义“患者基本信息”字段所有必需的键
    # 这个列表现在是函数内部的“知识”
    required_keys = [
        "住院号", "床号", "入院时间", "出院时间", "科别", "科室", "姓名", 
        "年龄", "性别", "低压(BP低)", "高压(BP高)", "脉搏(P)", "呼吸(R)", 
        "体温(T)", "入院诊断", "入院时简要病史", "体检摘要"
    ]

    # 1. 尝试直接解析
    try:
        # 策略1：最基本的清理
        text_to_parse = raw_text.strip()
        
        # 策略2：处理Markdown代码块标记
        if text_to_parse.startswith("```json"):
            text_to_parse = text_to_parse[7:]
        if text_to_parse.startswith("```"):
            text_to_parse = text_to_parse[3:]
        if text_to_parse.endswith("```"):
            text_to_parse = text_to_parse[:-3]
        text_to_parse = text_to_parse.strip()
        
        # 策略3：【关键】尝试修复未转义的换行符和尾随逗号。这是一个更宽容的解析尝试。
        # 注意：这需要一个更灵活的解析器，但我们可以先尝试用正则表达式移除尾随逗号
        text_to_parse = re.sub(r',\s*([}\]])', r'\1', text_to_parse)

        # 尝试使用标准的json.loads()
        parsed_json = json.loads(text_to_parse)
        
        if not isinstance(parsed_json, dict):
            raise ValueError("解析结果不是一个字典。")

        # 检查并补全缺失的键
        missing_keys = [key for key in required_keys if key not in parsed_json]
        if missing_keys:
            print(f"警告：JSON有效，但缺少字段：{missing_keys}。正在补全...")
            for key in missing_keys:
                parsed_json[key] = "" 
        
        print("通过自我修复和直接解析成功！")
        return parsed_json

    except (json.JSONDecodeError, ValueError) as e:
        print(f"警告：初步输出不是有效的JSON ({e})。启动模型修复流程...")

        # 2. 如果直接解析失败，则调用模型进行修复
        # 构建专门用于修复的Prompt
        repair_prompt = (
            f"原始的、格式错误的文本如下：\n"
            f"----------------\n"
            f"{raw_text}\n"
            f"----------------\n\n"
            f"修复任务：\n"
            f"1.  请将上述文本严格转换为一个标准的JSON对象格式。\n"
            f"2.  最终的JSON**必须**包含以下所有字段：{json.dumps(required_keys, ensure_ascii=False)}。\n"
            f"3.  对于在原始文本中找不到对应信息的字段，请保留该字段的键，并将其值设置为空字符串 `\"\"`。\n"
            f"4.  请不要输出任何解释、代码块标记（```json ... ```）或其他多余的文字，只返回纯净的、可以直接解析的JSON文本。"
        )

        # 调用模型执行修复任务
        # repaired_text = generate_qwen_response(
        #     model=model,
        #     tokenizer=tokenizer,
        #     user_prompt=repair_prompt,
        #     system_prompt=system_prompt
        # )

        repaired_text = chat_with_api(model="postprocess", user_prompt=repair_prompt, system_prompt=system_prompt)
        
        # 3. 最后一次尝试解析修复后的文本
        try:
            # 再次清理可能存在的代码块标记
            final_cleaned_text = repaired_text.strip().lstrip("```json").rstrip("```").strip()
            final_json = json.loads(final_cleaned_text)

            if not isinstance(final_json, dict):
                 raise ValueError("修复后的结果依然不是一个字典。")

            # 最后再检查一遍并补全缺失的键，确保万无一失
            for key in required_keys:
                if key not in final_json:
                    final_json[key] = ""
            
            print("JSON修复并校验成功！")
            return final_json
        
        except (json.JSONDecodeError, ValueError) as final_e:
            print(f"错误：模型修复后的文本仍然无法解析 ({final_e})。返回包含错误信息的字典。")
            return {"error": "JSON_REPAIR_FAILED", "original_faulty_text": raw_text, "repaired_text": repaired_text}

def transform_and_process_field(
    field_name: str, 
    field_config: dict,
    emr_data_dict: dict, 
    full_emr_text: str,
    model, 
    tokenizer
    ) -> str:
    """
    【最终版-混合控制模式】
    接收一个字段的完整配置（包括规则和用户指南），完成从转换、执行、智能筛选到最终总结和后处理的全过程。

    Args:
        field_name (str): 目标字段名，如 "出院诊断"。
        field_config (dict): 包含 'rules' 和 'user_guidance' 的配置对象。
        emr_data_dict (dict): 按章节切分好的病历数据字典。
        full_emr_text (str): 完整的、未经切分的原始病历字符串。
        model: 已加载的模型对象。
        tokenizer: 已加载的分词器对象。

    Returns:
        str: 为该字段生成的最终文本。
    """
    print(f"\n=============================================")
    print(f"   开始处理字段: 【{field_name}】")
    print(f"=============================================")

    rules_for_field = field_config.get("logic_rule", [])
    
    # **【核心复用】** 调用辅助函数执行规则链
    final_facts_for_summary = _run_rule_chain_for_facts(
        rules_for_field, 
        field_name, 
        emr_data_dict, 
        full_emr_text, 
        model, 
        tokenizer
    )
    
    # 步骤3: 调用最终的总结模型（混合控制模式）
    summary_text = "\n".join([f"- {k}: {v}" for k, v in final_facts_for_summary.items()]) or "（无用户定义的关键信息，请直接基于原始病历全文进行总结）"
    user_guidance = field_config.get("user_guidance", "") if isinstance(field_config, dict) else ""
    guidance_to_insert = user_guidance.strip() or "请按照通用医学规范进行总结。"

    # 从后端的策略库中获取该字段的Prompt“骨架”
    strategy = SUMMARY_STRATEGIES_HYBRID.get(field_name, SUMMARY_STRATEGIES_HYBRID["default"])
    prompt_template = strategy.get("prompt_template", "")
    
    # 格式化最终的Prompt，将所有部分都填充进去
    final_summary_prompt = prompt_template.format(
        summary_text=summary_text,
        original_text=full_emr_text,
        user_guidance=guidance_to_insert
    )

    print(f"\n用于总结字段【{field_name}】的最终Prompt (混合控制):")
    print(final_summary_prompt)

    # 根据有无筛选出的事实，赋予模型不同的角色
    if final_facts_for_summary:
        final_system_prompt = "你是一位资深的医学文书专家，请将给定的要点、用户指南和参考原文，严谨地进行总结。"
    else:
        final_system_prompt = f"你是一位资深的医学文书专家，请直接通读“原始病历全文”，并根据用户指南独立撰写关于“{field_name}”的内容。"

    # 生成初步的总结文本
    # initial_field_text = generate_qwen_response(
    #     model=model, 
    #     tokenizer=tokenizer, 
    #     user_prompt=final_summary_prompt,
    #     system_prompt=final_system_prompt
    # )

    initial_field_text = chat_with_api(model=model, user_prompt=final_summary_prompt, system_prompt=final_system_prompt)
    
    # 默认最终输出为初始文本
    final_output = initial_field_text.strip()

    if field_name == "患者基本信息":
        print("\n检测到“患者基本信息”字段，启动JSON格式校验后处理...")
        # 调用简版的JSON校验函数，它只负责确保格式正确
        verified_json_dict = refine_and_validate_json(model, tokenizer, raw_text=initial_field_text)
        final_output = json.dumps(verified_json_dict, indent=2, ensure_ascii=False)

    return final_output

def format_numbered_list(text: str) -> str:
    """
    自适应地格式化带有序号的文本。

    函数会首先检测文本中是先出现 "数字、" 还是 "数字." 格式的序号，
    然后以该格式为标准，处理整个文本。
    - 保持原始的序号格式（如 "1." 不会变成 "1、"）。
    - 确保每一项内容都以句号结尾。

    Args:
        text: 包含 "1、 2、" 或 "1. 2." 格式列表的输入字符串。

    Returns:
        一个根据原文格式进行标准化的字符串。
    """
    if not text:
        return ""

    # 1. --- 侦测阶段 ---
    # 定义两种可能的序号模式
    pattern_dun = re.compile(r'\b(\d+)、')  # 格式: 1、, 2、
    pattern_dot = re.compile(r'\b(\d+)\.')  # 格式: 1., 2. (注意.需要转义)

    # 分别查找两种模式第一次出现的位置
    match_dun = pattern_dun.search(text)
    match_dot = pattern_dot.search(text)

    # 获取位置索引，如果未找到则设为无穷大，便于比较
    pos_dun = match_dun.start() if match_dun else float('inf')
    pos_dot = match_dot.start() if match_dot else float('inf')

    # 如果两种格式都未找到，直接返回原文
    if pos_dun == float('inf') and pos_dot == float('inf'):
        return text

    # 根据先出现的格式，选择要使用的模式
    if pos_dun <= pos_dot:
        chosen_pattern = pattern_dun
    else:
        chosen_pattern = pattern_dot
        
    # 2. --- 处理阶段 ---
    # 使用选定的模式查找所有匹配项
    matches = list(chosen_pattern.finditer(text))

    result_items = []
    
    # 遍历所有找到的标记，并提取它们之间的内容
    for i, current_match in enumerate(matches):
        # 保留原始的序号格式，不再进行标准化
        original_marker = current_match.group(0)

        # 确定内容的起止位置
        content_start = current_match.end()
        if i + 1 < len(matches):
            content_end = matches[i+1].start()
        else:
            content_end = len(text)
            
        # 提取内容并清理
        content = text[content_start:content_end].strip()

        if not content:
            continue

        # 统一处理结尾标点
        punctuations_to_replace = '；;，,。．.!！?？'
        if content.endswith(tuple(punctuations_to_replace)):
            content = content[:-1] + '。'
        else:
            content += '。'
            
        # 拼接原始序号和处理后的内容
        result_items.append(original_marker + content) # 加一个空格更美观
        
    # 保留可能存在的前缀文本
    first_marker_start = matches[0].start()
    prefix = text[:first_marker_start]

    # 使用 " " 连接各个条目，使其分开，更易读
    return prefix + "".join(result_items)

def generateDS(model,tokenizer,ins_datas,key_id,keshi,out_dir='全部由模型生成',generation_params={}):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    preds = {}
    print(key_id,'全部的指令数据条数:{}'.format(len(ins_datas)))
    print(json.dumps(ins_datas, indent=2, ensure_ascii=False))
    for now_index,data in enumerate(ins_datas):
        zylsh = data['zylsh']

        if zylsh not in preds.keys():
            preds[zylsh] = {
                'output':{},
                'find_source':{}
            }

        data_key = data['key']
        now_key = data['key']
        now_input = data['instruction']
        # print('当前提示词：',now_input)
        gold = data['output']

        # try:
        #     tokenized_output = tokenizer.build_chat_input(data['instruction'])
        #     prompt_token_length = len(tokenized_output['input_ids'][0])
        # except Exception as e:
        #     print(f"为字段 {data['key']} 构建聊天输入时出错: {e}")
        #     prompt_token_length = 99999

        # # 使用变量进行判断
        # if prompt_token_length > 8000:
        #     print(f"Token 长度为 {prompt_token_length}，超过8000的限制。")
        #     res_json = {now_key: '输入数据过长，模型无法输出！'}
        #     print('当前数据"{}"字段生成过程中，输入过长，该字段无法正常输出'.format(data['key']))

        #     # +++ 新增打印 +++
        #     print("\n=== 生成结果 ===")
        #     print(f"字段：{data['key']}")
        #     print("状态：输入过长导致生成失败\n")

        
        if data_key == "住院期间医疗情况":
            if keshi == "肿瘤医院头颈外科":
                file_path = os.path.join(
                    "Intermediate_process",
                    "final_preprocessed_responses",
                    f"final_sources_{zylsh}.json"
                )
            else:
                file_path = os.path.join(
                    "Intermediate_process", 
                    "instructions", 
                    keshi, 
                    zylsh, 
                    'source.json'
                )
            res = process_medical_data(data['instruction'], data['input'], file_path)
        else:
            if keshi == "肿瘤医院头颈外科":
                file_path = os.path.join(
                    "Intermediate_process",
                    "final_preprocessed_responses",
                    f"final_sources_{zylsh}.json"
                )
            else:
                file_path = os.path.join(
                    "Intermediate_process", 
                    "instructions", 
                    keshi, 
                    zylsh, 
                    'final_data.json'
                )
            with open(file_path, 'r', encoding='utf8') as f:
                loaded_data = json.load(f)
            
            res = transform_and_process_field(data_key, data['input'], loaded_data[data_key], data['instruction'], model, tokenizer)

            if data_key == "出院后用药建议":
                res = format_numbered_list(res)

        # +++ 新增打印原始结果 +++
        # print("\n=== 原始生成结果 ===")
        # print(f"字段：{data['key']}")
        # print(f"原始输出：\n{res}\n")

        if now_key == '患者基本信息':
            # 检查是否是json
            try:
                res_json = {now_key:json.loads(res)}

                # +++ 新增成功打印 +++
                print("=== JSON解析成功 ===")
                print(json.dumps(res_json, indent=2, ensure_ascii=False))

            except:
                # 多次尝试
                for i in range(3):
                    # print('患者基本信息生成：第{}次尝试'.format(i+1))
                    print(f"患者基本信息生成格式有误，进行修正：第 {i + 1} 次尝试")
                    res = refine_and_validate_json(model, tokenizer, res)
                    try:
                        res_json = {now_key:json.loads(res)}
                        # 成功转json后，break
                        break
                    except:
                        # 否则继续尝试生成
                        pass
                # 多次后仍然无法生成
                try:
                    res_json = {now_key:json.loads(res)}
                except:
                    print('无法转json:{}'.format(res))
                    # 否则尝试转成json
                    res = res.strip()
                    if res[-1] == '}':
                        print('去掉最后的}，加上"}')
                        res = res[:-1]+'"}'
                    elif res[-1] == '\'' or res[-1] == '"':
                        print('最后是引号，直接加上大括号')
                        res = res + '}'
                    else:
                        print('直接加上引号与大括号')
                        res = res + '"}'
                # 最后尝试转json
                try:
                    res_json = {now_key:json.loads(res)}
                except:
                    print('患者基本信息字段 输出错误')
                    res_json = {
                        "患者基本信息": {
                            "住院号": "error",
                            "床号": "error",
                            "入院时间": "error",
                            "出院时间": "error",
                            "科别": "error",
                            "科室": "error",
                            "姓名": "error",
                            "年龄": "error",
                            "性别": "error",
                            "低压(BP低)": "error",
                            "高压(BP高)": "error",
                            "脉搏(P)": "error",
                            "呼吸(R)": "error",
                            "体温(T)": "error",
                            "入院诊断": "error",
                            "入院时简要病史": "error",
                            "体检摘要": "error"
                        }
                    }
        else:
            res_json = {now_key:res}

        preds[zylsh]['output'].update(res_json)
        preds[zylsh]['find_source'][data_key] = now_input 
    with open(os.path.join(out_dir,'{}.json'.format(key_id)),'w',encoding='utf8') as f:
        json.dump(preds,f,indent=4,ensure_ascii=False)
    return preds


if __name__ == '__main__':
    print('构造指令数据')
    data_dir = sys.argv[1]
    keshi = sys.argv[2]
    zylsh = sys.argv[3]
    out_dir = sys.argv[4]
    model_path = sys.argv[5]
    gpu = sys.argv[6]

    # show_dir = '/HL_user01/2024_03_24_生成出院小结_演示/演示/全部由模型生成'
    # 加载模型
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, trust_remote_code=True, device=gpu)
    
    data_name = '出院小结及子字段.jsonl'
    data_dir = os.path.join(data_dir,keshi)
    if zylsh == '-1':
        # 处理全部
        zylshs = os.listdir(data_dir)
    elif zylsh == '-2':
        zylshs = np.loadtxt(f'./流水号/{keshi}_新增源文件流水号.csv', delimiter=',',dtype=str)
        zylshs = list(zylshs)
        # zylshs = zylshs[344:]
    else:
        zylshs = [zylsh]

    print('处理{}个病例'.format(len(zylshs)))
    for zylsh in zylshs:
        ins_data_path = os.path.join(data_dir,zylsh,data_name)
        with jsonlines.open(ins_data_path,'r') as f:
            datas = [line for line in f]
        now_out_dir = os.path.join(out_dir,keshi,zylsh)
        generateDS(model,tokenizer,datas,zylsh,now_out_dir)
        # source = os.path.join(now_out_dir,'{}.json'.format(zylsh))
        # target = os.path.join(show_dir,'{}.json'.format(zylsh))
        # shutil.copy(source,target)

