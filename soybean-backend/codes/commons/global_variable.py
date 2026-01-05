from transformers import AutoModel, AutoTokenizer
import os
import json
import re
import torch
from decimal import Decimal
import spacy

# 加载中文模型
nlp_zh = spacy.load('zh_core_web_trf') # zh_core_web_trf  zh_core_web_sm
# python -m spacy download zh_core_web_trf
 
[file_path,key_id] = ['','']
[model1,tokenizer1] = ['','']
[model2,tokenizer2] = ['','']
[keshi,ins_out_dir,generate_out_dir,processed_out_dir] = ['','','','']
[model_generated_path,doctor_generated_path,html_generated_path] =['演示示例','医生示例','']
now_mode = ''
# kebie_to_chinesekeshi = {
#     '乳腺外科一':'乳腺外科',
#     '消化一病区':'消化内科',
#     '内分泌一':'内分泌'
# }

def _init(): #初始化
    global model1,tokenizer1
    global model2,tokenizer2
    global file_path,key_id
    global keshi,ins_out_dir,generate_out_dir
    [file_path,key_id] = ['','']
    [model1,tokenizer1] = ['','']
    [model2,tokenizer2] = ['','']
    [keshi,ins_out_dir,generate_out_dir] = ['','','']
 
def load_model(which_model,DEVICE):
    if which_model == 'model1': # 原始模型
        model_path = '/data/yuguangya/ALLYOUNEED/7B/chatglm/chat/chatglm3-6b'
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_path, trust_remote_code=True, device=DEVICE)
    elif which_model == 'model2': # 训练后的模型
        model_path = '/data/wangjiacheng/瑞金/1228_测试/export_models/chuyuanxiaojie_1201'
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_path,torch_dtype=torch.float16, trust_remote_code=True, device=DEVICE)
    elif which_model == 'model_wjc': # 全科室模型
        # model_path = '/HL_user01/trained_models/0229_ck36000_sft_stage4_lora_03-27-09-27-27_export_model'
        model_path = '/data/wangjiacheng/瑞金/1228_测试/export_models/chuyuanxiaojie_1201'
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_path,torch_dtype=torch.float16, trust_remote_code=True, device=DEVICE)
    model = model.eval()
    return model,tokenizer

def set_value(which_model,DEVICE):
    global model1,tokenizer1,model2,tokenizer2,file_path,key_id
    global keshi,ins_out_dir,generate_out_dir, now_mode,processed_out_dir
    global model_generated_path,doctor_generated_path,html_generated_path
    
    if which_model == 'model1':
        model1,tokenizer1 = load_model(which_model,DEVICE)
    elif which_model == 'model2':
        model2,tokenizer2 = load_model(which_model,DEVICE)
    elif which_model == "file_path":
        file_path = DEVICE
    elif which_model == "key_id":
        key_id = DEVICE
    elif which_model == "keshi":
        keshi = DEVICE
    elif which_model == "ins_out_dir":
        ins_out_dir = DEVICE
    elif which_model == "generate_out_dir":
        generate_out_dir = DEVICE
    elif which_model == "processed_out_dir":
        processed_out_dir = DEVICE
    elif which_model == "now_mode":
        now_mode = DEVICE
    elif which_model == "doctor_generated_path":
        doctor_generated_path = DEVICE
    elif which_model == "model_generated_path":
        model_generated_path = DEVICE
    elif which_model == "html_generated_path":
        html_generated_path = DEVICE
    else:
        print('error')
      
def get_value(which_model):
    global model1,tokenizer1,model2,tokenizer2,file_path,key_id
    global keshi,ins_out_dir,generate_out_dir, now_mode, processed_out_dir
    global model_generated_path,doctor_generated_path,html_generated_path

    if which_model == 'model1':
        return model1,tokenizer1
    elif which_model == 'model2':
        return model2,tokenizer2
    elif which_model == "file_path":
        return file_path
    elif which_model == "key_id":
        return key_id    
    elif which_model == "keshi":
        return keshi
    elif which_model == "ins_out_dir":
        return ins_out_dir 
    elif which_model == "generate_out_dir":
        return generate_out_dir 
    elif which_model == "now_mode":
        return now_mode 
    elif which_model == "doctor_generated_path":
        return doctor_generated_path 
    elif which_model == "model_generated_path":
        return model_generated_path
    elif which_model == "html_generated_path":
        return html_generated_path  
    elif which_model == "processed_out_dir":
        return processed_out_dir 

def read_json(file_path):
    with open(file_path,'r',encoding='utf8') as f:
        file_content = json.load(f)  
    return file_content

def save_json(content,file_path):
    with open(file_path,'w',encoding='utf8') as f:
        json.dump(content,f,ensure_ascii=False,indent = 4)

def read_html_json(file_path):
    two_html = read_json(file_path)
    model_json,doctor_json,backtracking_content,analysis_json = two_html['model'],two_html['doctor'],two_html['backtrack'],two_html['analysis']
    return model_json,doctor_json,backtracking_content,analysis_json

def replace_content(label,content,html_content):
    replaced_string = '这是' + label
    html_content = html_content.replace(replaced_string,content)
    return html_content

# 两文本逐字符比较
def diff_texts(texta,textb):
    d = Differ()
    new_texta , new_textb = [], []
    token_type = " " # [" ","+","-"]
    token_text = ""
    for token in d.compare(texta, textb):
        # if token[2:] in [',','。',';','；','：']:
        #     token = " " + token[1:]
        if token[0] != token_type:
            if token_type == " " or token_type == "-":
                new_texta.append((token_text,token_type))  
            if token_type == " " or token_type == "+":
                new_textb.append((token_text,token_type))  
            token_text = ''
            token_type = token[0]
        token_text += token[2:]
    if token_type == " " or token_type == "-":
        new_texta.append((token_text,token_type))  
    if token_type == " " or token_type == "+":
        new_textb.append((token_text,token_type)) 

    def add_highlight_html(new_text,color='red'):
        result = ''
        color = 'background-color: rgb(220, 252, 231);' if color=='green' else 'background-color: rgb(254, 226, 226);'
        for text,label in new_text:
            if label != " ":
                text = f"""<span  style="{color}"><span >{text}</span></span>"""
            result += text
        return result
    
    new_texta = add_highlight_html(new_texta,color='red')
    new_textb = add_highlight_html(new_textb,color='green')

    return new_texta,new_textb

from difflib import Differ
def highlightText(model_path,doctor_path,key_id):
    model_content = read_json(model_path)
    doctor_content = read_json(doctor_path)

    fields = ["病程与治疗情况","出院时情况","出院后用药建议","住院期间医疗情况"]
    for field in fields:
        model,doctor = model_content[key_id][field],doctor_content[key_id][field]
        model_content[key_id][field],doctor_content[key_id][field] = diff_texts(model,doctor)

    return model_content,doctor_content

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity 
def sentence_similarity(sent1, list_sent2):
    # 将句子A和列表B合并为一个列表，以便一起进行TF-IDF向量化
    sentences = [sent1] + list_sent2
    
    # 使用TF-IDF向量化
    vectorizer = TfidfVectorizer(tokenizer=nltk.word_tokenize, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(sentences)
    
    # 计算句子A（tfidf_matrix[0]）与列表B中每个句子的余弦相似度
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    most_similar_index = cosine_similarities.argmax()
    
    # 输出相似度最高的句子和相似度值
    most_similar_sentence = list_sent2[most_similar_index]
    most_similar_score = cosine_similarities[most_similar_index]

    return most_similar_sentence,most_similar_score,most_similar_index

# 对 住院期间医疗情况对分句
def splitByDate(paragraph):
    sentences = re.split(r'(\d{4}-\d{2}-\d{2})',paragraph)         # 保留分割符
    if sentences[0] == '':
        sentences = sentences[1:]
    new_sents = []
    for i in range(len(sentences)-1,1,-2):
        sent = sentences[i-1] + sentences[i]
        new_sents.insert(0,sent)
    if len(sentences)%2 == 1:
        # new_sents.insert(0,sentences[0])
        temp_sentences = nlp_zh(sentences[0])
        temp_sentences = [sent.text for sent in temp_sentences.sents]
        new_sents = temp_sentences + new_sents
    return new_sents

def splitBacktracking(model_content,field):
    # 删除科室类别：
    model_content = model_content[18:]
    # 删掉prompt部分
    temp_list = model_content.split('\n')[:-2] 
    if field in ['病程与治疗情况','出院后用药建议']: # 对这两字段，多删一次
        temp_list = temp_list[:-1]
    model_content = '\n'.join(temp_list)

    # 分句
    text_zh_list = re.split('(\n\n)',model_content)  
    return text_zh_list

# 将对应句子进行悬浮高亮
def highlightSentence(model_sentences,doctor_sentences,backtracking_sentences,analysis_sentences,field_index,field,br=''):
    new_model_sentences, new_doctor_sentences= '',''
    doctor_sentences_copy = doctor_sentences.copy()
    # print(field_index,field)
    backtracking_sentences_copy = backtracking_sentences.copy()
    for index,model_sentence in enumerate(model_sentences):
        most_similar_sentence,most_similar_score,most_similar_index = sentence_similarity(model_sentence, doctor_sentences) # model与doctor比较
        backtrack_sentence,backtrack_score,backtrack_index = sentence_similarity(field+':'+model_sentence, backtracking_sentences) # model与backtrack比较
        id_name = f"{field_index}_{index}+doctor{field_index}_{most_similar_index}+backtrack{field_index}_{backtrack_index}"
        analysis_sentences[id_name] = model_sentence
        doctor_sentences_copy[most_similar_index] =  f"""<span id="doctor{field_index}_{most_similar_index}" >{most_similar_sentence}</span>{br}"""
        model_sentence =  f"""<span id="{field_index}_{index}" onmouseover="openTooltip('{id_name}')"onmouseout="closeTooltip('{id_name}')" >{model_sentence}</span>{br}"""
        backtracking_sentences_copy[backtrack_index] = f"""<span id="backtrack{field_index}_{backtrack_index}" >{backtrack_sentence}</span>{br}"""
        new_model_sentences += model_sentence
    return new_model_sentences,''.join(doctor_sentences_copy),''.join(backtracking_sentences_copy),analysis_sentences

# 对相似的文本做高亮处理
def matchSentence(texta,textb,textc,analysis_sentences,field_index,field,split_date=False):
    # # 将；换成。提升分句效果
    br = ""
    if split_date:
        model_sentences = splitByDate(texta)
        doctor_sentences = splitByDate(textb)
        br = "<br/>"
    else:
        model_sentences = nlp_zh(texta)
        doctor_sentences = nlp_zh(textb)
        model_sentences = [sent.text for sent in model_sentences.sents]
        doctor_sentences = [sent.text for sent in doctor_sentences.sents]
    backtracking_sentences = splitBacktracking(textc,field)

    new_model_sentences,doctor_sentences,backtracking_sentences,analysis_sentences = highlightSentence(model_sentences,doctor_sentences,backtracking_sentences,analysis_sentences,field_index,field,br=br)

    return new_model_sentences,doctor_sentences,backtracking_sentences,analysis_sentences

import spacy
def splitSentence(model_path,doctor_path,backtracking_path,html_path,key_id):
    model_content = read_json(model_path)
    doctor_content = read_json(doctor_path)
    backtracking_content = read_json(backtracking_path)
    
    analysis_sentences = {}
    fields = ["病程与治疗情况","出院时情况","出院后用药建议"]
    for field_index,field in enumerate(fields):
        model,doctor,backtrack = model_content[key_id][field],doctor_content[key_id][field],backtracking_content[key_id][field]
        model_content[key_id][field],doctor_content[key_id][field],backtracking_content[key_id][field],analysis_sentences = matchSentence(model,doctor,backtrack,analysis_sentences,field_index,field)

    fields = ['住院期间医疗情况']
    for field in fields:
        field_index += 1
        model,doctor,backtrack = model_content[key_id][field],doctor_content[key_id][field],backtracking_content[key_id][field]
        model_content[key_id][field],doctor_content[key_id][field],backtracking_content[key_id][field],analysis_sentences = matchSentence(model,doctor,backtrack,analysis_sentences,field_index,field,split_date = True)

    fields = ['入院时简要病史','体检摘要']
    for field in fields:
        field_index += 1
        model,doctor,backtrack = model_content[key_id][field],doctor_content[key_id][field],backtracking_content[key_id]['患者基本信息']
        model_content[key_id][field],doctor_content[key_id][field] = diff_texts(model,doctor)  
        # model_content[key_id][field],doctor_content[key_id][field],backtracking_content[key_id]['患者基本信息'],analysis_sentences = matchSentence(model,doctor,backtrack,analysis_sentences,field_index,field)

    # # 对字典字段单独处理
    # fields = ["基本信息","生命体征"]
    # for field in fields:
    #     field_index += 1
    #     sub_field_index = field_index
    #     for sub_field in model_content[key_id][field].keys():
    #         model,doctor,backtrack = model_content[key_id][field],doctor_content[key_id][field],backtracking_content[key_id]['患者基本信息']
    #         model_content[key_id][field][sub_field],doctor_content[key_id][field][sub_field],backtracking_content[key_id]['患者基本信息'],analysis_sentences  = highlightSentence([model],[doctor],backtrack,analysis_sentences,sub_field_index,sub_field)    
    
    html_dir = '/'.join(html_path.split('/')[:-1])
    if not os.path.exists(html_dir):
        os.makedirs(html_dir)
    two_html = { 'model': model_content , 'doctor':doctor_content, 'analysis':analysis_sentences, 'backtrack': backtracking_content}
    save_json(two_html,html_path)
    
    return model_content,doctor_content,backtracking_content,analysis_sentences

def single_json_to_html(json_content,key_id,title='出院小结'):
    with open(('html/template.html'),'r',encoding='utf-8') as f:
        html_content = f.read()
    if title == "大模型版-出院小结":
        tooltip_html = """<div id="floating-window" class="floating-window"><div class="floating-window-header">分析</div> <div class="floating-window-content">这是一个悬浮窗口的内容</div></div>"""
        html_content = html_content.replace('<div id="floating-window"></div>',tooltip_html)
    html_content = html_content.replace('出院小结',title)
    model_json,doctor_json,backtracking_content,analysis_json = read_html_json(f"{html_generated_path}/{keshi}/{key_id}/{key_id}.json")
    analysis_json = json.dumps(analysis_json,indent=0,ensure_ascii=False)
    html_content = html_content.replace('这是大模型建议',analysis_json)
    
    # 去掉一些重复内容字段
    key_list = list(json_content[key_id].keys())
    key_list.remove('病人信息')

    # 对字典字段单独处理
    key_list.remove('基本信息')
    key_list.remove('生命体征')
    for item in key_list:
        html_content = replace_content(item,json_content[key_id][item],html_content)
    for item in list(json_content[key_id]['基本信息'].keys()):
        html_content = replace_content(item,json_content[key_id]['基本信息'][item],html_content)
    for item in list(json_content[key_id]['生命体征'].keys()):
        html_content = replace_content(item,json_content[key_id]['生命体征'][item],html_content)
    return html_content

def load_cyxj_html(file_name,key_id,prefix='大模型'):
    if os.path.exists(file_name):
        with open(file_name,'r',encoding='utf8') as f:
            content = json.load(f)  
        html_content = single_json_to_html(content,key_id,title=f'{prefix}版-出院小结')
        return html_content
    else:
        return  f'''<div id="container" style="padding:20pt;height: 75vh;overflow-y: scroll;background-color: #f5f5f5;">
                    <section class="docx" style="padding: 40pt 60pt;background-color: #FFFFFF;height:100%;">
                        <p style="text-align: center;"><span style="font-family: 宋体; min-height: 18pt; font-size: 18pt;">{prefix}版-出院小结</span></p>
                        <p style="text-align: center;">
                            <span style="font-family: 微软雅黑; font-weight: bold; min-height: 12pt; font-size: 12pt;">未查询到相关文件，请稍后重试^_^</span>
                        </p>
                    </section>
                </div>
                '''

def load_backtracking_html_wjc(json_content,key_id=key_id):
    with open('html/template_backtracking.html','r',encoding='utf-8') as f:
        backtracking_html = f.read()
    key_list = list(json_content[key_id].keys())
    # print(json_content[key_id]['住院期间医疗情况'])
    for item in key_list:
        # 处理一下输出格式
        # 处理开头的###
        json_content[key_id][item] = re.sub(r'^###(.*)(---|:)\n',r'<br/><span style="font-weight: bold;">###\1</span><br/>',json_content[key_id][item])
        # 处理非开头的
        json_content[key_id][item] = re.sub(r'\n###(.*)(---|:)\n',r'<br/><span style="font-weight: bold;">###\1</span><br/>',json_content[key_id][item])
        # print(json_content[key_id][item])
        json_content[key_id][item] = re.sub(r'\n', '<br/>', json_content[key_id][item])     #  替换\n为<br/>
        # print(json_content[key_id][item])
        json_content[key_id][item] = re.sub(r'^<br/>|<br/>$', '', json_content[key_id][item])     #  删除首尾的<br>
        
        # 替换到页面模板上
        backtracking_html = replace_content(item,json_content[key_id][item],backtracking_html)

    # 处理换行符
    json_content[key_id]['住院期间医疗情况'] = re.sub(r'(\n)+', '<br/>', json_content[key_id]['住院期间医疗情况'])
    return backtracking_html

def load_two_html(key_id=key_id):
    global model_generated_path,doctor_generated_path,html_generated_path,keshi

    model_path = f"{model_generated_path}/{keshi}/{key_id}/{key_id}_postprocessed.json"
    doctor_path = f"{doctor_generated_path}/{keshi}/{key_id}/{key_id}.json"
    html_path = f"{html_generated_path}/{keshi}/{key_id}/{key_id}.json"
    backtracking_path = f"./{model_generated_path}/{keshi}/{key_id}/{key_id}_findsource.json"

    # model_json,doctor_json = highlightText(model_path,doctor_path,key_id)
    # model_json = read_json(model_path)
    # doctor_json = read_json(doctor_path)
    # if not os.path.exists(html_path):
    #     model_json,doctor_json,backtracking_json,analysis_json = splitSentence(model_path,doctor_path,backtracking_path,html_path,key_id)
    # else:
    #     model_json,doctor_json,backtracking_json,analysis_json = read_html_json(html_path)
    model_json,doctor_json,backtracking_json,analysis_json = splitSentence(model_path,doctor_path,backtracking_path,html_path,key_id)

    model_html = single_json_to_html(model_json,key_id,title='大模型版-出院小结')
    doctor_html = single_json_to_html(doctor_json,key_id,title='医生版-出院小结')
    backtracking_html = load_backtracking_html_wjc(backtracking_json,key_id)
    # model_content = load_cyxj_html(model_path,key_id,prefix='大模型')
    # doctor_content = load_cyxj_html(doctor_path,key_id,prefix='医生')

    return model_html,doctor_html,backtracking_html
