import json

input_file = "/root/nas/瑞金/test_set/zhongyike/test.jsonl"
output_file = "/root/nas/瑞金/test_set/zhongyike/only_output.jsonl"

with open(input_file, "r", encoding="utf-8") as f_in, \
     open(output_file, "w", encoding="utf-8") as f_out:
    
    for idx, line in enumerate(f_in, start=1):
        record = json.loads(line)
        output_text = record.get("output", "")

        # 打印到控制台
        print(f"记录 {idx}: {output_text}")

        # 只写出 output
        f_out.write(json.dumps({"output": output_text}, ensure_ascii=False) + "\n")

print(f"\n已完成 ✅ 提取结果保存到 {output_file}")
