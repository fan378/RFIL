# -*- coding: utf-8 -*-
import os
import json
import base64
from PIL import Image
from datetime import datetime
from openai import OpenAI
import time

# ----------- 配置参数 -----------
base_url = "http://113.59.64.93:8085/v1"
api_key = "111"
model = "qwen2.5-vl-72b-instruct-awq"

prompt = (
    "你是一名医生助手，请识别这张医疗图片中的所有字段，并按图片中的结构提取信息。请严格分三步输出：\n\n"
    "⚠️ 特别注意：\n"
    "1. 在图像最顶部（与手术记录单处于同一水平线）可能有一个\"左肩 / 右肩\"的勾选框，请务必识别，并准确记录在结果中；\n"
    "2. 在图像底部通常有几个重要字段，包括“其他”、“主要手术”、“记录者”和“日期”，这些字段如有，请务必提取并写入结果中；\n"
    "【第一步】只提取字段结构及空白内容，输出字段层级和布局，字段值为空，格式为 JSON；\n"
    "【第二步】基于上述字段结构，如果图片中未填写或为空，请你基于医学常识合理虚构补全，输出完整填写的 JSON；\n"
    "【第三步】基于第二步的填写内容，请用连贯自然的语言生成三段描述，分别对应：患者基本信息、术中发现、手术过程。"
    "每段描述应当是自然通顺、内容完整的段落，而非简单罗列字段，语言应流畅、医学合理，适合直接用于正式手术记录文本。\n\n"
    "请使用结构化 JSON 输出，格式为：\n"
    "{\n"
    "  \"empty_template\": {...},\n"
    "  \"filled_data\": {...},\n"
    "  \"generated_text\": {\n"
    "     \"基本信息\": \"患者李四，男，32岁，于2024年5月6日因右肩关节损伤在运动医学科病区行右肩关节镜手术。手术由王医生主刀，病案号未明确，住院号ZY20240506001，床号23床，手术时间为14:10-16:00，采用全麻，入路包括后正中、后外、前下、外上，辅助通道为Nevasport通道。\",\n"
    "     \"术中发现\": \"术中发现患者前下盂唇存在Bankart损伤，后下盂唇有隐性撕裂，伴Ⅱ型上盂唇SLAP损伤及关节囊冗余。肩胛盂有起效弧缺损约20%，肱骨头骨缺损距冈下肌止点5至10毫米。肱二头肌腱鞘增厚伴炎症，肩峰下滑囊轻度粘连。\",\n"
    "     \"手术过程\": \"手术经后正中、后外、前下、外上入路建立关节腔，行Bankart修复并缝合3枚锚钉，前下盂肱韧带紧缩成形术，肱二头肌腱鞘松解。切除肩峰前骨赘，行肩峰下减压及滑囊清理，冈上肌腱部分修复缝合2枚锚钉，关节腔全面冲洗后置入引流管。手术过程顺利，效果满意。\"\n"
    "  }\n"
    "}"
)


# ----------- 工具函数 -----------

def compress_image(input_path, output_path, quality=50, max_size=(1600, 1600)):
    """压缩图片"""
    with Image.open(input_path) as img:
        img.thumbnail(max_size)
        img.convert("RGB").save(output_path, "JPEG", quality=quality)

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def generate_data(prompt, image_path):
    ext = os.path.splitext(image_path)[1].lower()[1:]
    client = OpenAI(api_key=api_key, base_url=base_url)
    b64 = encode_image(image_path)
    completion = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/{ext};base64,{b64}"}},
                {"type": "text", "text": prompt}
            ]
        }]
    )
    return completion.choices[0].message.content

def extract_three_parts(text):
    json_blocks = []
    stack = []
    start_idx = None
    for i, char in enumerate(text):
        if char == '{':
            if not stack:
                start_idx = i
            stack.append('{')
        elif char == '}':
            if stack:
                stack.pop()
                if not stack:
                    json_blocks.append(text[start_idx:i+1])
    if not json_blocks:
        raise ValueError("未提取到 JSON")
    return json.loads(json_blocks[0])

def save_all(data: dict, base_name: str) -> list:
    os.makedirs("output7.26", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = []

    # 空白模板
    p1 = os.path.join("output7.26", f"{base_name}_空白模板_{ts}.json")
    with open(p1, "w", encoding="utf-8") as f:
        json.dump(data.get("empty_template", {}), f, ensure_ascii=False, indent=2)
    paths.append(p1)

    # 虚构填写
    p2 = os.path.join("output7.26", f"{base_name}_虚构填写_{ts}.json")
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(data.get("filled_data", {}), f, ensure_ascii=False, indent=2)
    paths.append(p2)

    # 文本描述
    p3 = os.path.join("output7.26", f"{base_name}_文本描述_{ts}.txt")
    with open(p3, "w", encoding="utf-8") as f:
        for k, v in data.get("generated_text", {}).items():
            f.write(f"【{k}】\n{v}\n\n")
    paths.append(p3)

    return paths

# ----------- 主流程 -----------
def main(image_path):
    start_time = time.time()
    print("压缩图片中...")
    compressed_path = "temp_compressed.jpg"
    compress_image(image_path, compressed_path)

    print("识别图像中...")
    text = generate_data(prompt, compressed_path)

    print("解析返回内容...")
    data = extract_three_parts(text)

    print("保存文件中...")
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    paths = save_all(data, base_name)

    print("处理完成，生成以下文件：")
    for p in paths:
        print("✅", p)

    print(f"总耗时：{time.time() - start_time:.2f} 秒")

if __name__ == "__main__":
    image_file = "/root/nas/六院/新端口/肩关节.jpg"  # 修改为你的图片路径
    main(image_file)
