import openai
import json

client = openai.OpenAI(
    api_key="emr",
    base_url="http://172.20.137.82:8898/v1"
)

input_file = "/root/nas/llm_models/qwen3-paper-45k/paper_test_set.jsonl"
output_file = "/root/nas/瑞金/test_set//model_output.jsonl"

with open(input_file, "r", encoding="utf-8") as f_in, \
     open(output_file, "w", encoding="utf-8") as f_out:
    
    for idx, line in enumerate(f_in, start=1):
        record = json.loads(line)

        # 直接用 instruction 字段
        content = record.get("instruction", "")

        completion = client.chat.completions.create(
            model="Qwen3-8B-paper-45k-final",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": content}
            ],
            max_tokens=2048,
            temperature=0.7,
            top_p=0.9,
            extra_body={
                "stop_token_ids": [151644, 151645, 151643],
                "chat_template_kwargs": {"enable_thinking": False},
            },
        )

        result = completion.choices[0].message.content.strip()

        # 打印到控制台
        print(f"\n==== 记录 {idx} ====")
        # print(f"[Instruction] {content}")
        print(f"[Output] {result}")

        # 在原记录基础上加上 output 字段
        record["model_output"] = result

        # 写入结果文件
        f_out.write(json.dumps(record, ensure_ascii=False) + "\n")