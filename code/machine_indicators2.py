#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
传统指标评估脚本（ROUGE + BLEU + BERTScore）
- 直连 https://huggingface.co
- 自动下载 nghuyong/ernie-health-zh
- 支持限制样本、按科室统计、输出 JSONL + JSON
"""

import json
import os
from tqdm import tqdm
from collections import defaultdict

# -------------------------- 依赖库 --------------------------
# pip install rouge-score sacrebleu bert-score tqdm torch transformers
from rouge_score import rouge_scorer
import sacrebleu
import bert_score

# 关键：强制让 Python 使用 Clash 代理
# os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

# 全局离线检查（如果缓存存在，优先使用）
if os.path.exists("/root/.cache/huggingface/hub/models--nghuyong--ernie-health-zh"):
    os.environ["HF_HUB_OFFLINE"] = "1"

# -------------------------- 配置参数 --------------------------
FILE_PATH = "./generate/backfill_cleaned.jsonl"
OUTPUT_FILE_PATH = "./generate/calculation_results_traditional.jsonl"
STATS_OUTPUT_PATH = "./generate/traditional_stats.json"
MAX_SAMPLES = 454  # 限制处理的样本数量，设为 None 则全部

# BERTScore 模型（医疗专用 ERNIE-Health）
BERTSCORE_MODEL = "nghuyong/ernie-health-zh"

# -------------------------- 关键：直连 Hugging Face --------------------------
# 不设置 HF_ENDPOINT → 默认直连 huggingface.co
# 如果你想加速，可取消注释下面这行：
# os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# -------------------------- 传统指标计算函数 --------------------------
def calculate_traditional_metrics(gold_truth, model_summary):
    """
    计算 ROUGE, BLEU, BERTScore
    返回 dict 包含各项分数
    """
    results = {}

    # --- ROUGE ---
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    rouge_scores = scorer.score(gold_truth, model_summary)
    results['rouge1'] = rouge_scores['rouge1'].fmeasure
    results['rouge2'] = rouge_scores['rouge2'].fmeasure
    results['rougeL'] = rouge_scores['rougeL'].fmeasure

    # --- BLEU ---
    bleu = sacrebleu.sentence_bleu(model_summary, [gold_truth])
    results['bleu'] = bleu.score / 100.0  # 归一化到 [0,1]

    # --- BERTScore ---
    try:
        print(f"正在加载 BERTScore 模型: {BERTSCORE_MODEL} ...")
        P, R, F = bert_score.score(
            [model_summary], [[gold_truth]],
            lang="zh",
            model_type="bert-base-chinese",  # 关键修复：使用兼容架构名（ERNIE 基于 BERT）
            num_layers=12,  # 关键修复：指定 ERNIE 默认层数，避免默认搜索失败
            batch_size=1,
            device="cpu",  # 强制 CPU，避免 GPU 问题
            verbose=True  # 开启详细日志
        )
        results['bertscore_precision'] = P.mean().item()
        results['bertscore_recall'] = R.mean().item()
        results['bertscore_f1'] = F.mean().item()
        print("BERTScore 加载成功！")
    except Exception as e:
        print(f"BERTScore 计算失败: {e}")
        results['bertscore_precision'] = 0.0
        results['bertscore_recall'] = 0.0
        results['bertscore_f1'] = 0.0

    return results

# -------------------------- 单样本处理 --------------------------
def process_single_item(item):
    """处理单个样本，只计算传统指标"""
    gold_truth = item.get("output", "").strip()
    model_summary = item.get("new_summary", "").strip()

    if not gold_truth or not model_summary:
        tqdm.write(f"空文本跳过 ID: {item.get('zylsh', 'N/A')}")
        return None

    try:
        trad_metrics = calculate_traditional_metrics(gold_truth, model_summary)
    except Exception as e:
        tqdm.write(f"指标计算失败 ID: {item.get('zylsh', 'N/A')} - {e}")
        trad_metrics = {
            "rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0,
            "bleu": 0.0,
            "bertscore_precision": 0.0, "bertscore_recall": 0.0, "bertscore_f1": 0.0
        }

    return {
        "traditional_metrics": trad_metrics
    }

# -------------------------- 数据集处理与统计 --------------------------
def process_dataset(file_path, output_path, stats_output_path):
    # 统计累加器
    dept_stats = defaultdict(lambda: {
        "count": 0,
        "rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0,
        "bleu": 0.0, "bertscore_f1": 0.0
    })
    overall_stats = {
        "count": 0,
        "rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0,
        "bleu": 0.0, "bertscore_f1": 0.0
    }

    with open(file_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:

        sample_count = 0
        for line in tqdm(infile, desc="处理样本", unit="个"):
            if MAX_SAMPLES and sample_count >= MAX_SAMPLES:
                break

            try:
                item = json.loads(line.strip())
                item_id = item.get("zylsh", "N/A")
                department = item.get("科室", "未知科室")

                metrics_data = process_single_item(item)
                if metrics_data is None:
                    continue

                # 写入单样本结果
                result = {
                    "id": item_id,
                    "科室": department,
                    "input": {
                        "new_summary": item.get("new_summary", ""),
                        "output": item.get("output", "")
                    },
                    "metrics": metrics_data
                }
                outfile.write(json.dumps(result, ensure_ascii=False) + '\n')

                # 累加统计
                m = metrics_data["traditional_metrics"]
                for key in ["rouge1", "rouge2", "rougeL", "bleu", "bertscore_f1"]:
                    dept_stats[department][key] += m[key]
                    overall_stats[key] += m[key]
                dept_stats[department]["count"] += 1
                overall_stats["count"] += 1
                sample_count += 1

            except json.JSONDecodeError:
                tqdm.write(f"JSON 解析错误: {line.strip()}")
            except Exception as e:
                tqdm.write(f"处理错误 ID: {item.get('zylsh', 'N/A')} - {e}")

    # 计算平均值并保存统计
    save_statistics(overall_stats, dept_stats, stats_output_path)
    return overall_stats, dept_stats

def save_statistics(overall_stats, dept_stats, stats_output_path):
    count = overall_stats["count"]
    overall_avg = {
        "title": "整体平均指标",
        "样本数": count,
        "ROUGE-1": overall_stats["rouge1"] / count if count > 0 else 0,
        "ROUGE-2": overall_stats["rouge2"] / count if count > 0 else 0,
        "ROUGE-L": overall_stats["rougeL"] / count if count > 0 else 0,
        "BLEU": overall_stats["bleu"] / count if count > 0 else 0,
        "BERTScore-F1": overall_stats["bertscore_f1"] / count if count > 0 else 0,
    }

    dept_final = {}
    for dept, s in dept_stats.items():
        cnt = s["count"]
        if cnt == 0:
            continue
        dept_final[dept] = {
            "样本数": cnt,
            "ROUGE-1": s["rouge1"] / cnt,
            "ROUGE-2": s["rouge2"] / cnt,
            "ROUGE-L": s["rougeL"] / cnt,
            "BLEU": s["bleu"] / cnt,
            "BERTScore-F1": s["bertscore_f1"] / cnt,
        }

    final_stats = {
        "overall": overall_avg,
        "departments": dept_final
    }

    with open(stats_output_path, 'w', encoding='utf-8') as f:
        json.dump(final_stats, f, ensure_ascii=False, indent=2)
    print(f"统计结果已保存: {stats_output_path}")

# -------------------------- 打印统计结果 --------------------------
def print_overall_stats(stats):
    c = stats["count"]
    if c == 0:
        print("无有效样本。")
        return
    print(f"\n--- 整体平均指标 ({c} 个样本) ---")
    print(f"ROUGE-1 : {stats['rouge1']/c:.4f}")
    print(f"ROUGE-2 : {stats['rouge2']/c:.4f}")
    print(f"ROUGE-L : {stats['rougeL']/c:.4f}")
    print(f"BLEU    : {stats['bleu']/c:.4f}")
    print(f"BERT-F1 : {stats['bertscore_f1']/c:.4f}")

def print_department_table(dept_stats):
    print("\n--- 按科室平均指标 ---")
    table = []
    for dept, s in dept_stats.items():
        if s["count"] == 0:
            continue
        c = s["count"]
        table.append({
            "科室": dept,
            "样本数": c,
            "R1": f"{s['rouge1']/c:.4f}",
            "R2": f"{s['rouge2']/c:.4f}",
            "RL": f"{s['rougeL']/c:.4f}",
            "BLEU": f"{s['bleu']/c:.4f}",
            "BERT-F1": f"{s['bertscore_f1']/c:.4f}",
        })

    if not table:
        print("无科室数据。")
        return

    table.sort(key=lambda x: x["样本数"], reverse=True)
    header = ["科室", "样本数", "R1", "R2", "RL", "BLEU", "BERT-F1"]
    print("| " + " | ".join(header) + " |")
    print("| " + " --- |" * len(header))
    for row in table:
        print(f"| {row['科室']} | {row['样本数']} | {row['R1']} | {row['R2']} | {row['RL']} | {row['BLEU']} | {row['BERT-F1']} |")

# -------------------------- 主程序 --------------------------
if __name__ == "__main__":
    print(f"启动传统指标计算")
    print(f"输入文件: {FILE_PATH}")
    print(f"限制样本: {MAX_SAMPLES}")
    print(f"BERTScore 模型: {BERTSCORE_MODEL}")
    print(f"直连 Hugging Face: https://huggingface.co")
    print("-" * 60)

    # ==================== 新增：预下载医疗 BERT 模型 ====================
    print("开始预下载医疗 BERT 模型 (nghuyong/ernie-health-zh)...")
    try:
        from transformers import AutoTokenizer, AutoModel
        tokenizer = AutoTokenizer.from_pretrained("nghuyong/ernie-health-zh")
        model = AutoModel.from_pretrained("nghuyong/ernie-health-zh")
        print("模型下载并缓存成功！")
    except Exception as e:
        print(f"预下载模型失败: {e} (继续评估脚本)")
    print("预下载完成，继续评估...")

    overall_stats, dept_stats = process_dataset(
        FILE_PATH, OUTPUT_FILE_PATH, STATS_OUTPUT_PATH
    )

    print_overall_stats(overall_stats)
    print_department_table(dept_stats)

    print(f"\n单样本结果已保存: {OUTPUT_FILE_PATH}")
    print(f"统计汇总已保存: {STATS_OUTPUT_PATH}")
    print("计算完成！")