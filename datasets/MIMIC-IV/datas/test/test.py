import json
import os
from transformers import AutoTokenizer
from tqdm import tqdm


JSONL_PATH = "/home/ecust/workspace/EMR-Draft/data/post_discharge_medication_advice_instructions_cleaned2.jsonl"
MODEL_NAME = "/home/ecust/LLMs/Qwen3-8B-nothinking"

# token 数小于 THRESHOLD 的样本会被计数并导出
THRESHOLD = 10000

# 导出路径
OUTPUT_JSONL_PATH = "/home/ecust/workspace/EMR-Draft/data/251028-generate-train-lim10k.jsonl"


def count_lines(file_path):
    with open(file_path, 'rb') as f:
        return sum(1 for _ in f)

def main():
    print(f"Loading tokenizer from: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

    if not os.path.exists(JSONL_PATH):
        raise FileNotFoundError(f"JSONL file not found: {JSONL_PATH}")

    total_lines = count_lines(JSONL_PATH)
    token_lengths = []
    small_count = 0

    out_dir = os.path.dirname(OUTPUT_JSONL_PATH)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(OUTPUT_JSONL_PATH, 'w', encoding='utf-8') as fout, \
         open(JSONL_PATH, 'r', encoding='utf-8') as fin:

        for line in tqdm(fin, total=total_lines, desc="Tokenizing", unit="line"):
            raw = line.rstrip("\n")
            if not raw.strip():
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            text_parts = []
            for key in ["instruction", "input", "output"]:
                val = data.get(key, "")
                if isinstance(val, str):
                    text_parts.append(val)
                elif val is None:
                    continue
                else:
                    text_parts.append(str(val))
            text = "".join(text_parts)

            # 计算 token 数
            try:
                tokens = tokenizer.encode(text, add_special_tokens=False)
            except Exception as e:
                continue

            tok_len = len(tokens)
            token_lengths.append(tok_len)

            # 若小于阈值，写入到导出 jsonl
            if tok_len < THRESHOLD:
                small_count += 1
                # 保持与原始行一致（避免字段顺序被打乱）
                fout.write(raw + "\n")

    if not token_lengths:
        print("No valid entries processed.")
        return

    max_len = max(token_lengths)
    min_len = min(token_lengths)
    avg_len = sum(token_lengths) / len(token_lengths)

    print("\n" + "="*50)
    print("长度统计")
    print("="*50)
    print(f"File: {JSONL_PATH}")
    print(f"Total samples processed: {len(token_lengths)}")
    print(f"最长: {max_len}")
    print(f"最短: {min_len}")
    print(f"平均: {avg_len:.2f}")
    print(f"\n阈值: {THRESHOLD} tokens")
    print(f"小于阈值的数量: {small_count}")
    ratio = (small_count / len(token_lengths) * 100) if token_lengths else 0.0
    print(f"占比: {ratio:.2f}%")
    print(f"已导出到: {OUTPUT_JSONL_PATH}")
    print("="*50)

if __name__ == "__main__":
    main()
