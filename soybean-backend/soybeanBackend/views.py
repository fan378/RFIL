import os
import json
import torch
import pandas as pd
import glob
from datetime import datetime
os.environ["CUDA_VISIBLE_DEVICES"] = "2" # 指定使用物理 GPU 

from django.http import HttpResponse,JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.views.decorators.http import require_http_methods
# 进度条
from django.shortcuts import render
from django.views import View
import time
from django.core.cache import cache
# 任务处理
from codes.pipeline_wjc import generateDS
from codes.process_csv import process_and_merge
from codes.py_cyxj_2024_0324_change import get_instructions_v2024_0324
from codes.postprocess_wjc import postprocess
from codes.commons.frontend_constants import *
from codes.commons.utils2 import *
from transformers import AutoTokenizer,AutoModelForCausalLM, AutoModel

# 导入肿瘤医院模块
from codes.zhongliu import run_all_extractions,split_text_to_dict

key_id = ''
keshi = ''
csv_data = ''
doctor_json = {}
final_datas,final_sources = [],[]
generation_params = {}

# 使用API
USE_API = True

global model_path,tokenizer,model
# 默认模型
# model_path = '/data/yuguangya/ALLYOUNEED/Qwen3/Qwen3-8B'
# 训练后模型
model_path = '/data/chuyuxiang/Models/Qwen3-8B-lora-merged'
post_model_path = '/root/nas/llm_models/Qwen3-4B'

tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = ''
postprocess_tokenizer = AutoTokenizer.from_pretrained(post_model_path, trust_remote_code=True)
postprocess_model = ''

if not USE_API:
    model = AutoModelForCausalLM.from_pretrained(model_path, device_map='cuda:1', torch_dtype=torch.bfloat16, trust_remote_code=True)
    postprocess_model = AutoModelForCausalLM.from_pretrained(post_model_path, device_map='cuda:2', torch_dtype=torch.bfloat16, trust_remote_code=True)

# 肿瘤医院模型加载
global zhongliu_model_path, zhongliu_tokenizer, zhongliu_model
zhongliu_model_path = '/root/nas/llm_models/Qwen3-8B'

zhongliu_tokenizer = ''
zhongliu_model = ''
print("正在加载肿瘤医院模型...")
#zhongliu_tokenizer = AutoTokenizer.from_pretrained(zhongliu_model_path, trust_remote_code=True)
'''zhongliu_model = AutoModelForCausalLM.from_pretrained(
    zhongliu_model_path, 
    device_map="cuda:0",
    torch_dtype=torch.bfloat16, 
    trust_remote_code=True
)'''

# 设置pad_token以避免警告
'''if zhongliu_tokenizer.pad_token_id is None:
    zhongliu_tokenizer.pad_token_id = zhongliu_tokenizer.eos_token_id'''
print("肿瘤医院模型加载完成！")
# print("tokenizer:", type(zhongliu_tokenizer))
# print("model:", type(zhongliu_model))
# print("[DEBUG] 传入 tokenizer 类型:", type(zhongliu_tokenizer))
# print("[DEBUG] 传入 model 类型:", type(zhongliu_model))

# result = run_all_extractions(patient_id='wangnannan', external_model=zhongliu_model, external_tokenizer=zhongliu_tokenizer)
# print("result:", result)


from django.shortcuts import render

def index(request):
    return render(request, 'index.html')


@api_view(['POST'])
def login(request):
    api_fox_token = request.META.get('HTTP_APIFOXTOKEN')
    if api_fox_token == 'XL299LiMEDZ0H5h3A29PxwQXdMJqWyY2':
        response = {
            "data": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjpbeyJ1c2VyTmFtZSI6IlNveWJlYW4ifV0sImlhdCI6MTY5ODQ4NDg2MywiZXhwIjoxNzMwMDQ0Nzk5LCJhdWQiOiJzb3liZWFuLWFkbWluIiwiaXNzIjoiU295YmVhbiIsInN1YiI6IlNveWJlYW4ifQ._w5wmPm6HVJc5fzkSrd_j-92d5PBRzWUfnrTF1bAmfk",
                "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjpbeyJ1c2VyTmFtZSI6IlNveWJlYW4ifV0sImlhdCI6MTY5ODQ4NDg4MSwiZXhwIjoxNzYxNTgwNzk5LCJhdWQiOiJzb3liZWFuLWFkbWluIiwiaXNzIjoiU295YmVhbiIsInN1YiI6IlNveWJlYW4ifQ.7dmgo1syEwEV4vaBf9k2oaxU6IZVgD2Ls7JK1p27STE"
            },
            "code": "0000",
            "msg": "请求成功"
        }
        return Response(response)
    return HttpResponse('test request fail',status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def getUserInfo(request):
    # print(request.META)
    Authorization = request.META.get('HTTP_AUTHORIZATION')
    api_fox_token = request.META.get('HTTP_APIFOXTOKEN')
    if api_fox_token == 'XL299LiMEDZ0H5h3A29PxwQXdMJqWyY2' and Authorization == 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjpbeyJ1c2VyTmFtZSI6IlNveWJlYW4ifV0sImlhdCI6MTY5ODQ4NDg2MywiZXhwIjoxNzMwMDQ0Nzk5LCJhdWQiOiJzb3liZWFuLWFkbWluIiwiaXNzIjoiU295YmVhbiIsInN1YiI6IlNveWJlYW4ifQ._w5wmPm6HVJc5fzkSrd_j-92d5PBRzWUfnrTF1bAmfk':
        response = {
            "data": {
                "userId": "0",
                "userName": "Soybean",
                "roles": [
                    "R_SUPER"
                ],
                "buttons": [
                    "B_CODE1",
                    "B_CODE2",
                    "B_CODE3"
                ]
            },
            "code": "0000",
            "msg": "请求成功"
        }
        return Response(response)
    return HttpResponse('test request fail',status=status.HTTP_400_BAD_REQUEST)


def json_to_csv(input_json, output_folder="output_csv"):
    """
    将合并的JSON拆分为原始CSV
    :param input_json: 输入的JSON文件路径
    :param output_folder: 输出目录
    :return: 输出目录路径
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for key, records in data.items():
        if records is None or isinstance(records, str):
            continue
        output_file = os.path.join(output_folder, f"{key}.csv")
        pd.DataFrame(records).to_csv(output_file, index=False, encoding='utf-8')
        print(f"已保存 {output_file}")
    
    print(f"所有CSV文件已还原到 {output_folder}/")
    return output_folder

@api_view(['POST'])
def uploadFile(request):

    # 肿瘤医院匹配文件名
    DIRECT_FILENAME_PATTERN = re.compile(r"^肿瘤医院数据_\d+\.json$", re.IGNORECASE)
    global doctor_json, key_id, final_datas
    if request.FILES:
        # 初始化目录结构
        upload_dir = 'Intermediate_process'
        json_upload_dir = os.path.join(upload_dir, 'temp', 'upload_json')
        csv_output_dir = os.path.join(upload_dir, 'temp', 'upload_csv')
        
        # 创建目录（如果不存在）
        os.makedirs(json_upload_dir, exist_ok=True)
        os.makedirs(csv_output_dir, exist_ok=True)


        for uploaded_file in request.FILES.values():
            # 使用正则表达式的 match 方法进行检查
            if DIRECT_FILENAME_PATTERN.match(uploaded_file.name):
                print(f"检测到特殊模式文件: {uploaded_file.name}，将跳过预处理。")
                
                try:
                    # 直接从这个上传的文件中加载JSON数据
                    final_json_data = json.load(uploaded_file)
                    key_id_from_file = next(iter(final_json_data))

                    all_data = final_json_data.get(key_id_from_file)
                    saved_file_path = os.path.join(json_upload_dir, uploaded_file.name)
                    doctor_json = {f"{key_id_from_file}": all_data.get("出院小结")}
                    patient_json = all_data.get("住院信息")
                    key_id = key_id_from_file
                    with open(saved_file_path, 'w', encoding='utf-8') as destination:
                        # 使用 json.dump 来写入Python对象，ensure_ascii=False保证中文正确显示
                        json.dump(patient_json, destination, ensure_ascii=False, indent=4)
                    final_data = {}
                    final_datas = patient_json
                    response = {
                        "data": patient_json,
                        "message": f"已从文件 {uploaded_file.name} 直接加载数据，跳过预处理",
                    }
                    # 找到并处理后，立即返回
                    return Response(response)

                except Exception as e:
                    error_msg = f"直接解析JSON文件 '{uploaded_file.name}'失败: {str(e)}"
                    print(error_msg)
                    return JsonResponse({'error': error_msg}, status=500)

        # 1. 保存上传的文件（支持JSON和CSV）
        uploaded_files = []
        for file in request.FILES.values():
            file_path = os.path.join(
                json_upload_dir if file.name.lower().endswith('.json') else csv_output_dir,
                file.name
            )
            with open(file_path, 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            uploaded_files.append(file_path)

        # 2. 处理JSON文件（转换为CSV）
        try:
            for file_path in uploaded_files:
                if file_path.lower().endswith('.json'):
                    json_to_csv(
                        input_json=file_path,
                        output_folder=csv_output_dir
                    )
        except Exception as e:
            return JsonResponse({'error': f'文件转换失败: {str(e)}'}, status=500)

        # 3. 处理CSV数据（原有逻辑）
        processed_dir = os.path.join(upload_dir, 'temp', 'processed_csv')
        doctor_dir = os.path.join(upload_dir, 'doctor_generated')
        
        try:
            merged_df, json_datas, cyxjs = process_and_merge(csv_output_dir, processed_dir)
            
            key_id, doctor_json = cyxjs[0][0], cyxjs[0][1]
            response = {
                "data": json_datas,
                "message": "文件处理成功",
                "csv_location": csv_output_dir  # 新增输出路径信息
            }
            return Response(response)
            
        except Exception as e:
            return JsonResponse({'error': f'数据处理失败: {str(e)}'}, status=500)

    return JsonResponse({'error': '无效请求: 未接收到文件'}, status=400)


@api_view(['GET'])
def quickuploadFile(request):
    upload_dir = 'Intermediate_process'
    # 处理文件
    now_data_dir = os.path.join(upload_dir,'temp','upload_csv_back')
    now_out_dir = os.path.join(upload_dir,'temp','processed_csv')
    doctor_dir = os.path.join(upload_dir,'doctor_generated')
    merged_df,json_datas,cyxjs = process_and_merge(now_data_dir,now_out_dir)
    csv_data = merged_df
    global doctor_json,key_id
    key_id,doctor_json = cyxjs[0][0],cyxjs[0][1]
    response = {
        "data": json_datas,
        "message": "File uploaded successfully",
    }
    #print("[返回前端数据(quickuploadFile)]:\n" + json.dumps(response, ensure_ascii=False, indent=2))
    return Response(response)
  


@api_view(['POST'])
def uploadTumorHospitalFile(request):
    """
    肿瘤医院专用文件上传接口
    将上传的JSON文件保存到Intermediate_process/zhongliu目录下，并自动处理新保存的数据
    """
    if request.FILES:
        # 创建zhongliu目录
        zhongliu_dir = os.path.join('Intermediate_process', 'zhongliu')
        os.makedirs(zhongliu_dir, exist_ok=True)
        
        uploaded_files = []
        file_contents = {}
        processed_results = {}
        
        # 处理上传的文件
        for file in request.FILES.values():
            if file.name.lower().endswith('.json'):
                # 保存文件到zhongliu目录
                file_path = os.path.join(zhongliu_dir, file.name)
                with open(file_path, 'wb+') as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                uploaded_files.append(file_path)
                
                # 读取文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_contents[file.name] = json.load(f)
                except Exception as e:
                    return JsonResponse({
                        'error': f'文件内容读取失败: {str(e)}'
                    }, status=500)
                
                # 自动处理新保存的文件
                try:
                    patient_id = os.path.splitext(file.name)[0]
                    print(f"开始处理新上传的肿瘤医院文件: {patient_id}")
                    
                    # 调用肿瘤医院程序处理文件
                    result = run_all_extractions(patient_id, zhongliu_model, zhongliu_tokenizer)
                    doctor_dir = os.path.join('Intermediate_process', 'zhongliu', 'doctor_doc')
                    doctor_path = os.path.join(doctor_dir, f'{patient_id}.json')
                    doctor_doc_content = None
                    if os.path.exists(doctor_path):
                        with open(doctor_path, 'r', encoding='utf-8') as doc_f:
                            doctor_doc_content = json.load(doc_f)
                            print(f"医生文档内容: {doctor_doc_content}")
                            doctor_xianbingshi = doctor_doc_content['入院记录']['现病史']

                    else:
                        print(f"警告: 未找到医生文档文件 {doctor_path}，将使用默认内容")
                    if doctor_xianbingshi is not None:
                        doctor_reuslt = split_text_to_dict(doctor_xianbingshi)#处理医生现病史
                    else:
                        doctor_reuslt = {'现病史': '无现病史信息'}
                    doctor_reuslt['医生主诉'] = doctor_doc_content['入院记录']['主诉']
                    doctor_reuslt['医生初步诊断'] = doctor_doc_content['入院记录']['初步诊断']
                    doctor_reuslt['医生现病史'] = doctor_doc_content['入院记录']['现病史']
                    # 保存处理结果
                    result_dir = os.path.join('Intermediate_process', 'zhongliu', 'result')
                    os.makedirs(result_dir, exist_ok=True)
                    result_path = os.path.join(result_dir, f'{patient_id}_result.json')
                    
                    with open(result_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    # 将doctor_doc的内容拆开铺平到result里
                    merged_result = result.copy()
                    if doctor_reuslt:
                        # 将doctor_doc的每个键值对直接添加到result中
                        for key, value in doctor_reuslt.items():
                            merged_result[key] = value
                    
                    processed_results[patient_id] = {
                        'result': merged_result,
                        'result_path': result_path,
                        'doctor_doc': doctor_reuslt
                    }
                    print(f'响应文件：{processed_results}')
                    print(f"文件 {patient_id} 处理完成，结果已保存到: {result_path}")
                    
                except Exception as e:
                    print(f"处理文件 {file.name} 时出错: {e}")
                    processed_results[patient_id] = {
                        'error': f'处理失败: {str(e)}'
                    }
        
        if uploaded_files:
            # 重构响应结构，将processed_results合并到data中
            restructured_data = {}
            for filename, content in file_contents.items():
                patient_id = os.path.splitext(filename)[0]
                restructured_data[filename] = content
                
                # 如果该患者有处理结果，将其添加到对应的文件名下
                if patient_id in processed_results:
                    result_data = processed_results[patient_id]
                    if 'result' in result_data:
                        restructured_data[filename]['result'] = result_data['result']
            
            response = {
                "data": restructured_data,
                "message": "肿瘤医院文件上传并处理成功！",
                "saved_files": uploaded_files
            }
            return Response(response)
        else:
            return JsonResponse({
                'error': '未找到有效的JSON文件'
            }, status=400)
    else:
        return JsonResponse({
                       'error': '无效请求: 未接收到文件'
                   }, status=400)


@api_view(['POST'])
def uploadSixthHospitalFile(request):
    """
    六院图片上传接口
    保存上传的图片文件到指定目录
    """
    print("=" * 50)
    print("六院图片上传接口开始执行")
    print(f"请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"请求方法: {request.method}")
    print(f"请求头: {dict(request.headers)}")
    print(f"请求文件: {list(request.FILES.keys()) if request.FILES else '无文件'}")
    
    try:
        # 检查是否有文件上传
        if 'file' not in request.FILES:
            print("错误: 未找到'file'键在request.FILES中")
            print(f"可用的文件键: {list(request.FILES.keys())}")
            return JsonResponse({
                'error': '无效请求: 未接收到文件'
            }, status=400)

        uploaded_file = request.FILES['file']
        print(f"上传的文件名: {uploaded_file.name}")
        print(f"文件大小: {uploaded_file.size} bytes")
        print(f"文件类型: {uploaded_file.content_type}")
        
        # 检查文件类型
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/gif']
        if uploaded_file.content_type not in allowed_types:
            print(f"错误: 不支持的文件类型 {uploaded_file.content_type}")
            print(f"允许的文件类型: {allowed_types}")
            return JsonResponse({
                'error': '不支持的文件类型，请上传图片文件'
            }, status=400)

        # 创建保存目录
        save_dir = 'Intermediate_process/liuyuan'
        print(f"创建保存目录: {save_dir}")
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件名（使用时间戳避免重名）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(uploaded_file.name)[1]
        filename = f'liuyuan_{timestamp}{file_extension}'
        file_path = os.path.join(save_dir, filename)
        
        print(f"生成的文件名: {filename}")
        print(f"完整文件路径: {file_path}")
        
        # 保存文件
        print("开始保存文件...")
        with open(file_path, 'wb+') as destination:
            chunk_count = 0
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
                chunk_count += 1
        print(f"文件保存完成，共写入 {chunk_count} 个数据块")
        
        # 验证文件是否成功保存
        if os.path.exists(file_path):
            actual_size = os.path.getsize(file_path)
            print(f"文件保存成功，实际大小: {actual_size} bytes")
            print(f"图片已保存到: {file_path}")
        else:
            print("错误: 文件保存失败，文件不存在")
            return JsonResponse({
                'error': '文件保存失败'
            }, status=500)
        
        # 读取文件内容（用于返回给前端）
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"读取的文件内容大小: {len(file_content)} bytes")
        
        # 返回成功响应
        response = {
            "code": 200,
            "data": {
                "filename": filename,
                "file_path": file_path,
                "file_size": len(file_content),
                "content_type": uploaded_file.content_type
            },
            "message": "六院图片上传成功！",
            "status": "success"
        }
        print(f"准备返回响应: {response}")
        print("六院图片上传接口执行完成")
        print("=" * 50)
        return Response(response)
        
    except Exception as e:
        print(f"六院图片上传异常: {str(e)}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        print("六院图片上传接口执行失败")
        print("=" * 50)
        return JsonResponse({
            'error': f'服务器内部错误: {str(e)}'
        }, status=500)


@api_view(['GET'])
def getSixthHospitalImage(request, filename):
    """
    获取六院图片文件
    """
    print("=" * 50)
    print("获取六院图片接口开始执行")
    print(f"请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"请求方法: {request.method}")
    print(f"请求头: {dict(request.headers)}")
    print(f"请求文件名: {filename}")
    
    try:
        print(f"请求获取图片: {filename}")
        
        # 构建文件路径
        file_path = os.path.join('Intermediate_process/liuyuan', filename)
        print(f"文件路径: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在 - {file_path}")
            print(f"目录内容: {os.listdir('Intermediate_process/liuyuan') if os.path.exists('Intermediate_process/liuyuan') else '目录不存在'}")
            return JsonResponse({
                'error': '文件不存在'
            }, status=404)
        
        print(f"文件存在，开始读取: {file_path}")
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        file_mtime = os.path.getmtime(file_path)
        print(f"文件大小: {file_size} bytes")
        print(f"文件修改时间: {datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 读取文件并返回
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        print(f"文件读取成功，实际读取大小: {len(file_content)} bytes")
        
        # 验证读取的数据大小
        if len(file_content) != file_size:
            print(f"警告: 读取的数据大小({len(file_content)})与文件大小({file_size})不匹配")
        
        # 根据文件扩展名确定内容类型
        content_type = 'image/jpeg'  # 默认
        if filename.lower().endswith('.png'):
            content_type = 'image/png'
        elif filename.lower().endswith('.gif'):
            content_type = 'image/gif'
        elif filename.lower().endswith('.bmp'):
            content_type = 'image/bmp'
        
        print(f"确定的内容类型: {content_type}")
        
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        print(f"响应已创建，状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print("获取六院图片接口执行完成")
        print("=" * 50)
        return response
        
    except Exception as e:
        print(f"获取图片异常: {str(e)}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        print("获取六院图片接口执行失败")
        print("=" * 50)
        return JsonResponse({
            'error': f'服务器内部错误: {str(e)}'
        }, status=500)


@api_view(['POST'])
def generateSixthHospital(request):
    """
    六院数据生成接口
    调用three_extract.py处理上传的图片数据
    """
    print("=" * 50)
    print("六院数据生成接口开始执行")
    print(f"请求时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"请求方法: {request.method}")
    print(f"请求头: {dict(request.headers)}")
    
    try:
        # 获取请求数据
        data = request.data
        print(f"接收到的请求数据: {data}")
        print(f"数据类型: {type(data)}")
        
        # 即使数据为空，也继续处理，因为文件可能已经保存在本地
        if not data:
            print("警告: 请求数据为空，将尝试查找本地保存的文件")

        # 导入three_extract模块
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'codes'))
        print("已添加codes目录到Python路径")
        
        try:
            print("开始导入three_extract模块...")
            import three_extract
            print("three_extract模块导入成功")
            
            # 从数据中提取文件名
            filename = None
            
            # 方法1: 从请求数据中获取
            if isinstance(data, dict) and 'filename' in data:
                filename = data['filename']
                print(f"从请求数据中获取文件名: {filename}")
            
            # 方法2: 从请求头中获取（如果前端通过header传递）
            elif 'HTTP_X_FILENAME' in request.META:
                filename = request.META['HTTP_X_FILENAME']
                print(f"从请求头中获取文件名: {filename}")
            
            # 方法3: 查找liuyuan目录中最新的图片文件
            else:
                print("未从请求数据或请求头中找到文件名，尝试查找最新上传的图片文件...")
                liuyuan_dir = 'Intermediate_process/liuyuan'
                if os.path.exists(liuyuan_dir):
                    image_files = []
                    for file in os.listdir(liuyuan_dir):
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                            file_path = os.path.join(liuyuan_dir, file)
                            image_files.append((file, os.path.getmtime(file_path)))
                    
                    if image_files:
                        # 按修改时间排序，获取最新的文件
                        image_files.sort(key=lambda x: x[1], reverse=True)
                        filename = image_files[0][0]
                        print(f"找到最新的图片文件: {filename}")
                    else:
                        print("liuyuan目录中没有找到图片文件")
                else:
                    print("liuyuan目录不存在")
            
            if not filename:
                print("错误: 无法确定要处理的文件名")
                print(f"请求数据: {data}")
                print(f"请求头: {dict(request.headers)}")
                return JsonResponse({
                    'error': '无法确定要处理的文件名，请确保上传了图片文件'
                }, status=400)
            
            file_path = os.path.join('Intermediate_process/liuyuan', filename)
            print(f"最终确定的文件名: {filename}")
            print(f"完整文件路径: {file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"错误: 文件不存在 - {file_path}")
                print(f"liuyuan目录内容: {os.listdir('Intermediate_process/liuyuan') if os.path.exists('Intermediate_process/liuyuan') else '目录不存在'}")
                return JsonResponse({
                    'error': '图片文件不存在'
                }, status=400)
            
            print(f"文件存在，开始调用three_extract.main()...")
            print(f"传入参数: {file_path}")
            
            # 调用three_extract.py的主函数
            start_time = time.time()
            three_extract.main(file_path)
            end_time = time.time()
            print(f"three_extract.main()执行完成，耗时: {end_time - start_time:.2f}秒")
            
            # 读取生成的结果文件
            base_name = os.path.splitext(filename)[0]
            output_dir = "output7.26"
            print(f"基础文件名: {base_name}")
            print(f"输出目录: {output_dir}")
            
            # 查找最新的生成文件
            timestamp_pattern = datetime.now().strftime("%Y%m%d_%H%M%S")
            print(f"时间戳模式: {timestamp_pattern}")
            
            # 查找空白模板文件
            empty_template_pattern = os.path.join(output_dir, f"{base_name}_空白模板_*.json")
            filled_data_pattern = os.path.join(output_dir, f"{base_name}_虚构填写_*.json")
            text_desc_pattern = os.path.join(output_dir, f"{base_name}_文本描述_*.txt")
            
            print(f"查找空白模板文件: {empty_template_pattern}")
            print(f"查找虚构填写文件: {filled_data_pattern}")
            print(f"查找文本描述文件: {text_desc_pattern}")
            
            empty_template_files = glob.glob(empty_template_pattern)
            filled_data_files = glob.glob(filled_data_pattern)
            text_desc_files = glob.glob(text_desc_pattern)
            
            print(f"找到空白模板文件数量: {len(empty_template_files)}")
            print(f"找到虚构填写文件数量: {len(filled_data_files)}")
            print(f"找到文本描述文件数量: {len(text_desc_files)}")
            
            result = {}
            
            # 读取空白模板
            if empty_template_files:
                latest_empty = max(empty_template_files, key=os.path.getctime)
                print(f"读取空白模板文件: {latest_empty}")
                with open(latest_empty, 'r', encoding='utf-8') as f:
                    result['empty_template'] = json.load(f)
                print(f"空白模板数据大小: {len(str(result['empty_template']))} 字符")
            
            # 读取虚构填写数据
            if filled_data_files:
                latest_filled = max(filled_data_files, key=os.path.getctime)
                print(f"读取虚构填写文件: {latest_filled}")
                with open(latest_filled, 'r', encoding='utf-8') as f:
                    result['filled_data'] = json.load(f)
                print(f"虚构填写数据大小: {len(str(result['filled_data']))} 字符")
            
            # 读取文本描述
            if text_desc_files:
                latest_text = max(text_desc_files, key=os.path.getctime)
                print(f"读取文本描述文件: {latest_text}")
                with open(latest_text, 'r', encoding='utf-8') as f:
                    result['generated_text'] = f.read()
                print(f"文本描述大小: {len(result['generated_text'])} 字符")
            
            print(f"最终处理结果键: {list(result.keys())}")
            print(f"处理结果摘要: {result}")
                
        except ImportError as e:
            print(f"导入three_extract模块失败: {str(e)}")
            print(f"Python路径: {sys.path}")
            return JsonResponse({
                'error': f'模块导入失败: {str(e)}'
            }, status=500)
        except Exception as e:
            print(f"three_extract.py处理失败: {str(e)}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return JsonResponse({
                'error': f'数据处理失败: {str(e)}'
            }, status=500)

        # 返回处理结果 - 只返回generated_text部分
        response_data = {}
        if 'generated_text' in result:
            response_data = result['generated_text']
        else:
            response_data = "未生成文本描述"
            
        response = {
            "code": 200,
            "data": response_data,
            "message": "六院数据生成成功！",
            "status": "success"
        }
        print(f"准备返回响应: {response}")
        print("六院数据生成接口执行完成")
        print("=" * 50)
        return Response(response)
        
    except Exception as e:
        print(f"生成接口异常: {str(e)}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        print("六院数据生成接口执行失败")
        print("=" * 50)
        return JsonResponse({
            'error': f'服务器内部错误: {str(e)}'
        }, status=500)





@api_view(['POST'])
def generateTumorHospital(request):
    """
    肿瘤医院数据生成接口
    调用zhongliu.py处理上传的文件数据
    """
    try:
        # 获取请求数据
        data = request.data
        if not data:
            return JsonResponse({
                'error': '无效请求: 未接收到数据'
            }, status=400)

        # 导入zhongliu模块
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'codes'))
        
        try:
            import zhongliu
            
            # 从数据中提取文件名（假设数据格式为 {filename: content}）
            if isinstance(data, dict) and len(data) > 0:
                # 获取第一个文件名
                filename = list(data.keys())[0]
                # 移除.json扩展名得到患者ID
                patient_id = filename.replace('.json', '')
                
                print(f"处理患者ID: {patient_id}")
                
                # 调用zhongliu.py的主函数
                result = zhongliu.run_all_extractions(patient_id, zhongliu_model, zhongliu_tokenizer)
                
                print(f"处理结果: {result}")
                
            else:
                return JsonResponse({
                    'error': '数据格式错误'
                }, status=400)
                
        except ImportError as e:
            print(f"导入zhongliu模块失败: {str(e)}")
            return JsonResponse({
                'error': f'模块导入失败: {str(e)}'
            }, status=500)
        except Exception as e:
            print(f"zhongliu.py处理失败: {str(e)}")
            return JsonResponse({
                'error': f'数据处理失败: {str(e)}'
            }, status=500)

        # 返回处理结果
        response = {
            "data": result,
            "message": "肿瘤医院数据生成成功！",
            "status": "success"
        }
        return Response(response)
        
    except Exception as e:
        print(f"生成接口异常: {str(e)}")
        return JsonResponse({
            'error': f'服务器内部错误: {str(e)}'
        }, status=500)
  


@api_view(['POST'])
def postParams(request):
    global final_datas,final_sources,tokenizer, keshi
    # 打印传递的参数
    params = json.loads(request.body.decode())  # 获取 department 参数
    department = params.get('department')
    zylsh = key_id
    if department == "肿瘤医院头颈外科":
        keshi = department
        final_sources_path = os.path.join("Intermediate_process", "final_preprocessed_responses", f"final_sources_{zylsh}.json")
        final_datas_path = os.path.join("Intermediate_process", "final_preprocessed_responses", f"final_datas_{zylsh}.json")
        # 检查这个文件是否存在
        if os.path.exists(final_sources_path) and os.path.exists(final_datas_path):
            print(f"检测到最终预处理文件: {final_sources_path} 和 {final_datas_path}。将直接加载并返回。")
            try:
                # 加载这个最终结果文件
                with open(final_sources_path, 'r', encoding='utf-8') as f:
                    final_sources_data = json.load(f)
                with open(final_datas_path, 'r', encoding='utf-8') as f:
                    final_datas_data = json.load(f)
                final_datas = final_datas_data
                final_sources.append(final_sources_data)
                section_columns = {}
                for key,value in final_sources_data.items():
                    section_columns[key] = list(value.keys())
                # 构建一个和原函数一模一样的响应结构
                response = {
                    "data": {'section_contents':final_sources_data,'section_columns':section_columns,'logic_type':logic_type},
                    "message": "已成功加载预处理的最终结果",
                }
                # 直接返回，后续所有代码都不会执行
                return Response(response)
            except Exception as e:
                return JsonResponse({'error': f"加载最终预处理文件失败: {str(e)}"}, status=500)

    global generation_params
    # generation_params['topp'] = float(params.get('topp'))
    # generation_params['topk'] = int(params.get('topk'))
    generation_params['max_length'] = int(params.get('max_tokens'))

    if department in en_zn_keshis:
        keshi = en_zn_keshis[department]
    elif department in zn_en_keshis:
        keshi = zn_en_keshis[department]
    
    csv_data_path = os.path.join("Intermediate_process/temp/processed_csv",'new_最终处理并合并后数据.csv')
    now_out_dir = os.path.join("Intermediate_process","instructions",keshi,zylsh)
    if not os.path.exists(now_out_dir):
        os.makedirs(now_out_dir)
    final_datas,final_sources = get_instructions_v2024_0324(csv_data_path,now_out_dir,keshi,zylsh,tokenizer)
    with open(os.path.join("Intermediate_process","instructions",keshi,zylsh,'source.json'), 'w',encoding='utf8') as f:
        json.dump(final_sources[0], f, ensure_ascii=False, indent=4)
    
    doctor_dir = os.path.join("Intermediate_process","doctor_generated",keshi,zylsh)
    if not os.path.exists(doctor_dir):
        os.makedirs(doctor_dir)
    with open(os.path.join("Intermediate_process","doctor_generated",keshi,zylsh,f'{zylsh}.json'), 'w',encoding='utf8') as f:
        json.dump(doctor_json, f, ensure_ascii=False, indent=4)

    # 传回数据二次处理
    final_data = {}
    # 2. 使用 for 循环遍历原始列表中的每一项
    print("开始处理EMR列表...")
    for item in final_datas:
        # 从当前项中获取顶层键 (如 "患者基本信息") 和 EMR文本
        top_level_key = item.get("key")
        instruction_text = item.get("instruction")

        # 进行简单的校验，防止数据格式问题导致程序出错
        if not top_level_key or not instruction_text:
            print(f"警告: 列表中的一项缺少 'key' 或 'instruction'，已跳过: {item}")
            continue
    
        # 3. 调用解析函数处理 EMR 文本
        parsed_emr_dict = parse_emr_to_dict(instruction_text)
        
        # 4. 将解析后的字典作为值，存入最终结果字典中
        final_data[top_level_key] = parsed_emr_dict
        
        print(f"已处理: '{top_level_key}'")
    with open(os.path.join("Intermediate_process","instructions",keshi,zylsh,'final_data.json'), 'w',encoding='utf8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)

    final_sources[0] = final_data

    section_columns = {}
    for key,value in final_data.items():
        section_columns[key] = list(value.keys())
    response = {
        "data": {'section_contents':final_data,'section_columns':section_columns,'logic_type':logic_type},
        "message": "Params accepted successfully",
    }
    #print("[返回前端数据(postParams)]:\n" + json.dumps(response, ensure_ascii=False, indent=2))
    return Response(response)

@api_view(['POST'])
def generateSummary(request):
    # 日志
    log_filename_with_date = f"interaction_log_{datetime.now().strftime('%Y-%m-%d')}.log"
    setup_global_logger(log_filename_with_date)

    params = json.loads(request.body.decode())
    import time
    t1 = time.time()

    # 新增：优先从前端参数获取key_id，避免全局变量丢失导致KeyError
    global key_id
    if 'key_id' in params and params['key_id']:
        key_id = params['key_id']
    logic_type = params
    # 兼容多种格式
    logic_prompt = {}
    for key, value in logic_type.items():
        logic_prompt[key] = value 

    # 生成结果
    global doctor_json,keshi,final_sources,final_datas,generation_params
    for index,instruction in  enumerate(final_datas):
        key = instruction['key']
        final_datas[index]['input'] = logic_prompt[key]

    now_out_dir = os.path.join("Intermediate_process","model_generated",keshi,key_id)

    if keshi == "肿瘤医院头颈外科":
        model = "postprocess"
    else:
        model = "pretrained"

    preds = generateDS(model,tokenizer,final_datas,key_id,keshi,now_out_dir,generation_params)
    #print("模型生成的preds内容：", json.dumps(preds, ensure_ascii=False, indent=2))
    patient = postprocess(key_id, keshi, postprocess_model, postprocess_tokenizer, preds, now_out_dir, now_out_dir)

    t2 = time.time()
    print(f"模型生成执行时间：{t2-t1:.2f}s")
    
    # 处理格式
    doctor = process_format(doctor_json[key_id])
    source = process_source(final_sources[0])

    patient = process_format(patient[key_id])
    
    #source_pattern1 = process_pattern(source,patient,model,tokenizer) # 溯源
    source_pattern1 = process_pattern_new(source,patient)
    source_pattern = re_source(source_pattern1)# 溯源
    #save_json('source_pattern.json',source_pattern)
    #doctor_pattern = find_best_matches(patient,doctor)
    doctor_pattern,patient_new,doctor_new = find_best_matches_ceshi(patient, doctor)
    source_pattern_new = find_jianyanjiancha(patient_new,source_pattern)

    # save_json('1.json',doctor_pattern)
    # save_json('source_pattern_new.json',source_pattern_new)
    save_json(os.path.join("Intermediate_process","model_generated",keshi,key_id,f'{key_id}_source.json'),source)
    save_json(os.path.join("Intermediate_process","model_generated",keshi,key_id,f'{key_id}_back.json'),patient)
    # time.sleep(90)

    response = {
        #"data": {'source':source,'source_pattern':source_pattern,'patient':patient,'doctor':doctor, 'doctor_pattern':doctor_pattern},
        "data": {'source':source,'source_pattern':source_pattern_new,'patient':patient,'doctor':doctor, 'doctor_pattern':doctor_pattern, 'patient_new':patient_new, 'doctor_new':doctor_new},
        "message": "Summary generated successfully",
    }
    #print("[返回前端数据(generateSummary)]:\n" + json.dumps(response, ensure_ascii=False, indent=2))

    t2 = time.time()
    print(f"总执行时间：{t2-t1:.2f}s")
    return Response(response)

@api_view(['POST'])
def saveComment(request):
    # 打印传递的参数
    params = json.loads(request.body.decode())  # 获取参数
    comment = params.get('comment') 
    save_id = params.get('save_id') 

    # 向comment.txt中追加一行 时间： save_id : comment
    with open('comment.txt', 'a', encoding='utf-8') as file:
        file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} : {save_id} : {comment}\n")

    response = {
        "message": "successfully",
    }
    #print("[返回前端数据(saveComment)]:\n" + json.dumps(response, ensure_ascii=False, indent=2))
    return Response(response)


class LongTaskView(View):
    def get(self, request):
        # 这是假设你有一个长时间运行的任务
        total_steps = 10
        for step in range(total_steps):
            # 模拟耗时操作
            time.sleep(1)
            progress = (step + 1) / total_steps * 100
            # 将进度存储在缓存中
            cache.set('task_progress', progress)
        return JsonResponse({"message": "Task completed"})
    def post(self, request):
        # 这是假设你有一个长时间运行的任务
        total_steps = 10
        for step in range(total_steps):
            # 模拟耗时操作
            time.sleep(1)
            progress = (step + 1) / total_steps * 100
            # 将进度存储在缓存中
            cache.set('task_progress', progress)
        return JsonResponse({"message": "Task completed"})

class GetProgressView(View):
    def get(self, request):
        # 获取任务的当前进度
        progress = cache.get('task_progress', 0)
        return JsonResponse({"progress": progress})


@api_view(['POST'])
def processZhongliuFile(request):
    """
    处理肿瘤医院文件的API接口
    接收保存在zhongliu目录下的文件，调用肿瘤医院程序进行处理
    """
    try:
        params = json.loads(request.body.decode())
        patient_id = params.get('patient_id', '')
        
        if not patient_id:
            return JsonResponse({
                'error': '缺少patient_id参数'
            }, status=400)
        
        # 检查文件是否存在
        file_path = os.path.join('Intermediate_process', 'zhongliu', f'{patient_id}.json')
        if not os.path.exists(file_path):
            return JsonResponse({
                'error': f'文件不存在: {file_path}'
            }, status=404)
        
        # 调用肿瘤医院程序处理文件
        print(f"开始处理肿瘤医院文件: {patient_id}")
        result = run_all_extractions(patient_id, zhongliu_model, zhongliu_tokenizer)
        
        # 保存结果到zhongliu目录
        result_dir = os.path.join('Intermediate_process', 'zhongliu', 'result')
        os.makedirs(result_dir, exist_ok=True)
        result_path = os.path.join(result_dir, f'{patient_id}_result.json')
        
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        response = {
            "data": result,
            "message": "肿瘤医院文件处理成功",
            "result_path": result_path
        }
        return Response(response)
        
    except Exception as e:
        return JsonResponse({
            'error': f'处理失败: {str(e)}'
        }, status=500)

