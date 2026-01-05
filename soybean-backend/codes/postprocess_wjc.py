# 全部由模型生成结果后的后处理步骤
import csv
import numpy as np
import pandas as pd
import jsonlines
import os
import shutil
from collections import defaultdict
from copy import deepcopy
import json
import sys
import re
from tqdm import tqdm
from codes.commons.utils import load_excel_csv
from codes.commons.utils2 import generate_qwen_response, chat_with_api

#psh 新导入的包
from transformers import AutoTokenizer,AutoModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from decimal import Decimal

formats = {
    "基本信息": {
        "出院诊断": "出院诊断",
        "床号": "患者基本信息---床号",
        "科别": "患者基本信息---科别",
        "入院时间": "患者基本信息---入院时间",
        "出院时间": "患者基本信息---出院时间",
        "姓名": "患者基本信息---姓名",
        "性别": "患者基本信息---性别",
        "年龄": "患者基本信息---年龄",
        "住院号": "患者基本信息---住院号",
        "入院诊断": "患者基本信息---入院诊断"
    },
    "入院时简要病史": "患者基本信息---入院时简要病史",
    "体检摘要": "患者基本信息---体检摘要",
    "生命体征": {
        "T": "患者基本信息---体温(T)",
        "P": "患者基本信息---脉搏(P)",
        "R": "患者基本信息---呼吸(R)",
        "BP高": "患者基本信息---高压(BP高)",
        "BP低": "患者基本信息---低压(BP低)"
    },
    "住院期间医疗情况": "住院期间医疗情况",
    "出院时情况": "出院时情况",
    "病程与治疗情况": "病程与治疗情况",
    "出院后用药建议": "出院后用药建议",
    "病人信息": {
        "姓名": "患者基本信息---姓名",
        "性别": "患者基本信息---性别",
        "科室": "患者基本信息---科别",
        "床号": "患者基本信息---床号",
        "住院号": "患者基本信息---住院号",
        "住院流水号": "",
        "年龄": "患者基本信息---年龄",
        "出生年月": "",
        "入院时间": "患者基本信息---入院时间",
        "出院时间": "患者基本信息---出院时间"
    }
}

#psh 加载模型
def load_model(which_model):
    if which_model == 'model1': # 原始模型
        model_path = '/HL_user01/llm_models/chatglm3-6b'
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_path, trust_remote_code=True,device='cuda:1')
    elif which_model == 'model_wjc': # 全科室模型
        model_path = '/data/xiazhentao/System/ruijin/model/0229_ck36000_sft_stage4_lora_03-27-09-27-27_export_model'
        # model_path = '/HL_user01/trained_models/0229_ck36000_sft_stage4_lora_03-27-09-27-27_export_model'
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_path,torch_dtype=torch.float16, trust_remote_code=True,device='cuda:0')
    elif which_model == 'model_ht': # 华佗
        model_path = '/HL_user01/medical_llm/HuatuoGPT2-7b'
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_path,torch_dtype=torch.float16, trust_remote_code=True)
        
    model = model.eval()
    print('模型加载成功！')
    return model,tokenizer

#psh 过滤'科随访'
def filter_kesuifang(item):
    return "科随访" not in item

#psh 最后让模型给出院后用药建议编号
def conclude_suggestion(ori_datas,postprocess_model,postprocess_tokenizer):
    conclude="请你帮我重新给每个句子编号，编号从1开始，不要改写文本，直接输出编号整理好的文本\n需要编号的文本："

    conclusion = generate_qwen_response(postprocess_model, postprocess_tokenizer, conclude+ori_datas['出院后用药建议'], temperature=0.01)
    # print(conclusion)
    return conclusion

#psh 删除并重新添加随访建议
def process_suifang(ori_datas, ori_source,postprocess_model,postprocess_tokenizer):
    jiancha_source=ori_source['出院后用药建议']
    pattern = r'[。|;]' 
    suggestion=ori_datas['出院后用药建议']
    suggestion_list=re.split(pattern,suggestion)
    
    suggestion_list = list(filter(filter_kesuifang, suggestion_list))
    final_suggestion='。 '.join(suggestion_list)
    # print(suggestion_list)
    
    # if len(suggestion_list[0])>2:
    #     if re.match(r'\d\.',suggestion_list[0]):    
    #         suggestion_list[0]=suggestion_list[0][2:]
    # num=1

    # for s in suggestion_list:
    #     if len(s)>=6:
    #         if re.match(r'\d\.',s) or re.match(r' \d\.',s) or re.match(r'\n \d\.',s) or re.match(r'\n \d\.',s):
    #             s=s[2:]
    #         if num < len(suggestion_list):
    #             final_suggestion+=str(num)+'.'+s+'。\n'
    #         else:
    #             final_suggestion+=str(num)+'.'+s
    #         num+=1


    #print(final_suggestion)
    all_jiancha=jiancha_source[jiancha_source.find('###全部检查')+8:jiancha_source.find('###最后一个在院评估单')]
    all_jiancha=all_jiancha[:all_jiancha.find('###')]
    jiancha_list=re.split(r'报告时间',all_jiancha)
    jiancha_list=list(filter(None,jiancha_list))

    # print(jiancha_list)

    suifang_dic={}
    suifang_suggestion=final_suggestion

    for item in jiancha_list:
        item = item[item.find('描述'):]
        flag = generate_qwen_response(postprocess_model, postprocess_tokenizer, "请根据检查结果中的'图像分析'，判断下面的检查结果是否需要随访，请从['是'，'否']中选择一个输出，不要输出其他内容。\n "+item, temperature=0.01)
        # print(flag)t
        if '正常心电图' in item:
            flag='否'

        desc_match = re.search(r'描述:(.*?)(?:\n|$)', item)
        if desc_match:
            description = desc_match.group(1).split('|')[-2]
            description = description+'：'
        else:
            description = ''
        jiancha_summary= generate_qwen_response(postprocess_model, postprocess_tokenizer,"你是一位专业医生，请将下面的检查进行总结，请直接输出总结出的图像异常的检查项目和检查结果，精炼语句，将输出控制在一句话，不要提出建议\n"+item,temperature=0.01)
        jiancha_summary = jiancha_summary.replace("，随诊","").replace("，随访","")
        jiancha_summary=description + jiancha_summary
        flag = generate_qwen_response(postprocess_model, postprocess_tokenizer, "请判断下面的检查结果是否有异常，有异常输出'是',没有异常输出'否',请从['是'，'否']中选择一个输出，不要输出其他内容。\n "+ jiancha_summary, temperature=0.01)
        if '其他检查' in item or '，随诊' in item or'，随访' in item or '其他相关检查' in item :
            flag='是'
        if '明显异常' in jiancha_summary or  '未见异常' in jiancha_summary or '未发现异常' in jiancha_summary or '正常范围心电' in jiancha_summary:
            flag='否'


        if '是' in flag or flag=='需要随访。':
            rjkeshi_list="，请从下面的科室列表中选择随访科室:['心内科'，'呼吸科'，'乳腺外科'，'胰腺外科'，'消化科'，'高血压科'，'骨科'，'妇科'，'血液科'，'耳鼻喉科'，'甲状腺血管科'，'神经内科'，'神经外科'，'肾脏内科'，'内分泌科'，'胃肠外科'，'小儿科']"
            suifang_keshi= generate_qwen_response(postprocess_model, postprocess_tokenizer,"你是一位专业医生，请根据下面的检查给出对应的随访科室"+rjkeshi_list+"，请最后输出唯一随访科室名称，例如：某某科，不要输出其他内容。\n"+item, temperature=0.01)
            if(suifang_dic.get(suifang_keshi,0)):
                suifang_dic[suifang_keshi]+=jiancha_summary
            else:
                suifang_dic[suifang_keshi]=jiancha_summary
    
    for i in suifang_dic:
        jiancha_suggestion=suifang_dic[i]
        if jiancha_suggestion[-1]=='。':
            jiancha_suggestion=jiancha_suggestion[:-1]
        keshi_suggestion='，建议于'+ i +'随访。'
        suifang_suggestion = '{}{}'.format(suifang_suggestion, "患者"+jiancha_suggestion+keshi_suggestion+'\n')

    ori_datas['出院后用药建议']=suifang_suggestion

# gys 体温、呼吸、脉搏、血压处理
def extract_data(text):
    print(text)
    pattern = r'体温([\d.]+) ?°C|脉搏(\d+)次/分|呼吸(\d+)次/分|血压(\d+)/(\d+)mmHg'
    matches = re.findall(pattern, text)
    print(matches)
    # 提取匹配结果并去除None值
    results = [match for group in matches for match in group if match]
    return results
def extract_data_2(text):
    try:
        T = text.split("体温")[1].strip().split("℃")[0].strip()
        P = text.split("脉搏")[1].strip().split("次/分")[0].strip()
        R = text.split("呼吸")[1].strip().split("次/分")[0].strip()
        if len(text.split("血压")) != 2:
            BP_H = ""
            BP_L = ""
        else:
            BP_H = text.split("血压")[1].strip().split("mmHg")[0].split("/")[0].strip()
            BP_L = text.split("血压")[1].strip().split("mmHg")[0].split("/")[1].strip()
    except:
         T, P, R, BP_H, BP_L = ""
    return T, P, R, BP_H, BP_L

# gys 矫正体征数据
def correct_tizheng(ori_datas,ori_source):
    tz_info = "" 
    for info in ori_source['患者基本信息'].split('###'):
        if '体温' in info:
            tz_info = info
            break

    T, P, R, BP_H, BP_L = extract_data_2(info)   
    if T!="" and P!="" and R !="" and BP_H !="" and BP_L !="": 
        ori_datas['患者基本信息']['体温(T)'] = T
        ori_datas['患者基本信息']['脉搏(P)'] = P
        ori_datas['患者基本信息']['呼吸(R)'] = R
        ori_datas['患者基本信息']['高压(BP高)'] = BP_H
        ori_datas['患者基本信息']['低压(BP低)'] = BP_L

# gys 病程与治疗情况
def process_bingcheng(text):
    return text.split('出院。')[0]+"出院。"

# 字符串转json
def transfer_value(val):
    '''
    load dataframe后，字符串转json
    '''
    if val == '':
        return []
    else:
        return json.loads(val)

# 获得文书列表
def get_source_wenshu_list(zylsh, keshi):
    processed_file = f"./Intermediate_process/temp/processed_csv/new_最终处理并合并后数据.csv"
    print(keshi)
    datas = load_excel_csv(processed_file)
    datas.fillna('', inplace=True)

    for col in datas.columns[1:]:
        datas[col] = datas[col].apply(transfer_value)
    
    # processed 后的数据
    data_processed = datas.iloc[0,:].copy()
    wenshu_list = data_processed.iat[5]

    return wenshu_list

# 病史随访
def correct_bingshi(wenshu_list,ori_datas):
    suifang_keshi_dict = {}
    with open('codes/出院小结及子字段/病史随访科室对应.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # 跳过标题行
        for row in reader:
            suifang_keshi_dict[row[0]] = row[1]

    # print("suifang_keshi_dict:", suifang_keshi_dict)  # 打印随访科室字典

    result_jiwangshi_suifang = {}  # 存放既往史结果的随访字典

    # 获取患者入院记录中的"既往史"
    past_history = ""
    for wenshu in wenshu_list:
        if '入院记录' in wenshu['文书名']:
            if '既往史' in wenshu['内容']:
                past_history = wenshu['内容']['既往史']
                break
        if '新入院评估单' == wenshu['文书名']:
            if '一、基本信息' in wenshu['内容']:
                start_index = wenshu['内容']['一、基本信息'].find('特殊既往史:')
                end_index = wenshu['内容']['一、基本信息'].find('既往不安全事件发生史:')
                if start_index != -1 and end_index != -1:
                    past_history += "\t" + wenshu['内容']['一、基本信息'][start_index:end_index].strip()


    # print("past_history:", past_history)  # 打印既往史内容

    # 处理每个既往史条目
    for history_item in past_history.strip().split("。"):
        history_item = history_item.strip()  # 去掉前后空格

        if '；' in history_item or '，' in history_item:
            sub_items = history_item.replace('；', '，').split('，')
        else:
            sub_items = [history_item]

        for sub_item in sub_items:
            sub_item = sub_item.strip()  # 去掉前后空格

            if '否认' not in sub_item and sub_item:  # 确保不是空字符串
                # print("sub_item:", sub_item)  # 打印每个分割后的条目

                if '；' in sub_item:
                    final_items = sub_item.split('；')
                else:
                    final_items = [sub_item]

                for final_item in final_items:
                    final_item = final_item.strip()  # 去掉前后空格

                    if '否认' not in final_item and final_item:  # 确保不是空字符串
                        # print("final_item:", final_item)  # 打印每个最终分割后的条目

                        # 按逗号或顿号分割条目
                        disease_sentences = final_item.replace('、', '，').split('，')
                        for sentence in disease_sentences:
                            sentence = sentence.strip()
                            if sentence:
                                # 在suifang_keshi_dict中匹配对应的科室
                                for key, value in suifang_keshi_dict.items():
                                    if key in sentence:
                                        if value not in result_jiwangshi_suifang:
                                            result_jiwangshi_suifang[value] = []
                                        result_jiwangshi_suifang[value].append(sentence)
                                        break

    # print('--'*70)
    output_list = []
    for keshi, diseases in result_jiwangshi_suifang.items():
        unique_diseases = list(set(diseases))  # 去重
        output_list.append(f"患者{'；'.join(unique_diseases)}，建议{keshi}随访")

    final_output = "；".join(output_list)

    # 如果结果为空，处理传染病史
    if not final_output:
        for history_item in past_history.strip().split("。"):
            if '传染病史' in history_item:
                start_index = past_history.find('传染病史')
                end_index = past_history.find('。', start_index)
                infectious_disease_history = past_history[start_index:end_index].strip()
                # print("infectious_disease_history:", infectious_disease_history)  # 打印传染病史内容

                disease_sentences = infectious_disease_history.split("，")
                for sentence in disease_sentences:
                    sentence = sentence.strip()
                    if sentence:
                        # 在suifang_keshi_dict中匹配对应的科室
                        for key, value in suifang_keshi_dict.items():
                            if key in sentence:
                                if value not in result_jiwangshi_suifang:
                                    result_jiwangshi_suifang[value] = []
                                result_jiwangshi_suifang[value].append(sentence)
                                break

        output_list = []
        for keshi, diseases in result_jiwangshi_suifang.items():
            unique_diseases = list(set(diseases))  # 去重
            output_list.append(f"患者{'；'.join(unique_diseases)}，建议{keshi}随访")

        final_output = "；".join(output_list)

    if final_output:
        final_output += "。"
        final_output = f" 患者病史及建议的随访科室：{final_output}"

    # print(f"患者慢性病病史及建议的随访科室如下：{final_output}")

    ori_datas['出院后用药建议'] = ori_datas['出院后用药建议'] + final_output

def postprocess_yongyaojianyi(model, tokenizer, raw_summary):
    """出院后用药建议去除多余信息"""
    prompt = f"""# [核心任务]
    你的目标是剔除文本中所有通用的、模板化的信息，只保留与患者病情直接相关的、个性化的核心指令，并重新编号。

    # [净化规则 (必须严格遵守)]
    请逐一审查文本中的每一条建议，并执行以下操作：

    1.  **关于【出院带药】**:
        -   如果建议中提到了具体的药品名称，**请只保留药品名称**，修改为“出院带药：药物1, 药物2...”。若出现重复药品，仅保留一个。
        -   **必须删除**所有关于该药品的具体服用说明（如剂量、频率、用法等）。

    2.  **关于【医院行政信息】**:
        -   **必须删除**所有具体的联系方式（如电话号码）。
        -   **必须删除**所有具体的地点和时间信息（如“门诊大楼X楼”、“每周X...”）。

    3.  **关于【格式】**:
        -   将所有保留下来的建议，**重新使用从1开始的连续序号**（例如：1、...。 2、...。）进行编号。

    # [学习示例]
    为了帮助你理解规则，这里有一个例子：

    --- 示例开始 ---
    **待编辑的文本:** 1、注意休息，合理饮食 2、胃肠肿瘤专病门诊随访，不适随诊 3、出院带药：美施康定(硫酸吗啡缓释片)，10mg*10片/盒，10mg，口服，1次1片，1天1次；美施康定(硫酸吗啡缓释片)，30mg*10片/盒，30mg，口服，1次1片，1天1次。4、术后胸带加压包扎切口5天；之后可佩戴文胸；保持伤口清洁干燥，2周内避免洗澡；术后10天内每3天来院换药一次，换药门诊时间：每周一～周五9:00-11:00 在门诊大楼3楼乳腺中心。5、如遇特殊情况，石院长门诊就诊。
    **应用规则后的输出:** 1、注意休息，合理饮食。2、胃肠肿瘤专病门诊随访，不适随诊。3、出院带药：美施康定。4、术后胸带加压包扎切口5天；之后可佩戴文胸；保持伤口清洁干燥，2周内避免洗澡；术后10天内每3天来院换药一次。
    --- 示例结束 ---

    # [正式任务]
    --------------------------------------------------
    现在，请将以上规则应用到下方这份**全新的【待处理文本】**上。

    # 【待处理文本】
    {raw_summary}

    请严格按照规则，直接输出处理【待处理文本】后的信息："""
    # new_summary = generate_qwen_response(model, tokenizer, prompt, system_prompt="你是一位专业的医疗文书编辑，你的任务是对一份【待处理文本】进行净化和精简。", temperature=0.1)
    new_summary = chat_with_api(model="postprocess", user_prompt=prompt, system_prompt="你是一位专业的医疗文书编辑，你的任务是对一份【待处理文本】进行净化和精简。", temperature=0.1)
    return new_summary
 
# 更新数据格式
def update_formats_with_ori_data(zylsh, keshi, formats, ori_datas, ori_source, postprocess_model, postprocess_tokenizer):
    # 对患者基本信息对判断
    if ori_datas['患者基本信息'] == '输入数据过长，模型无法输出！':
        ori_datas['患者基本信息'] = {
            "住院号": "over_length",
            "床号": "over_length",
            "入院时间": "over_length",
            "出院时间": "over_length",
            "科别": "over_length",
            "科室": "over_length",
            "姓名": "over_length",
            "年龄": "over_length",
            "性别": "over_length",
            "低压(BP低)": "over_length",
            "高压(BP高)": "over_length",
            "脉搏(P)": "over_length",
            "呼吸(R)": "over_length",
            "体温(T)": "over_length",
            "入院诊断": "over_length",
        }
    
    # 获取患者的原始文书
    wenshu_list = get_source_wenshu_list(zylsh, keshi)

    # 矫正出院时间
    if ori_datas['患者基本信息']['出院时间'] == '无法判断':
        ori_datas['患者基本信息']['出院时间'] = ori_source['患者基本信息'].split('医嘱时间:')[1].split('\n')[0]
    if keshi == "肿瘤医院头颈外科":
        if zylsh == "2287064":
            ori_datas['患者基本信息']['出院时间'] = "2025.03.03"
    # 病程与治疗情况
    # ori_datas['病程与治疗情况'] = process_bingcheng(ori_datas['病程与治疗情况'])

    #psh 删除并重新添加随访建议
    # process_suifang(ori_datas, ori_source,postprocess_model,postprocess_tokenizer)

    # 病史随访
    # correct_bingshi(wenshu_list,ori_datas)

    # 出院后用药建议
    # ori_datas['出院后用药建议'] = conclude_suggestion(ori_datas,postprocess_model,postprocess_tokenizer)
    if keshi != "肿瘤医院头颈外科":
        ori_datas['出院后用药建议'] = postprocess_yongyaojianyi(postprocess_model, postprocess_tokenizer, ori_datas['出院后用药建议'])
        print("出院后用药建议后处理结束。")
    # 矫正体征数据
    # correct_tizheng(ori_datas,ori_source)

    # 处理 病程与治疗情况 格式问题
    # ori_datas['病程与治疗情况'] = post_process_bingcheng_summary(ori_datas['病程与治疗情况'], postprocess_model, postprocess_tokenizer)

    # 更新格式
    for key, value in formats.items():
        if isinstance(value, dict):
            for sub_key, path in value.items():
                path_parts = path.split('---')
                data = ori_datas
                for part in path_parts:
                    data = data.get(part, "")
                    if isinstance(data, list):
                        if len(data)>=1:
                            data=data[0]
                formats[key][sub_key] = data
        elif isinstance(value, str):
            path_parts = value.split('---')
            data = ori_datas
            for part in path_parts:
                data = data.get(part, "")
                if isinstance(data, list):
                    if len(data)>=1:
                        data=data[0]
            formats[key] = data

def save_json(save_path, data):
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4,ensure_ascii=False)         

def postprocess(key_id,keshi,postprocess_model,postprocess_tokenizer,preds,out_dir = '全部由模型生成', data_dir='全部由模型生成'):
    # input_file = os.path.join(read_dir,'{}.json'.format(key_id))
    
    # with open(input_file, 'r',encoding='utf8') as f:
    #     datas = json.load(f)
    
    datas = preds

    # output取output字段，溯源取source字段
    zylshs = list(datas.keys())
    
    # if len(zylshs[0]) == len('20050400000144'):
    #     return
    # else:
    #     datas[key_id] = datas.pop("")
    #     zylshs = [key_id]

    for zylsh in zylshs:
        data_save_dir = os.path.join(data_dir,zylsh)
        if not os.path.exists(data_save_dir):
            os.makedirs(data_save_dir)
        save_json(os.path.join(data_save_dir,'{}.json'.format(zylsh)),{zylsh:datas[zylsh]})
        data = datas[zylsh]

        data_output = data['output']
        data_output_source = data['find_source']
        data_source = {
            zylsh:data['find_source']
        }
        
        # 处理成医院格式
        processed_data = deepcopy(formats)

        zylsh = key_id #yc添加
        update_formats_with_ori_data(zylsh,keshi,processed_data,data_output, data_output_source ,postprocess_model,postprocess_tokenizer)
            
        # 处理一下住院流水号
        processed_data['病人信息']['住院流水号'] = zylsh
        processed_json = {
            zylsh:processed_data
        }
        # 输出
        rname=os.path.join(data_save_dir,"{}_postprocessed.json".format(zylsh))
        save_json(rname,processed_json)
        # print(f"生成的postprocessed.json内容如下：\n{json.dumps(processed_json, ensure_ascii=False, indent=2)}")
        rname=os.path.join(data_save_dir,"{}_findsource.json".format(zylsh))
        save_json(rname,data_source)
    return processed_json

#psh 加载模型
# which_postprocess_model='model_wjc'
# postprocess_model,postprocess_tokenizer=load_model(which_postprocess_model)

if __name__ == '__main__':
    print('构造指令数据')
    data_dir = sys.argv[1]
    keshi = sys.argv[2]
    zylsh = sys.argv[3]
    out_dir = sys.argv[4]
    data_dir = os.path.join(data_dir,keshi)

    if zylsh == '-1':
        # 处理全部
        zylshs = os.listdir(data_dir)
    elif zylsh == '-2':
        # zylshs = np.loadtxt('新增源文件流水号.csv', delimiter=',',dtype=str)
        # zylshs = np.loadtxt('新增源文件流水号_test_100.csv', delimiter=',',dtype=str)
        zylshs = np.loadtxt(f'./流水号/{keshi}_新增源文件流水号.csv', delimiter=',',dtype=str)
        zylshs = list(zylshs)
        # zylshs = [
        # "21012700000305",
        # "21012700000304",
        # "21012700000287",
        # "21012700000228",
        # "21012700000227",
        # "21012700000216"
        # ]
        # print(zylshs)
    else:
        zylshs = [zylsh]

    #psh 加载模型
    which_postprocess_model='model_wjc'
    postprocess_model,postprocess_tokenizer=load_model(which_postprocess_model)

    print('处理{}个病例'.format(len(zylshs)))
    for zylsh in zylshs:
        read_dir = os.path.join(data_dir,zylsh)
        input_file = os.path.join(read_dir,'{}.json'.format(zylsh))
        with open(input_file, 'r',encoding='utf8') as f:
            datas = json.load(f)
        now_out_dir = os.path.join(out_dir,keshi,zylsh)
        tmp_zylshs = postprocess(zylsh,keshi,postprocess_model,postprocess_tokenizer,datas,now_out_dir,data_dir)
        # for tmp_zylsh in tmp_zylshs:
        #     data_save_dir = os.path.join(data_dir,tmp_zylsh)