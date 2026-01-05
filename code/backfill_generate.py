# 有instruction
import json
import os
import asyncio
from tqdm import tqdm
from openai import AsyncOpenAI
import aiofiles
import re


INPUT_FILE = "./fill-test-updated.jsonl"
OUTPUT_FILE = "./llama3.jsonl"
TEMP_FILE = OUTPUT_FILE + ".tmp"  # 临时文件用于断点续跑
# MODEL = "Qwen3-1.7B-sft-v1-672"
MODEL = "llama3-1b-fill"
CONCURRENCY = 5  # 并发数，可按机器性能调高

# 只处理以下科室
TARGET_DEPTS = {"乳腺外科", "甲状腺血管外科", "肿瘤科", "中医科", "妇科"}

client = AsyncOpenAI(
    api_key="emr",  # 不需要真实 key
    base_url=" "

)

# ========== 去除 <think>...</think> 的清洗函数 ==========
def clean_think_tags(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"\n\s*\n", "\n", text).strip()
    return text


# ========== 系统提示词 ==========
SYSTEM_PROMPT = """你是一名经验丰富的医疗文本智能助手，擅长根据上下文逻辑和临床常识，
对带有占位符（格式为$...$）的出院小结进行智能回填。

$任务目标$
请根据语义补全这些占位符，使文本自然流畅，语义连贯，符合医学常识与书写规范。

$回填原则$
1. **语义合理性**：
   - 回填内容需临床合理（例如术后拆线时间一般为5-7日或3日等；复查为术后1周或1月）。
2. **隐私与虚构**：
   - 所有回填数据均为虚构，不得涉及真实人物或隐私信息。
3. **格式与一致性**：
   - 保留原文 summary 的编号、换行、标点、语气，不重写句子结构。(尤其是一定要保留换行)
   - 多次出现的同类占位符，回填内容保持一致。
4. **医生/护士/签名类占位符**：
   - 若占位符包含“医生”“护士”“主任”“签名”等职业词汇，请保留原样，不替换。
5. **输出要求**：
   - 仅输出回填后的完整纯文本，不要附加任何解释、提示或额外说明。
"""

# ========== Few-Shot 样例 ==========
FEW_SHOTS = [
    {
        "input": "1、请至血液科门诊随访。如有不适，请及时就诊。\n2、$门诊时间$中医科$医生$主任专家门诊，需预约。\n3、中医科电话：$电话$。\n4、血液科专家门诊时间：$医生$主任，$血液科专家门诊时间$；$医生$主任，$血液科专家门诊时间$；$医生$主任，$血液科专家门诊时间$。可预约。",
        "output": "1、请至血液科门诊随访。如有不适，请及时就诊。\n2、每周三下午、周五上午中医科$医生$主任专家门诊，需预约。\n3、中医科电话：021-34187827。 \n4、血液科专家门诊时间：$医生$主任，周二上午、周三下午；$医生$主任，周一下午；$医生$主任，周四下午。可预约。"
    },
    {
        "input": "1、我科及相关科室门诊随访，如有不适，及时处理。\n2、出院后$复查时间$复查血常规、肝肾功能电解质，下次化疗时间：$待化疗时间$。\n3、避风寒，节饮食，畅情志，免劳累。\n4、出院带药：云芝糖肽胶囊*3盒（每天3次，每次3粒，口服）；平消胶囊*4盒（每日3次，每次4粒，口服）；复方斑蝥胶囊*3盒（每天3次，每次4粒，口服），思诺思*1盒（每天1粒，睡前口服）",
        "output": "1、我科及相关科室门诊随访，如有不适，及时处理。\n2、出院后1周复查血常规、肝肾功能电解质，下次化疗时间：2019-07-06。 \n3、避风寒，节饮食，畅情志，免劳累。\n4、出院带药：云芝糖肽胶囊*3盒（每天3次，每次3粒，口服）；平消胶囊*4盒（每日3次，每次4粒，口服）；复方斑蝥胶囊*3盒（每天3次，每次4粒，口服），思诺思*1盒（每天1粒，睡前口服） 。"
    },
    {
        "input": "1、注意营养与休息，禁盆浴及性生活$禁房事或盆浴时间$。\n2、$待病理报告时间$电话询问病理结果$妇科查询病理报告电话$。\n3、$复查时间$妇科门诊复查携出院小结。\n4、注意住院期间异常的化验检查结果，定期内外科复查随访。",
        "output": "1、注意营养与休息，禁盆浴及性生活3个月。\n2、术后10天电话询问病理报告64370045*602168。\n3、术后1月妇科门诊复查携出院小结。\n4、注意住院期间异常的化验检查结果，定期内外科复查随访。"
    },
    {
        "input": "1、注意饮食和休息。\n2、出院后$复查时间$复查血常规，若WBC小于3*10-9/L，或NE小于1.5*10-9/L，予以升白治疗。\n3、肿瘤科门诊随访，不适随诊。",
        "output": "1、注意饮食和休息。\n2、出院后一周复查血常规，若WBC小于3*10-9/L，或NE小于1.5*10-9/L，予以升白治疗。\n3、肿瘤科门诊随访，不适随诊"
    },
    {
        "input": "1、$待病理报告时间$来院询问石蜡病理报告，并带至$医生$医师门诊就诊，拟定进一步诊疗或随访方案。\n2、术后胸带加压包扎切口$包扎时间$，之后可佩戴文胸；保持伤口清洁干燥，$禁止洗澡时间$避免洗澡；术后$换药时间$来院换药一次，换药门诊时间：$门诊时间$。\n3、保持伤口清洁干燥，如有发热，切口局部红肿、疼痛、化脓等不适，及时来院就诊。\n4、术后康复指导详见专页。\n5、患者住院期间：心电图示窦性心动过缓，建议心内科随访。",
        "output": "1、10个工作日后来院询问石蜡病理报告，并带至$医生$医师门诊就诊，拟定进一步诊疗或随访方案。\n2、术后胸带加压包扎切口5-7天，之后可佩戴文胸；保持伤口清洁干燥，2周内避免洗澡；术后10天内每3天来院换药一次，换药门诊时间：每周一～周五9:00-11:00门诊大楼3楼乳腺外科。\n3、保持伤口清洁干燥，如有发热，切口局部红肿、疼痛、化脓等不适，及时来院就诊。\n4、术后康复指导详见专页。\n5、患者住院期间：心电图示窦性心动过缓，建议心内科随访。"
    },
    {
        "input": "1、注意休息，合理营养，低碘饮食，防止感染。\n2、术后$待拆线时间$拆线，病房$拆线服务时间$提供拆线服务。术后$待病理报告时间$致电$电话$询问石蜡病理报告；石蜡病理结果可能与目前诊断不符，最终诊断以石蜡病理为准；\n3、出院带药：优甲乐100片、钙尔奇30片，遵医嘱服用。\n4、$随访时间$后门诊随访复查甲状腺功能，调整用药。\n5、定期外科门诊随访，如有切口疼痛、发热等不适，及时就诊。\n6、如遇特殊情况，石蜡病理需进一步行基因检测或免疫组化，病理科可能要求再次缴费，敬请理解。",
        "output": "1、注意休息，合理营养，低碘饮食，防止感染。\n2、术后5-6日拆线，病房每周二、四、六上午9-10点提供拆线服务。术后10日致电64370045*666659询问石蜡病理报告；石蜡病理结果可能与目前诊断不符，最终诊断以石蜡病理为准；\n3、出院带药：优甲乐100片、钙尔奇30片，遵医嘱服用。\n4、一月后门诊随访复查甲状腺功能，调整用药。\n5、定期外科门诊随访，如有切口疼痛、发热等不适，及时就诊。\n6、如遇特殊情况，石蜡病理需进一步行基因检测或免疫组化，病理科可能要求再次缴费，敬请理解。"
    }
]

# ========== 构造 Few-Shot Prompt ==========
def build_fewshot_prompt(instruction_text, summary):
    examples = "\n\n".join([
        f"$示例{i+1}$\n输入：\n{ex['input']}\n输出：\n{ex['output']}"
        for i, ex in enumerate(FEW_SHOTS)
    ])
    return f"""
以下是一些参考示例：
{examples}

$病例原始上下文$：
{instruction_text}

$待回填文本$：
{summary}

请严格按照上述规则和风格，结合病例原始上下文内容，输出回填后的完整出院小结。
"""

# ========== 异步模型调用 ==========
async def call_model(instruction_text, summary, semaphore):
    prompt = build_fewshot_prompt(instruction_text, summary)
    async with semaphore:
        try:
            completion = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            raw_output = completion.choices[0].message.content.strip()
            return clean_think_tags(raw_output)
        except Exception as e:
            print(f"❌ 模型调用失败: {e}")
            return ""

# ========== 异步单条任务 ==========
async def process_item(i, item, semaphore, progress_bar):
    summary = item.get("summary", "").strip()
    instruction_text = item.get("instruction", "").strip()
    if not summary:
        item["new_summary"] = ""
    else:
        item["new_summary"] = await call_model(instruction_text, summary, semaphore)
    progress_bar.update(1)
    return item

# ========== 主流程 ==========
async def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        # data = json.load(f)
        data = [json.loads(line) for line in f if line.strip()]

    filtered_data = [item for item in data if item.get("科室") in TARGET_DEPTS]
    print(f"共筛选出 {len(filtered_data)} 条记录（目标科室: {', '.join(TARGET_DEPTS)}）")

    processed = []
    start_idx = 0
    if os.path.exists(TEMP_FILE):
        with open(TEMP_FILE, "r", encoding="utf-8") as tf:
            processed = json.load(tf)
            start_idx = len(processed)
        print(f"检测到断点文件，已处理 {start_idx} 条，将继续执行...")

    total = len(filtered_data)
    semaphore = asyncio.Semaphore(CONCURRENCY)
    progress_bar = tqdm(total=total, desc="智能回填中", initial=start_idx)

    async with aiofiles.open(OUTPUT_FILE, "a", encoding="utf-8") as wf:
        for i in range(start_idx, total):
            item = filtered_data[i]
            result = await process_item(i, item, semaphore, progress_bar)
            await wf.write(json.dumps(result, ensure_ascii=False) + "\n")
            processed.append(result)

            # 定期保存断点
            if (i + 1) % 10 == 0:
                async with aiofiles.open(TEMP_FILE, "w", encoding="utf-8") as tf:
                    await tf.write(json.dumps(processed, ensure_ascii=False, indent=2))

    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)

    progress_bar.close()
    print(f"✅ 全部完成！输出文件：{OUTPUT_FILE}")

# ========== 入口 ==========
if __name__ == "__main__":
    asyncio.run(main())
