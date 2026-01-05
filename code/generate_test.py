import asyncio
import json
from openai import AsyncOpenAI

# 用于全局进度计数
progress = {
    "total": 0,
    "done": 0
}
progress_lock = asyncio.Lock()  # 确保多协程安全更新

async def chat_model(client, user_prompt, semaphore, progress_callback=None):
    """
    异步地向API发送单个请求。
    使用信号量（semaphore）来控制同时进行的请求数量。
    """
    async with semaphore:
        try:
            completion = await client.chat.completions.create(
                # model="Qwen3-8B",
                model="qwen3-8b-gen-newprompt",
                messages=[
                    {"role": "system", "content": ""},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2048,
                temperature=0.1,
                top_p=0.9,
                extra_body={
                    "stop_token_ids": [151644, 151645, 151643],
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            )
            response = completion.choices[0].message.content
        except Exception as e:
            print(f"处理prompt时发生错误: '{user_prompt[:50]}...'. 错误信息: {e}")
            response = f"错误: {e}"

        # 更新进度
        if progress_callback:
            await progress_callback()
        return response


def save_json(data, dir):
    """将数据保存为JSON文件。"""
    with open(dir, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"数据已保存到 {dir}")


async def update_progress():
    """更新并显示进度"""
    async with progress_lock:
        progress["done"] += 1
        print(f"进度: {progress['done']} / {progress['total']}")


async def process_category(client, semaphore, data_list, category_name):
    """
    为指定类别的数据列表创建并运行并发任务。
    """
    tasks = []
    for data in data_list:
        tasks.append(chat_model(client, data["instruction"], semaphore, update_progress))

    model_responses = await asyncio.gather(*tasks)

    for data, summary in zip(data_list, model_responses):
        data["summary"] = summary
    
    output_path = f"/root/nas/瑞金/EMR-Paper-data/1117generate/1117—{category_name}.json"
    save_json(data_list, output_path)


async def main():
    """主函数，负责加载数据、初始化客户端并编排整个并发处理流程。"""
    test_data_dir = "/root/nas/瑞金/EMR-Paper-data/1117generate/251028-generate-test-modified.jsonl"
    
    categorized_data = {
        "yyjy": [], 
        "bcyzlqk": [], 
        "jbxx": [], 
        "cysqk": []
    }
    key_to_category = {
        "出院后用药建议": "yyjy",
        "病程与治疗情况": "bcyzlqk",
        "患者基本信息": "jbxx",
        "出院时情况": "cysqk"
    }
    with open(test_data_dir, "r", encoding="utf-8") as f:
        for line in f:
            line_data = json.loads(line)
            category = key_to_category.get(line_data["key"])
            if category:
                categorized_data[category].append(line_data)

    # 设置总任务数
    progress["total"] = sum(len(v) for v in categorized_data.values())
    progress["done"] = 0
    print(f"总任务数: {progress['total']}")

    CONCURRENCY_LIMIT = 32
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)


    client = AsyncOpenAI(
        api_key="emr",
        base_url=" "
    )

    processing_tasks = []
    for category_name, data_list in categorized_data.items():
        if data_list:
            processing_tasks.append(
                process_category(client, semaphore, data_list, category_name)
            )
    
    await asyncio.gather(*processing_tasks)
    print("全部任务完成 ✅")


if __name__ == "__main__":
    asyncio.run(main())
