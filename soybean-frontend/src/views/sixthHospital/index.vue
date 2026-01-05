<script setup lang="ts">
import { defineOptions, ref } from 'vue';
import { useMessage } from 'naive-ui';
import { GenerateSixthHospital, UploadSixthHospitalFiles } from '@/service/api/configureTask';

defineOptions({
  name: 'SixthHospital'
});

const message = useMessage();

const uploadSuccess = ref(false);
const uploadedFileData = ref<any>(null);
const currentView = ref<'upload' | 'generating' | 'result'>('upload');
const progress = ref(0);
const status = ref('正在初始化...');
const resultData = ref<any>(null);

// 示例图片文件列表
const imageSampleFiles = ref([
  {
    name: '肩关节镜手术记录示例.jpg',
    url: '/samples/shoulder_surgery_record.jpg'
  }
]);

// 处理文件上传
const handleUpload = async (options: any) => {
  const { file, onFinish, onError } = options;

  try {
    const formData = new FormData();
    formData.append('file', file.file);

        const response = await UploadSixthHospitalFiles(
      { 'Content-Type': 'multipart/form-data' },
      formData
    );

    // 由于 transformBackendResponse 会提取 response.data.data
    // 所以这里直接使用 response 就是 data 字段的内容
    console.log('上传响应:', response);
    if (response) {
      message.success('图片上传成功！');
      uploadSuccess.value = true;
      uploadedFileData.value = response;
      console.log('设置的上传文件数据:', uploadedFileData.value);
    } else {
      message.error('上传失败');
      onError();
    }
    } catch (error: any) {
    console.error('上传失败:', error);
    message.error(error?.message || '上传失败，请重试');
    onError();
  }

  onFinish();
};

// 处理生成
const handleGenerate = async () => {
  console.log('点击生成按钮，当前文件数据:', uploadedFileData.value);
  currentView.value = 'generating';

  try {
    // 模拟进度更新
    const updateProgress = () => {
      const interval = setInterval(() => {
        if (progress.value < 90) {
          progress.value += Math.random() * 10;
          if (progress.value < 30) {
            status.value = '正在读取图片数据...';
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
    const requestData = {
      filename: uploadedFileData.value.filename
    };
    console.log('发送给后端的数据:', requestData);

    const response = await GenerateSixthHospital(requestData);

    // 处理成功响应
    progress.value = 100;
    status.value = '生成完成！';

    // 清理定时器
    clearInterval(progressInterval);

    // 添加调试信息
    console.log('生成API响应:', response);
    console.log('响应类型:', typeof response);
    console.log('响应数据结构:', {
      hasData: Boolean(response),
      dataKeys: response ? Object.keys(response) : [],
      dataType: typeof response
    });

    // 延迟显示结果
    setTimeout(() => {
      // 尝试不同的数据结构
      if (response && response.data) {
        resultData.value = response.data;
      } else if (response) {
        resultData.value = response;
      } else {
        resultData.value = { message: '生成完成，但未返回数据' };
      }

      console.log('设置的结果数据:', resultData.value);
      currentView.value = 'result';
    }, 1000);

  } catch (error) {
    console.error('生成失败:', error);
    message.error('生成失败，请重试');
    currentView.value = 'upload';
  }
};

// 返回上传页面
const handleBackToUpload = () => {
  currentView.value = 'upload';
  uploadSuccess.value = false;
  uploadedFileData.value = null;
  progress.value = 0;
  status.value = '正在初始化...';
  resultData.value = null;
};

// 重新生成
const handleRegenerate = () => {
  currentView.value = 'upload';
  uploadSuccess.value = false;
  uploadedFileData.value = null;
  progress.value = 0;
  status.value = '正在初始化...';
  resultData.value = null;
};

// 下载结果
const handleDownload = () => {
  if (!resultData.value) return;

  let content = '';
  if (typeof resultData.value === 'string') {
    content = resultData.value;
  } else if (typeof resultData.value === 'object' && resultData.value !== null) {
    content = `六院手术记录生成结果

【基本信息】
${resultData.value.basicInfo || ''}

【术中发现】
${resultData.value.findings || ''}

【手术过程】
${resultData.value.procedure || ''}

生成时间: ${new Date().toLocaleString()}`;
  } else {
    content = String(resultData.value);
  }

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `六院手术记录_${new Date().toISOString().split('T')[0]}.txt`;
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
      <NCard title="六院生成" class="mb-4">
        <NText depth="3">
          欢迎使用六院生成功能。请上传您的医疗记录图片，系统将为您生成相应的医疗报告。
        </NText>
      </NCard>

      <NUpload
        :max="1"
        accept=".jpg,.jpeg,.png,.bmp,.gif"
        @change="handleUpload"
      >
        <NUploadDragger>
          <div style="margin-bottom: 12px">
            <NIcon size="48" :depth="3">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21,15 16,10 5,21"/>
              </svg>
            </NIcon>
          </div>
          <NText style="font-size: 16px">单击或将图片拖到此区域进行上传。</NText>
          <NP depth="3" style="margin: 8px 0 0 0">
            支持 JPG、PNG、BMP、GIF 等图片格式，请不要上传敏感数据
          </NP>
        </NUploadDragger>
      </NUpload>

      <!-- 生成按钮 -->
      <div v-if="uploadSuccess" class="mt-4">
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

      <NGrid cols="2" x-gap="16" class="mt-4">
        <!-- 左侧：操作说明 -->
        <NGridItem>
          <NAlert title="操作说明" type="info">
            <p>上传图片之前，请按照以下说明操作：</p>
            <ol>
              <li>
                <strong>图片格式要求：</strong> 支持 JPG、PNG、BMP、GIF 等常见图片格式。
              </li>
              <li>
                <strong>图片质量：</strong> 请确保图片清晰可读，文字内容完整。
              </li>
              <li>
                <strong>文件大小：</strong> 建议图片大小不超过 10MB。
              </li>
              <li>
                <strong>隐私保护：</strong> 请确保上传的图片不包含敏感的个人信息。
              </li>
            </ol>
          </NAlert>

          <!-- 支持的文件类型说明 -->
          <NCard title="支持的文件类型" style="margin-top: 16px">
            <NList hoverable>
              <NListItem>
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%">
                  <div>
                    <NText strong>图片文件</NText>
                    <br />
                    <NText depth="3" style="font-size: 12px">医疗记录、检查报告等图片格式文件</NText>
                  </div>
                  <NTag :bordered="false" type="info" size="small">
                    .jpg, .jpeg, .png, .bmp, .gif
                  </NTag>
                </div>
              </NListItem>
            </NList>
          </NCard>
        </NGridItem>

        <!-- 右侧：示例文件列表 -->
        <NGridItem>
          <!-- 示例图片 -->
          <NCard title="示例图片">
            <NList hoverable style="overflow: auto; padding: 0; border: none">
              <NListItem v-for="file in imageSampleFiles" :key="file.name">
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%">
                  <div>
                    <NText strong>{{ file.name }}</NText>
                    <br />
                    <NText depth="3" style="font-size: 12px">示例医疗记录图片</NText>
                  </div>
                  <a :href="file.url" target="_blank" rel="noopener noreferrer" style="text-decoration: none;">
                    <NButton size="small">
                      查看
                    </NButton>
                  </a>
                </div>
              </NListItem>
            </NList>
          </NCard>
        </NGridItem>
      </NGrid>
    </div>

    <!-- 生成中页面 -->
    <div v-else-if="currentView === 'generating'" class="generating-page">
      <NCard title="六院数据生成" class="max-w-2xl mx-auto mt-8">
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
            <p>正在使用 three_extract.py 处理您的医疗图片，这可能需要一些时间。请耐心等待，不要关闭页面。</p>
          </NAlert>
        </div>
      </NCard>
    </div>

    <!-- 结果页面 -->
    <div v-else-if="currentView === 'result'">
      <NCard title="六院生成结果" class="mb-4">
        <div class="mb-4">
          <NButton @click="handleBackToUpload" class="mr-2">
            返回上传
          </NButton>
          <NButton @click="handleRegenerate" type="primary" class="mr-2">
            重新生成
          </NButton>
          <NButton @click="handleDownload" type="info">
            下载结果
          </NButton>
        </div>
      </NCard>

      <NCard v-if="resultData">
        <div class="result-content">
          <!-- 如果是字符串（文本描述），直接显示 -->
          <div v-if="typeof resultData === 'string'">
            <h3>生成的手术记录</h3>
            <div class="text-content">
              <NText>{{ resultData }}</NText>
            </div>
          </div>

          <!-- 如果是对象，尝试显示特定字段 -->
          <div v-else-if="typeof resultData === 'object' && resultData !== null">
            <div v-if="resultData.basicInfo || resultData.findings || resultData.procedure">
              <div v-if="resultData.basicInfo" class="mb-4">
                <h3>基本信息</h3>
                <NText>{{ resultData.basicInfo }}</NText>
              </div>
              <div v-if="resultData.findings" class="mb-4">
                <h3>术中发现</h3>
                <NText>{{ resultData.findings }}</NText>
              </div>
              <div v-if="resultData.procedure" class="mb-4">
                <h3>手术过程</h3>
                <NText>{{ resultData.procedure }}</NText>
              </div>
            </div>

            <!-- 如果没有特定字段，显示原始JSON数据 -->
            <div v-else>
              <h3>生成结果</h3>
              <pre>{{ JSON.stringify(resultData, null, 2) }}</pre>
            </div>
          </div>

          <!-- 其他情况 -->
          <div v-else>
            <h3>生成结果</h3>
            <NText>{{ resultData }}</NText>
          </div>
        </div>
      </NCard>

      <!-- 如果没有结果数据，显示提示 -->
      <NCard v-else>
        <div class="result-content">
          <NText depth="3">暂无生成结果数据</NText>
        </div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
::v-deep(.n-alert.n-alert--show-icon .n-alert-body) {
  padding-right: calc(var(--n-icon-margin-left) + var(--n-icon-size) + var(--n-icon-margin-right));
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

.result-content h3 {
  color: #495057;
  margin-bottom: 10px;
  font-weight: 600;
}

.result-content .text-content {
  background: #ffffff;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  line-height: 1.6;
  white-space: pre-wrap;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
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
</style>
