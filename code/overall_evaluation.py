import os
import json
from openai import OpenAI
from tqdm import tqdm
from collections import defaultdict
import time
import sys
import re

# -------------------------- 配置参数 --------------------------
# 请将此路径修改为您实际的文件路径
# FILE_PATH = "/root/nas/瑞金/EMR-Paper-data/generate_model/1103Uncleaned/yyjy.jsonl"
FILE_PATH = "./backfill_cleaned.jsonl"
OUTPUT_FILE_PATH = "./llama_calculation_results_backfill_cleaned.jsonl" # 输出文件名为前10条
STATS_OUTPUT_PATH = "./llama_overall_dept_stats_backfill_cleaned.json"  # 新增：整体和科室统计文件
MODEL_NAME = " "
MAX_RETRIES = 3
LLM_TEMPERATURE = 0.01 # 使用较低的温度以获得稳定的事实比对结果
MAX_SAMPLES = 454 # 限制处理的样本数量

# -------------------------- API 配置 --------------------------
try:
    # ⚠️ 确保环境变量 DASHSCOPE_API_KEY 已设置，或在此处硬编码。
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY", " "),
        base_url=" "
    )
    print("✅ API 客户端初始化成功。")
except Exception as e:
    print(f"❌ API 客户端初始化失败: {e}")
    sys.exit(1)

# -------------------------- 核心逻辑函数 --------------------------
def safe_int_convert(value, default=0):
    """安全地将值转换为int，如果失败则返回默认值"""
    if isinstance(value, int):
        return value
    elif isinstance(value, (str, float)):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            pass
    elif isinstance(value, list) or isinstance(value, dict):
        # 如果是意外的list或dict，记录警告并返回默认
        tqdm.write(f"⚠️ 检测到非数字类型 ({type(value)}): {value}，转换为默认值 {default}")
        return default
    return default

def calculate_metrics(N, M, X, Y):
    """根据事实数量计算三个指标"""
    if N == 0:
        cfcr = 0.0
    else:
        cfcr = X / N # 核心事实覆盖率
    if M == 0:
        fcr = 0.0
        fhr = 0.0
    else:
        fcr = (X + Y) / M # 事实符合率
        fhr = (M - X - Y) / M # 事实幻觉率
  
    return cfcr, fcr, fhr

def process_single_item(item, client):
    """处理单个数据项，构建Prompt，调用LLM并计算指标"""
    gold_truth = item.get("output", "")
    model_summary = item.get("new_summary", "")
  
    # 从 instruction 中提取撰写建议
    instruction_full = item.get("instruction", "")
    try:
        # 假设撰写建议在 '撰写建议:' 后
        instruction_advice = instruction_full.split("撰写建议:")[1].strip()
    except IndexError:
        # 如果没有找到分隔符，则使用整个 instruction 作为建议，并进行清理
        instruction_advice = "；".join([line.strip() for line in instruction_full.split('\n') if line.strip()])
        if not instruction_advice:
            instruction_advice = "无明确撰写建议"
    # 构建 LLM Prompt 结构
    prompt_data = {
      "gold_truth": gold_truth,
      "model_summary": model_summary,
      "instruction_advice": instruction_advice
    }
  
    # 构造 LLM 提示词 (Prompt)
    prompt = f"""
    请严格执行以下医疗文本事实比对和分类任务，并以JSON格式返回结果。这是输入数据：
    {json.dumps(prompt_data, ensure_ascii=False, indent=2)}
    请严格遵循以下步骤：
    1. 拆解：将 'gold_truth' 拆解成离散的 N_facts 列表。将 'model_summary' 拆解成 M_facts 列表。将 'instruction_advice' 拆解成 I_facts 列表。
    2. 比对与分类 (M中的每个事实必须分类)：
       - **核心匹配 (X):** 对于 M_facts 中的事实 m_i，首先判断是否与 N_facts 中某个事实**语义高度一致**。
       - **指令匹配 (Y):** 如果 m_i 不属于 X 类，则判断 m_i 是否合理地**满足**了 I_facts 中的某个指令要求。
       - **幻觉事实 (H):** 如果 m_i 既不属于 X 也不属于 Y，则归类为 "H"。
    3. 返回：返回一个单一的JSON对象，包含 'N_total', 'M_total', 'X_matched', 'Y_matched', 'N_facts_list', 'M_facts_list', 'I_facts_list' 和 'match_details' 列表。
       - 'N_total' 和 'M_total' 必须是整数（列表长度）。
       - 'match_details' 是每个 M_facts 的分类列表，每个项是 dict 如 {{'model_fact': '事实文本', 'gold_fact': '匹配金标准（如果X）或空', 'instruction_fact': '匹配指令（如果Y）或空', 'type': 'X' 或 'Y' 或 'H'}}。
    严格返回 JSON 对象，不要包含任何额外文字或解释。
    """
    # LLM API 调用 (带重试机制)
    llm_output = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "你是一个严谨的事实项比对助手，请严格按照用户要求返回JSON。确保数字键值为整数，列表为数组。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=LLM_TEMPERATURE
            )
            response_content = response.choices[0].message.content
          
            # 尝试解析 JSON
            llm_output = json.loads(response_content)
            break
      
        except json.JSONDecodeError:
            tqdm.write(f"⚠️ API 返回非标准 JSON (第 {attempt + 1} 次重试)，尝试重新调用。")
            llm_output = None
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            tqdm.write(f"⚠️ API调用失败 (第 {attempt + 1} 次重试): {e}")
            llm_output = None
            time.sleep(2 * (attempt + 1))
          
    if llm_output is None or "match_details" not in llm_output:
        # 失败时，返回默认/幻觉结果
        tqdm.write(f"❌ LLM事实比对失败，样本 {item.get('zylsh', 'N/A')} 标记为幻觉。")
        # 尝试从输入数据中估计 M (用于 FHR)
        M_fallback = len(re.findall(r'[0-9]+[、\.，]', model_summary)) or 1
      
        return {
            "error": "LLM fact comparison failed after retries or returned bad JSON.",
            "CFCR": 0.0, "FCR": 0.0, "FHR": 1.0,
            "N": 0, "M": M_fallback, "X": 0, "Y": 0,
            "match_details": []
        }
    
    # 鲁棒计算：从列表派生总数，覆盖 LLM 可能的错误
    N_facts_list = llm_output.get("N_facts_list", [])
    N = len(N_facts_list) if isinstance(N_facts_list, list) else safe_int_convert(llm_output.get("N_total", 0))
    
    match_details = llm_output.get("match_details", [])
    if isinstance(match_details, list):
        M = len(match_details)
        X = sum(1 for d in match_details if isinstance(d, dict) and d.get('type') == 'X')
        Y = sum(1 for d in match_details if isinstance(d, dict) and d.get('type') == 'Y')
    else:
        M = safe_int_convert(llm_output.get("M_total", 0))
        X = safe_int_convert(llm_output.get("X_matched", 0))
        Y = safe_int_convert(llm_output.get("Y_matched", 0))
    
    I_facts_list = llm_output.get("I_facts_list", [])
  
    # 强制校正：确保 X + Y 不超过 M (模型总事实数)
    if M > 0 and X + Y > M:
        tqdm.write(f"⚠️ 计数异常: X({X}) + Y({Y}) > M({M})。 Y已强制校正为 {M - X}。ID: {item.get('zylsh', 'N/A')}")
        Y = max(0, M - X)
      
    cfcr, fcr, fhr = calculate_metrics(N, M, X, Y)
    return {
        "CFCR": cfcr,
        "FCR": fcr,
        "FHR": fhr,
        "N": N, "M": M, "X": X, "Y": Y,
        "match_details": match_details, # 详细匹配结果
        "N_facts_list": N_facts_list,
        "I_facts_list": I_facts_list,
    }

def process_dataset(file_path, output_path, stats_output_path, client):
    """加载数据，批量处理并计算统计结果 (限制前MAX_SAMPLES条)"""
  
    # 科室统计的累加器
    dept_stats = defaultdict(lambda: {"N_total": 0, "M_total": 0, "X_total": 0, "Y_total": 0, "count": 0})
  
    # 整体统计的累加器
    overall_stats = {"N_total": 0, "M_total": 0, "X_total": 0, "Y_total": 0, "count": 0}
  
    # 逐行读取和处理数据
    with open(file_path, 'r', encoding='utf-8') as infile, open(output_path, 'w', encoding='utf-8') as outfile:
        # 使用 tqdm 包装迭代器以显示进度条，总数为 MAX_SAMPLES
        for i, line in enumerate(tqdm(infile, total=MAX_SAMPLES, desc="📊 正在处理样本")):
            if i >= MAX_SAMPLES:
                break # 达到限制，退出循环
          
            try:
                item = json.loads(line)
              
                # --- 提取关键字段 ---
                item_id = item.get("zylsh", "N/A")
                department = item.get("科室", "未知科室")
              
                # --- 调用处理函数 ---
                metrics_data = process_single_item(item, client)
              
                # --- 收集和保存结果 ---
                item_result = {
                    "id": item_id,
                    "科室": department,
                    "input_data": {
                        "new_summary": item.get("new_summary", ""),
                        "output": item.get("output", ""),
                        "instruction_snippet": item.get("instruction", "")[:50] + "...",
                    },
                    "metrics": metrics_data
                }
              
                # 写入结果文件
                outfile.write(json.dumps(item_result, ensure_ascii=False) + '\n')
              
                # --- 累加统计 ---
                # 安全提取 N, M, X, Y，确保为 int
                N = safe_int_convert(metrics_data.get("N", 0))
                M = safe_int_convert(metrics_data.get("M", 0))
                X = safe_int_convert(metrics_data.get("X", 0))
                Y = safe_int_convert(metrics_data.get("Y", 0))
                
                # 仅对模型返回有效事实数的样本进行统计
                if M > 0 or N > 0:
                    # 科室统计
                    dept_stats[department]["N_total"] += N
                    dept_stats[department]["M_total"] += M
                    dept_stats[department]["X_total"] += X
                    dept_stats[department]["Y_total"] += Y
                    dept_stats[department]["count"] += 1
                    # 整体统计
                    overall_stats["N_total"] += N
                    overall_stats["M_total"] += M
                    overall_stats["X_total"] += X
                    overall_stats["Y_total"] += Y
                    overall_stats["count"] += 1
            except json.JSONDecodeError:
                tqdm.write(f"❌ 忽略行: JSON格式错误 - {line.strip()}")
            except Exception as e:
                tqdm.write(f"❌ 处理样本 {item.get('zylsh', 'N/A')} 时发生未知错误: {e}")
    
    # 新增：计算并保存统计结果到文件
    overall_final = {
        "title": "整体统计",
        "N_total": overall_stats["N_total"],
        "M_total": overall_stats["M_total"],
        "X_total": overall_stats["X_total"],
        "Y_total": overall_stats["Y_total"],
        "count": overall_stats["count"],
        "CFCR": calculate_metrics(overall_stats["N_total"], overall_stats["M_total"], overall_stats["X_total"], overall_stats["Y_total"])[0],
        "FCR": calculate_metrics(overall_stats["N_total"], overall_stats["M_total"], overall_stats["X_total"], overall_stats["Y_total"])[1],
        "FHR": calculate_metrics(overall_stats["N_total"], overall_stats["M_total"], overall_stats["X_total"], overall_stats["Y_total"])[2]
    }
    
    dept_final = {
        "title": "科室统计",
        "departments": {}
    }
    for dept, stats in dept_stats.items():
        if stats["count"] > 0:
            cfcr, fcr, fhr = calculate_metrics(stats["N_total"], stats["M_total"], stats["X_total"], stats["Y_total"])
            dept_final["departments"][dept] = {
                "N_total": stats["N_total"],
                "M_total": stats["M_total"],
                "X_total": stats["X_total"],
                "Y_total": stats["Y_total"],
                "count": stats["count"],
                "CFCR": cfcr,
                "FCR": fcr,
                "FHR": fhr
            }
    
    final_stats = {
        "overall": overall_final,
        "departments": dept_final["departments"]
    }
    
    with open(stats_output_path, 'w', encoding='utf-8') as stats_file:
        json.dump(final_stats, stats_file, ensure_ascii=False, indent=2)
    
    print(f"📁 统计结果已保存至: {stats_output_path}")
    
    return overall_stats, dept_stats

def print_statistics(stats_dict, title):
    """格式化并打印统计结果"""
    print(f"\n--- {title} 统计结果 ({stats_dict['count']}个样本) ---")
  
    N = stats_dict["N_total"]
    M = stats_dict["M_total"]
    X = stats_dict["X_total"]
    Y = stats_dict["Y_total"]
  
    cfcr, fcr, fhr = calculate_metrics(N, M, X, Y)
  
    print(f"总 Gold 事实数 (N): {N}")
    print(f"总 Model 事实数 (M): {M}")
    print(f"总 核心匹配数 (X): {X}")
    print(f"总 指令匹配数 (Y): {Y}")
    print("----------------------------------------")
    print(f"✅ 核心事实覆盖率 (CFCR = X/N): {cfcr:.4f}")
    print(f"✅ 事实符合率 (FCR = (X+Y)/M): {fcr:.4f}")
    print(f"✅ 事实幻觉率 (FHR = (M-X-Y)/M): {fhr:.4f}")

def print_department_stats(dept_stats):
    """打印按科室分组的统计结果"""
    print("\n--- 🏥 按科室分组统计结果 ---")
  
    table_data = []
  
    for dept, stats in dept_stats.items():
        if stats["count"] == 0:
            continue
      
        N, M, X, Y = stats["N_total"], stats["M_total"], stats["X_total"], stats["Y_total"]
        cfcr, fcr, fhr = calculate_metrics(N, M, X, Y)
      
        table_data.append({
            "科室": dept,
            "样本数": stats["count"],
            "CFCR": f"{cfcr:.4f}",
            "FCR": f"{fcr:.4f}",
            "FHR": f"{fhr:.4f}",
        })
      
    # 格式化输出为 Markdown 表格
    if table_data:
        table_data.sort(key=lambda x: x['样本数'], reverse=True)
      
        header = ["科室", "样本数", "CFCR", "FCR", "FHR"]
        print("| " + " | ".join(header) + " |")
        print("|" + "---|"*len(header))
      
        for row in table_data:
            print(f"| {row['科室']} | {row['样本数']} | {row['CFCR']} | {row['FCR']} | {row['FHR']} |")
    else:
        print("无科室数据可供统计。")

# --- 主程序入口 ---
if __name__ == "__main__":
  
    print(f"🚀 正在启动事实比对计算。文件: {FILE_PATH}")
    print(f"模型: {MODEL_NAME} | 限制样本数: {MAX_SAMPLES}")
    print("---------------------------------------------------------")
    overall_stats, dept_stats = process_dataset(FILE_PATH, OUTPUT_FILE_PATH, STATS_OUTPUT_PATH, client)
    # 1. 整体计算值
    print_statistics(overall_stats, "总 体")
  
    # 2. 按科室分组计算值
    print_department_stats(dept_stats)
  
    print(f"\n🎉 样本处理完毕。详细匹配结果已保存至 {OUTPUT_FILE_PATH}")




# 所有的数据
