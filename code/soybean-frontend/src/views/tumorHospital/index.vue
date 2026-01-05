<script setup lang="ts">
import { computed, defineOptions, nextTick, ref } from 'vue';
import { useMessage } from 'naive-ui';
import type { UploadFileInfo } from 'naive-ui';
import { ArchiveOutline as ArchiveIcon, ArrowForwardOutline, DocumentAttachOutline, DownloadOutline, MedicalOutline, PersonOutline } from '@vicons/ionicons5';
import { GenerateTumorHospital, UploadTumorHospitalFiles } from '@/service/api';

defineOptions({
  name: 'TumorHospital'
});

const headers = { 'Content-Type': 'multipart/form-data' };
const fileList = ref<UploadFileInfo[]>([]); // 存储用户上传的文件列表
const message = useMessage();

// 状态管理
const uploadSuccess = ref(false);
const uploadedFileData = ref<any>(null);
const showPreview = ref(false);
const currentView = ref<'upload' | 'preview' | 'generating' | 'result'>('upload');
const progress = ref(0);
const status = ref('正在初始化...');
const resultData = ref<any>(null);

// 源文件内容选择状态
const selectedSourceKey = ref('');

// 计算源文件菜单选项
const computedSourceMenuOptions = computed(() => {
  if (!resultData.value?.data) return [];

  const fileName = Object.keys(resultData.value.data)[0];
  const fileContent = resultData.value.data[fileName];

  console.log('源文件内容调试信息:', {
    fileName,
    fileContentKeys: Object.keys(fileContent),
    totalKeys: Object.keys(fileContent).length,
    fileContent
  });

  // 过滤掉result字段，只保留原始医疗文件内容
  const filteredEntries = Object.entries(fileContent).filter(([key]) => {
    // 只过滤掉result字段，保留所有其他字段
    const shouldKeep = key !== 'result';
    if (!shouldKeep) {
      console.log('过滤掉字段:', key);
    }
    return shouldKeep;
  });

  console.log('过滤后的条目:', {
    filteredEntries: filteredEntries.map(([key]) => key),
    filteredCount: filteredEntries.length
  });

  return filteredEntries.map(([key]) => ({
    label: key.length > 20 ? `${key.substring(0, 20)}...` : key,
    key,
    title: key // 添加完整的title属性用于tooltip显示
  }));
});

// 获取当前选中的源文件内容
const currentSourceContent = computed(() => {
  if (!resultData.value?.data || !selectedSourceKey.value) return '';

  const fileName = Object.keys(resultData.value.data)[0];
  const fileContent = resultData.value.data[fileName];

  return fileContent[selectedSourceKey.value] || '';
});

// 处理源文件菜单选择
const handleSourceMenuSelect = (key: string) => {
  selectedSourceKey.value = key;
};

// 初始化源文件选择
const initializeSourceSelection = () => {
  if (resultData.value?.data) {
    const options = computedSourceMenuOptions.value;
    console.log('初始化源文件选择:', {
      optionsCount: options.length,
      options: options.map(opt => opt.key),
      selectedKey: selectedSourceKey.value
    });
    if (options.length > 0) {
      selectedSourceKey.value = options[0].key;
      console.log('设置初始选择:', selectedSourceKey.value);
    }
  } else {
    console.log('resultData.value?.data 不存在');
  }
};

// 获取过滤后的文件数据（用于预览页面）
const filteredFileData = computed(() => {
  if (!uploadedFileData.value) return null;

  const fileName = Object.keys(uploadedFileData.value)[0];
  const fileContent = uploadedFileData.value[fileName];

  if (!fileContent) return null;

  // 过滤掉result字段，只保留原始医疗文件内容
  const filteredContent = { ...fileContent };
  delete filteredContent.result;

  return {
    [fileName]: filteredContent
  };
});

// 获取生成结果数据
const getResultData = computed(() => {
  if (!resultData.value?.processed_results) return {
    zhusu: "",
    chubuzhenduan: "",
    shiyanshi: "",
    xizhen: "",
    ct: "",
    shuhoubingli: "",
    xianbingshi: ""
  };

    const fileName = Object.keys(resultData.value.processed_results)[0];
  const data: any = resultData.value.processed_results[fileName]?.result || {};

    // 提取result相关字段
  const extractedResultData = {
    zhusu: data.zhusu || "",
    chubuzhenduan: data.chubuzhenduan || "",
    shiyanshi: data.shiyanshi || "",
    xizhen: data.xizhen || "",
    ct: data.ct || "",
    shuhoubingli: data.shuhoubingli || "",
    xianbingshi: data.xianbingshi || ""
  };

  return extractedResultData;
});

// 获取医生版数据
const getDoctorData = computed(() => {
  if (!resultData.value?.processed_results) return {
    "医生主诉": "",
    "医生初步诊断": "",
    "查超声示": "",
    "行细针穿刺示": "",
    "颈部CT提示": "",
    "术后病理": "",
    "医生现病史": ""
  };

    const fileName = Object.keys(resultData.value.processed_results)[0];
  const data: any = resultData.value.processed_results[fileName]?.result || {};

    // 从result中提取医生版相关字段
  const doctorData = {
    "医生主诉": data.医生主诉 || "",
    "医生初步诊断": data.医生初步诊断 || "",
    "查超声示": data.查超声示 || "",
    "行细针穿刺示": data.行细针穿刺示 || "",
    "颈部CT提示": data.颈部CT提示 || "",
    "术后病理": data.术后病理 || "",
    "医生现病史": data.医生现病史 || ""
  };

  return doctorData;
});

// 格式化文本内容，处理换行符
const formatText = (text: string) => {
  if (!text) return '';
  return text.replace(/\n/g, '<br>');
};


async function UploadTumorHospitalFilesRequest(options: { fileList: UploadFileInfo[] }) {
  const formData = new FormData();
  options.fileList.forEach(file => {
    if (file.file) {
      formData.append(file.name, file.file);
    }
  });

    const { data: info, error } = await UploadTumorHospitalFiles(headers, formData);

  console.log('肿瘤医院上传响应:', info);
  console.log('响应数据结构:', {
    hasData: Boolean(info),
    dataKeys: info ? Object.keys(info) : [],
    dataType: typeof info
  });

  if (!error) {
    // 显示上传成功消息
    message.success('肿瘤医院文件上传成功！文件已保存到指定目录。');

    // 设置状态
    uploadSuccess.value = true;

    // 直接使用info作为文件数据，因为transformBackendResponse已经提取了data字段
    uploadedFileData.value = info;
    console.log('设置的文件数据:', uploadedFileData.value);
    console.log('info 类型:', typeof info);
    console.log('info 是否为对象:', typeof info === 'object');
    console.log('info 结构:', info ? Object.keys(info) : 'null');

    // 检查上传的数据是否已经包含处理结果
    if (info && info.processed_results) {
      console.log('上传数据已包含处理结果，直接设置resultData');
      resultData.value = info;
      console.log('resultData已设置:', resultData.value);
      console.log('resultData.value 结构:', Object.keys(resultData.value));
    } else {
      console.log('上传数据不包含processed_results字段，需要调用生成API');
      console.log('info.processed_results:', info?.processed_results);
      console.log('上传的数据结构:', info);
    }

    // 打印文件内容
    if (info) {
      console.log('文件内容:', info);
    }
  } else {
    console.error('上传失败:', error);
    message.error('上传失败，请重试');
    uploadSuccess.value = false;
  }
}

let timerId: NodeJS.Timeout | null = null;
const wait = 500;

const handleChange = (options: { fileList: UploadFileInfo[] }) => {
  if (timerId !== null) {
    clearTimeout(timerId);
  }

  timerId = setTimeout(() => {
    // console.log('handle', options.fileList.length);
    UploadTumorHospitalFilesRequest(options);
    // 重置定时器
    timerId = null;
  }, wait);
};

// 支持的文件类型
const supportedFileTypes = [
  { label: 'JSON文件', extensions: ['.json'], description: '包含所有数据的合并JSON文件' }
];

// JSON 示例文件
const jsonSampleFiles = [
  { label: 'henglihua.json', url: '/henglihua.json', description: '包含完整患者数据的JSON文件' }
];

// 处理生成
const handleGenerate = async () => {
  console.log('=== 生成函数开始 ===');
  console.log('点击生成按钮，当前文件数据:', uploadedFileData.value);
  console.log('uploadedFileData.value 类型:', typeof uploadedFileData.value);
  console.log('uploadedFileData.value 结构:', uploadedFileData.value ? Object.keys(uploadedFileData.value) : 'null');

  // 检查是否已经有处理结果
  if (uploadedFileData.value && uploadedFileData.value.processed_results) {
    console.log('数据已包含处理结果，直接显示结果');
    resultData.value = uploadedFileData.value;
    console.log('resultData.value 已设置:', resultData.value);
    currentView.value = 'result';
    return;
  }

  // 检查是否需要构造数据结构
  if (uploadedFileData.value && Object.keys(uploadedFileData.value).length > 0) {
    console.log('上传数据存在，但需要调用生成API获取处理结果');
    console.log('上传数据是否包含processed_results:', uploadedFileData.value.processed_results);
    if (uploadedFileData.value.processed_results) {
      console.log('上传数据已包含processed_results，直接使用');
      resultData.value = uploadedFileData.value;
      currentView.value = 'result';
      return;
    }
  }

  console.log('数据不包含处理结果，需要调用生成API');
  console.log('uploadedFileData.value.processed_results:', uploadedFileData.value?.processed_results);

  currentView.value = 'generating';

  try {
    // 模拟进度更新
    const updateProgress = () => {
      const interval = setInterval(() => {
        if (progress.value < 90) {
          progress.value += Math.random() * 10;
          if (progress.value < 30) {
            status.value = '正在读取文件数据...';
          } else if (progress.value < 60) {
            status.value = '正在处理医疗数据...';
          } else if (progress.value < 90) {
            status.value = '正在生成结果...';
          }
        }
      }, 500);
      return interval;
    };

    const progressInterval = updateProgress();

    // 调用后端API
    const { data: generateResult, error } = await GenerateTumorHospital(uploadedFileData.value);

    // 处理成功响应
    progress.value = 100;
    status.value = '生成完成！';

    // 清理定时器
    clearInterval(progressInterval);

        // 延迟显示结果
    setTimeout(() => {
      console.log('=== 生成结果调试信息 ===');
      console.log('error:', error);
      console.log('generateResult:', generateResult);
      console.log('generateResult 类型:', typeof generateResult);
      console.log('generateResult 是否为对象:', typeof generateResult === 'object');
      console.log('generateResult 的所有键:', generateResult ? Object.keys(generateResult) : []);
      console.log('generateResult.医生主诉:', generateResult?.医生主诉);
      console.log('generateResult.医生初步诊断:', generateResult?.医生初步诊断);
      console.log('generateResult.查超声示:', generateResult?.查超声示);
      console.log('generateResult 完整内容:', JSON.stringify(generateResult, null, 2));

      // 使用后端返回的生成结果
      if (!error && generateResult) {
        // 构造正确的数据结构
        const fileName = Object.keys(uploadedFileData.value)[0];
        const fileNameWithoutExt = fileName.replace('.json', '');

        // 从上传数据中获取完整的result（包含医生版字段）
        const fullResult = uploadedFileData.value[fileName]?.result || generateResult;

        console.log('上传数据中的result:', uploadedFileData.value[fileName]?.result);
        console.log('generateResult:', generateResult);
        console.log('使用的fullResult:', fullResult);
        console.log('fullResult中的医生版字段:', {
          "医生主诉": fullResult.医生主诉,
          "医生初步诊断": fullResult.医生初步诊断,
          "查超声示": fullResult.查超声示,
          "行细针穿刺示": fullResult.行细针穿刺示
        });

        resultData.value = {
          data: uploadedFileData.value,
          message: "肿瘤医院文件上传并处理成功！",
          saved_files: [`Intermediate_process/zhongliu/${fileName}`],
          processed_results: {
            [fileNameWithoutExt]: {
              result: fullResult,
              result_path: `Intermediate_process/zhongliu/result/${fileNameWithoutExt}_result.json`,
              doctor_doc: fullResult
            }
          }
        };

        console.log('设置的结果数据（生成结果）:', resultData.value);
        console.log('resultData.value 结构:', Object.keys(resultData.value));
      } else {
        // 如果生成失败，检查上传的数据是否包含processed_results
        console.log('生成API失败，检查上传数据...');
        console.log('uploadedFileData.value:', uploadedFileData.value);

        if (uploadedFileData.value && uploadedFileData.value.processed_results) {
          // 如果上传的数据已经包含processed_results，直接使用
          resultData.value = uploadedFileData.value;
          console.log('使用上传数据（包含processed_results）:', resultData.value);
        } else {
          // 如果上传的数据没有processed_results，显示错误信息
          console.error('上传数据中没有processed_results字段');
          message.error('生成失败：数据格式不正确，请重新上传文件');
          currentView.value = 'upload';
          return;
        }
      }

      console.log('最终 resultData.value:', resultData.value);
      console.log('切换到结果页面');
      currentView.value = 'result';
      // 初始化源文件选择
      nextTick(() => {
        initializeSourceSelection();
      });
    }, 1000);

  } catch (error) {
    console.error('生成失败:', error);
    message.error('生成失败，请重试');
    currentView.value = 'upload';
  }
};

// 下一步按钮处理函数
const handleNextStep = () => {
  console.log('点击下一步按钮');
  console.log('当前文件数据:', uploadedFileData.value);
  console.log('数据类型:', typeof uploadedFileData.value);
  currentView.value = 'preview';
};

// 返回上传页面
const handleBackToUpload = () => {
  currentView.value = 'upload';
  uploadSuccess.value = false;
  uploadedFileData.value = null;
  progress.value = 0;
  status.value = '正在初始化...';
  resultData.value = null;
  showPreview.value = false;
};

// 从预览页面返回上传页面（保留数据）
const handleBackFromPreview = () => {
  currentView.value = 'upload';
  // 保留上传的数据，不清空
};

// 重新生成
const handleRegenerate = () => {
  currentView.value = 'upload';
  uploadSuccess.value = false;
  uploadedFileData.value = null;
  progress.value = 0;
  status.value = '正在初始化...';
  resultData.value = null;
  showPreview.value = false;
};

// 下载文件内容
const handleDownload = () => {
  if (!resultData.value) return;

  // 创建下载内容，包含生成结果和医生版
  const downloadContent = {
    timestamp: new Date().toISOString(),
    processed_results: resultData.value.processed_results,
    source_files: resultData.value.saved_files,
    message: resultData.value.message
  };

  const content = JSON.stringify(downloadContent, null, 2);
  const blob = new Blob([content], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `肿瘤医院生成结果_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
</script>

<template>
  <div>
    <!-- 上传页面 -->
    <div v-if="currentView === 'upload'">
      <NCard title="肿瘤医院生成" class="mb-4">
        <NText depth="3">
          欢迎使用肿瘤医院生成功能。请上传您的医疗数据文件，系统将为您生成相应的医疗报告。
        </NText>
      </NCard>

      <NUpload
        v-model:file-list="fileList"
        multiple
        :header="{}"
        directory-dnd
        :max="10"
        accept=".json"
        @change="handleChange"
      >
        <NUploadDragger>
          <div style="margin-bottom: 12px">
            <NIcon size="48" :depth="3">
              <ArchiveIcon />
            </NIcon>
          </div>
          <NText style="font-size: 16px">单击或将文件拖到此区域进行上传。</NText>
          <NP depth="3" style="margin: 8px 0 0 0">
            支持 JSON 文件格式，请不要上传敏感数据
          </NP>
        </NUploadDragger>
      </NUpload>

      <NGrid cols="2" x-gap="16" class="mt-4">
        <!-- 左侧：文档说明 -->
        <NGridItem>
          <NAlert title="操作说明" type="info">
            <p>上传文件之前，请按照以下说明操作：</p>
            <ol>
              <li>
                <strong>JSON文件上传：</strong> 您可以上传一个包含所有数据的JSON文件，系统会自动处理并转换为所需的格式。
              </li>
              <li>
                如果您不小心遗漏了某个文件，不用担心——只需重新上传文件，系统就会覆盖之前上传的文件。
              </li>
            </ol>
          </NAlert>

          <!-- 支持的文件类型说明 -->
          <NCard title="支持的文件类型" style="margin-top: 16px">
            <NList hoverable>
              <NListItem v-for="fileType in supportedFileTypes" :key="fileType.label">
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%">
                  <div>
                    <NText strong>{{ fileType.label }}</NText>
                    <br />
                    <NText depth="3" style="font-size: 12px">{{ fileType.description }}</NText>
                  </div>
                  <NTag :bordered="false" type="info" size="small">
                    {{ fileType.extensions.join(', ') }}
                  </NTag>
                </div>
              </NListItem>
            </NList>
          </NCard>
        </NGridItem>

        <!-- 右侧：示例文件列表 -->
        <NGridItem>
          <!-- JSON 示例文件 -->
          <NCard title="JSON 示例文件">
            <NList hoverable style="overflow: auto; padding: 0; border: none">
              <NListItem v-for="file in jsonSampleFiles" :key="file.label" style="padding: 6px 12px; border-bottom: none">
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%">
                  <div style="display: flex; align-items: center; gap: 6px; flex: 1;">
                    <NIcon><DocumentAttachOutline /></NIcon>
                    <div>
                      <NText>{{ file.label }}</NText>
                      <br />
                      <NText depth="3" style="font-size: 12px">{{ file.description }}</NText>
                    </div>
                  </div>
                  <a :href="file.url" download style="color: inherit">
                    <NIcon size="18"><DownloadOutline /></NIcon>
                  </a>
                </div>
              </NListItem>
            </NList>
          </NCard>
        </NGridItem>
      </NGrid>

      <!-- 下一步按钮 -->
      <div v-if="uploadSuccess" class="mt-6 text-center">
        <NButton type="primary" size="large" @click="handleNextStep">
          <NIcon><ArrowForwardOutline /></NIcon>
          <span>下一步 - 查看文件内容</span>
        </NButton>
      </div>
    </div>

    <!-- 文件预览页面 -->
    <div v-else-if="currentView === 'preview'">
      <div class="mb-4">
        <NButton @click="handleBackFromPreview" type="default">
          <NIcon><ArrowForwardOutline /></NIcon>
          <span>返回上传页面</span>
        </NButton>
      </div>

      <NCard title="肿瘤医院文件内容预览" class="mb-4">
        <NText depth="3">
          以下是上传文件中的所有医疗数据内容，您可以查看各个部分的详细信息。
        </NText>

        <!-- 生成按钮 -->
        <div class="mt-4">
          <NButton
            type="primary"
            size="large"
            @click="handleGenerate"
          >
            <template #icon>
              <NIcon>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2v6m0 0v6m0-6h6m-6 0H6"/>
                </svg>
              </NIcon>
            </template>
            开始生成
          </NButton>
        </div>
      </NCard>

      <NCard>
        <!-- 调试信息 -->
        <div class="mb-4">
          <NText strong>文件信息：</NText>
          <NText depth="3" class="ml-2">
            文件名: {{ uploadedFileData?.filename || '未知' }}
          </NText>
        </div>

        <!-- 文件内容预览 -->
        <div class="mb-4">
          <NText strong>文件内容：</NText>
          <div class="mt-2">
            <pre class="file-content">{{ JSON.stringify(filteredFileData, null, 2) }}</pre>
          </div>
        </div>
      </NCard>
    </div>

    <!-- 生成中页面 -->
    <div v-else-if="currentView === 'generating'" class="generating-page">
      <NCard title="肿瘤医院数据生成" class="max-w-2xl mx-auto mt-8">
        <div class="text-center">
          <!-- 加载动画 -->
          <div class="mb-6">
            <NIcon size="64" class="text-blue-500 animate-spin">
              <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12a9 9 0 11-6.219-8.56"/>
              </svg>
            </NIcon>
          </div>

          <!-- 进度条 -->
          <div class="mb-6">
            <NProgress
              type="line"
              :percentage="progress"
              :show-indicator="false"
              :height="8"
              color="#1890ff"
            />
          </div>

          <!-- 状态信息 -->
          <div class="mb-6">
            <NText size="large" class="text-gray-700">
              {{ status }}
            </NText>
          </div>

          <!-- 进度百分比 -->
          <div class="mb-6">
            <NText size="x-large" class="text-blue-600 font-bold">
              {{ Math.round(progress) }}%
            </NText>
          </div>

          <!-- 提示信息 -->
          <NAlert type="info" class="text-left">
            <template #header>
              <NIcon>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 16v-4"/>
                  <path d="M12 8h.01"/>
                </svg>
              </NIcon>
              处理提示
            </template>
            <p>正在使用 zhongliu.py 处理您的医疗数据，这可能需要一些时间。请耐心等待，不要关闭页面。</p>
          </NAlert>
        </div>
      </NCard>
    </div>

    <!-- 结果页面 -->
    <div v-else-if="currentView === 'result'">
      <NSpace vertical :size="16">
        <!-- 页面标题和操作按钮 -->
        <NGrid :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
          <NGi span="24 s:24 m:24">
            <NCard title="肿瘤医院生成结果" class="result-header-card">
              <template #header>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <NIcon size="20"><MedicalOutline /></NIcon>
                  <span>肿瘤医院生成结果</span>
                </div>
              </template>
              <div class="mb-4">
                <NText depth="3">
                  以下是您上传的肿瘤医院文件处理结果，已成功生成相应的医疗报告。
                </NText>
              </div>
              <div class="action-buttons">
                <NButton @click="handleBackToUpload" class="mr-2">
                  <NIcon><ArrowForwardOutline /></NIcon>
                  返回上传
                </NButton>
                <NButton @click="handleRegenerate" type="primary" class="mr-2">
                  <NIcon>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                      <path d="M21 3v5h-5"/>
                      <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                      <path d="M3 21v-5h5"/>
                    </svg>
                  </NIcon>
                  重新生成
                </NButton>
                <NButton @click="handleDownload" type="info">
                  <NIcon><DownloadOutline /></NIcon>
                  下载文件
                </NButton>
              </div>
            </NCard>
          </NGi>
        </NGrid>

        <!-- 生成结果表格 -->
        <div v-if="resultData?.processed_results">
          <NGrid :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
            <!-- 左侧：生成结果 -->
            <NGi span="24 s:12 m:12">
              <NCard title="生成结果" class="result-card">
                <template #header>
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <NIcon><MedicalOutline /></NIcon>
                    <span>生成结果</span>
                  </div>
                </template>
                <div class="result-table-container">
                  <table class="dynamic-table">
                    <colgroup>
                      <col style="width: 25%" />
                      <col style="width: 75%" />
                    </colgroup>
                    <tbody>
                      <tr>
                        <td class="table-cell field-label">主诉：</td>
                        <td class="table-cell field-content">
                          <span v-if="getResultData.zhusu" class="cell-wrapper">{{ getResultData.zhusu }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">初步诊断：</td>
                        <td class="table-cell field-content">
                          <span v-if="getResultData.chubuzhenduan" class="cell-wrapper">{{ getResultData.chubuzhenduan }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">超声：</td>
                        <td class="table-cell field-content">
                          <span v-if="getResultData.shiyanshi" class="cell-wrapper">{{ getResultData.shiyanshi }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">穿刺：</td>
                        <td class="table-cell field-content">
                          <span v-if="getResultData.xizhen" class="cell-wrapper">{{ getResultData.xizhen }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">CT：</td>
                        <td class="table-cell field-content">
                          <span v-if="getResultData.ct" class="cell-wrapper">{{ getResultData.ct }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">术后病理：</td>
                        <td class="table-cell field-content">
                          <span v-if="getResultData.shuhoubingli" class="cell-wrapper">{{ getResultData.shuhoubingli }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">现病史：</td>
                        <td class="table-cell field-content">
                          <span v-if="getResultData.xianbingshi" class="cell-wrapper">{{ getResultData.xianbingshi }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </NCard>
            </NGi>

            <!-- 右侧：医生版 -->
            <NGi span="24 s:12 m:12">
              <NCard title="医生版" class="result-card">
                <template #header>
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <NIcon><PersonOutline /></NIcon>
                    <span>医生版</span>
                  </div>
                </template>
                <div class="result-table-container">
                  <table class="dynamic-table">
                    <colgroup>
                      <col style="width: 25%" />
                      <col style="width: 75%" />
                    </colgroup>
                    <tbody>
                      <tr>
                        <td class="table-cell field-label">主诉：</td>
                        <td class="table-cell field-content">
                          <span v-if="getDoctorData.医生主诉" class="cell-wrapper">{{ getDoctorData.医生主诉 }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">初步诊断：</td>
                        <td class="table-cell field-content">
                          <span v-if="getDoctorData.医生初步诊断" class="cell-wrapper">{{ getDoctorData.医生初步诊断 }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">超声：</td>
                        <td class="table-cell field-content">
                          <span v-if="getDoctorData.查超声示" class="cell-wrapper">{{ getDoctorData.查超声示 }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">穿刺：</td>
                        <td class="table-cell field-content">
                          <span v-if="getDoctorData.行细针穿刺示" class="cell-wrapper">{{ getDoctorData.行细针穿刺示 }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">CT：</td>
                        <td class="table-cell field-content">
                          <span v-if="getDoctorData.颈部CT提示" class="cell-wrapper">{{ getDoctorData.颈部CT提示 }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">术后病理：</td>
                        <td class="table-cell field-content">
                          <span v-if="getDoctorData.术后病理" class="cell-wrapper">{{ getDoctorData.术后病理 }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                      <tr>
                        <td class="table-cell field-label">现病史：</td>
                        <td class="table-cell field-content">
                          <span v-if="getDoctorData.医生现病史" class="cell-wrapper">{{ getDoctorData.医生现病史 }}</span>
                          <span v-else class="cell-wrapper empty-content">暂无数据</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </NCard>
            </NGi>
          </NGrid>
        </div>

        <!-- 源文件内容展示 -->
        <NGrid :x-gap="16" :y-gap="16" responsive="screen" item-responsive v-if="resultData?.data">
          <NGi span="24 s:24 m:24">
            <NCard title="源文件内容" class="source-content-card">
              <template #header>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <NIcon><DocumentAttachOutline /></NIcon>
                  <span>源文件内容</span>
                </div>
              </template>
              <div class="mb-4">
                <NText depth="3">
                  以下是上传文件中的原始医疗数据内容，请从左侧菜单选择查看具体项目。
                </NText>
              </div>

              <!-- 源文件内容选择式展示 -->
              <div class="source-layout" style="height: calc(40vh)">
                <div class="source-sider">
                  <NMenu
                    :options="computedSourceMenuOptions"
                    :value="selectedSourceKey"
                    size="small"
                    @update:value="handleSourceMenuSelect"
                  />
                </div>
                <div class="source-content">
                  <div v-if="currentSourceContent" class="source-content-display">
                    <div class="source-content-text" v-html="formatText(currentSourceContent)"></div>
                  </div>
                  <div v-else class="source-content-empty">
                    <NText depth="3">请从左侧选择要查看的内容</NText>
                  </div>
                </div>
              </div>
            </NCard>
          </NGi>
        </NGrid>

        <!-- 如果没有结果数据，显示提示 -->
        <NGrid :x-gap="16" :y-gap="16" responsive="screen" item-responsive v-else>
          <NGi span="24 s:24 m:24">
            <NCard>
              <div class="result-content">
                <NText depth="3">暂无文件内容数据</NText>
              </div>
            </NCard>
          </NGi>
        </NGrid>
      </NSpace>
    </div>
  </div>
</template>

<style scoped>
::v-deep(.n-alert.n-alert--show-icon .n-alert-body) {
  padding-right: calc(var(--n-icon-margin-left) + var(--n-icon-size) + var(--n-icon-margin-right));
}
::v-deep(.n-divider:not(.n-divider--dashed) .n-divider__line) {
  background-color: var(--n-divider-color);
}

.generating-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.result-content {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.result-content pre {
  background: #f1f3f4;
  padding: 15px;
  border-radius: 6px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.file-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  max-height: 400px;
  overflow-y: auto;
}

/* 结果页面样式 - 参考审查页面设计 */
.result-header-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.result-header-card .n-card-header {
  background: transparent;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.result-header-card .n-card-header .n-card-header__main {
  color: white;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 结果卡片样式 */
.result-card {
  height: 100%;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s ease;
}

.result-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.result-card .n-card-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 2px solid #1890ff;
  border-radius: 12px 12px 0 0;
  padding: 16px 20px;
}

.result-card .n-card-header .n-card-header__main {
  color: #1890ff;
  font-weight: 600;
}

/* 表格容器 */
.result-table-container {
  padding: 0;
  overflow: hidden;
  border-radius: 0 0 12px 12px;
}

/* 动态表格样式 - 参考审查页面 */
.dynamic-table {
  font-family: 'SimSun', serif;
  width: 100%;
  table-layout: fixed;
  border: 2px solid rgba(238, 239, 241, 0.5);
  border-radius: 0 0 12px 12px;
  overflow: hidden;
}

.dynamic-table tr:nth-child(odd) {
  background-color: rgba(238, 239, 241, 0.3);
}

.dynamic-table tr:nth-child(even) {
  background-color: rgba(255, 255, 255, 0.8);
}

.dynamic-table tr:hover {
  background-color: rgba(24, 144, 255, 0.05);
  transition: background-color 0.3s ease;
}

.table-cell {
  padding: 12px 16px;
  vertical-align: top;
  border-bottom: 1px solid rgba(238, 239, 241, 0.5);
  font-family: 'SimSun', serif;
}

.field-label {
  font-weight: 600;
  color: #1890ff;
  background-color: rgba(24, 144, 255, 0.05);
  width: 25%;
  min-width: 120px;
  text-align: right;
  padding-right: 20px;
}

.field-content {
  color: #333;
  line-height: 1.6;
  word-break: break-word;
  padding-left: 20px;
}

/* 单元格包装器样式 */
.cell-wrapper {
  display: inline-block;
  white-space: normal;
  max-width: 100%;
  word-wrap: break-word;
  vertical-align: top;
  padding: 4px 8px;
  margin: 2px;
  border: 1px solid transparent;
  border-radius: 4px;
  transition: all 0.3s ease;
  font-family: 'SimSun', serif;
}

.cell-wrapper:hover {
  background-color: rgba(24, 144, 255, 0.1);
  border-color: rgba(24, 144, 255, 0.3);
}

.empty-content {
  color: #999;
  font-style: italic;
  background-color: rgba(153, 153, 153, 0.1);
}

/* 源文件内容卡片 */
.source-content-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  border: 1px solid #f0f0f0;
}

.source-content-card .n-card-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 2px solid #52c41a;
  border-radius: 12px 12px 0 0;
}

.source-content-card .n-card-header .n-card-header__main {
  color: #52c41a;
  font-weight: 600;
}

/* 源文件布局样式 */
.source-layout {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100%;
}

.source-sider {
  background: #fafafa;
  border-right: 1px solid #f0f0f0;
  flex-shrink: 0;
  width: 250px;
  overflow-y: auto;
}

.source-content {
  background: #ffffff;
  flex: 1;
  min-width: 0;
  padding: 16px;
  overflow-y: auto;
}

/* 源文件内容显示 */
.source-content-display {
  height: 100%;
  overflow-y: auto;
}

.source-content-text {
  font-family: 'SimSun', serif;
  line-height: 1.8;
  color: #333;
  white-space: pre-line;
  word-break: break-word;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.source-content-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-style: italic;
}

/* 菜单样式优化 */
.source-sider .n-menu {
  border: none;
  width: 100%;
  height: 100%;
  overflow-y: auto;
}

.source-sider .n-menu .n-menu-item {
  border-radius: 0;
  margin: 0;
  text-align: left;
  padding: 12px 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 44px;
  display: flex;
  align-items: center;
}

.source-sider .n-menu .n-menu-item:hover {
  background-color: rgba(82, 196, 26, 0.1);
}

.source-sider .n-menu .n-menu-item--selected {
  background-color: rgba(82, 196, 26, 0.2);
  color: #52c41a;
  font-weight: 600;
}

/* 菜单项文本样式 */
.source-sider .n-menu .n-menu-item-content {
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
  display: flex;
  align-items: center;
}

.source-sider .n-menu .n-menu-item-content__text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
  width: 100%;
  line-height: 1.4;
}

/* 文件内容样式 */
.file-item {
  margin-bottom: 16px;
}

.file-content-card {
  border-left: 4px solid #52c41a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.file-content-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.file-content-card .n-card-header {
  background: #f6ffed;
  border-bottom: 1px solid #b7eb8f;
  border-radius: 8px 8px 0 0;
}

.file-content-text {
  font-family: 'SimSun', serif;
  line-height: 1.8;
  color: #333;
  white-space: pre-line;
  word-break: break-word;
  padding: 16px;
  background: #fafafa;
  border-radius: 0 0 8px 8px;
}

/* 分页器样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .field-label {
    width: 30%;
    min-width: 100px;
    font-size: 14px;
    padding-right: 12px;
  }

  .field-content {
    font-size: 14px;
    padding-left: 12px;
  }

  .file-content-text {
    font-size: 14px;
    padding: 12px;
  }

  .action-buttons {
    flex-direction: column;
    gap: 8px;
  }

  .action-buttons .n-button {
    width: 100%;
  }

  /* 移动端源文件布局 */
  .source-layout {
    flex-direction: column;
  }

  .source-sider {
    width: 100%;
    height: auto;
    max-height: 200px;
    border-right: none;
    border-bottom: 1px solid #f0f0f0;
  }

  .source-content {
    flex: none;
    height: calc(40vh - 200px);
  }

  .source-sider .n-menu .n-menu-item {
    padding: 8px 12px;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .source-sider {
    max-height: 150px;
  }

  .source-content {
    height: calc(40vh - 150px);
  }
}

/* 加载动画 */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* 高亮效果 - 参考审查页面 */
.highlight {
  background-color: #e8efff;
  border-radius: 6px;
  color: #1890ff;
  transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 卡片内容区域 */
.result-card .n-card__content {
  padding: 0;
}

/* 表格行悬停效果增强 */
.dynamic-table tbody tr:hover .field-label {
  background-color: rgba(24, 144, 255, 0.1);
}

.dynamic-table tbody tr:hover .field-content {
  background-color: rgba(24, 144, 255, 0.05);
}

/* 空状态样式 */
.empty-content {
  display: inline-block;
  padding: 8px 12px;
  background: rgba(153, 153, 153, 0.1);
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  color: #999;
  font-style: italic;
}

/* 图标样式 */
.n-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* 按钮悬停效果 */
.action-buttons .n-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
