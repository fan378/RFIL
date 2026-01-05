<script setup lang="ts">
import { defineOptions, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

defineOptions({
  name: 'SixthHospitalResult'
});

const router = useRouter();
const route = useRoute();
const resultData = ref<any>(null);

// 解析结果数据
const parseResultData = (data: any) => {
  const sections: Record<string, string> = {
    basicInfo: '',
    findings: '',
    procedure: ''
  };

  console.log('开始解析数据:', data);

    if (typeof data === 'string') {
    // 如果是字符串，尝试解析为三个部分
    console.log('数据是字符串类型，开始解析...');
    console.log('原始字符串数据:', data);

    const lines = data.split('\n');
    let currentSection = '';

    for (const line of lines) {
      const trimmedLine = line.trim();
      console.log('处理行:', trimmedLine);

      if (trimmedLine.includes('【基本信息】')) {
        currentSection = 'basicInfo';
        console.log('找到基本信息部分');
      } else if (trimmedLine.includes('【术中发现】')) {
        currentSection = 'findings';
        console.log('找到术中发现部分');
      } else if (trimmedLine.includes('【手术过程】')) {
        currentSection = 'procedure';
        console.log('找到手术过程部分');
      } else if (currentSection && trimmedLine) {
        sections[currentSection] = `${sections[currentSection]}${line}\n`;
        console.log(`添加到${currentSection}:`, line);
      }
    }

    console.log('解析完成，各部分内容长度:', {
      basicInfo: sections.basicInfo.length,
      findings: sections.findings.length,
      procedure: sections.procedure.length
    });

    console.log('各部分内容预览:', {
      basicInfo: `${sections.basicInfo.substring(0, 100)}...`,
      findings: `${sections.findings.substring(0, 100)}...`,
      procedure: `${sections.procedure.substring(0, 100)}...`
    });
  } else if (typeof data === 'object' && data !== null) {
    // 如果是对象，直接提取对应字段
    console.log('数据是对象类型，直接提取字段...');
    sections.basicInfo = data.basicInfo || data['基本信息'] || '';
    sections.findings = data.findings || data['术中发现'] || '';
    sections.procedure = data.procedure || data['手术过程'] || '';
  }

  // 清理多余的空行
  Object.keys(sections).forEach(key => {
    sections[key] = sections[key].trim();
  });

  return sections;
};

// 返回上传页面
const handleBackToUpload = () => {
  router.push({ path: '/sixthhospital' });
};

// 重新生成
const handleRegenerate = () => {
  router.push({ path: '/sixthhospital' });
};

// 下载结果
const handleDownload = () => {
  if (!resultData.value) return;

  const content = `六院手术记录生成结果

【基本信息】
${resultData.value.basicInfo}

【术中发现】
${resultData.value.findings}

【手术过程】
${resultData.value.procedure}

生成时间: ${new Date().toLocaleString()}`;

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

onMounted(() => {
  try {
    const result = route.query.result;
    if (result) {
      const parsedData = JSON.parse(result as string);
      console.log('原始结果数据:', parsedData);
      console.log('数据类型:', typeof parsedData);

      // 处理嵌套的数据结构
      let actualData = parsedData;
      if (parsedData && typeof parsedData === 'object' && parsedData.data) {
        actualData = parsedData.data;
        console.log('提取的data字段:', actualData);
      }

      // 解析数据为三个部分
      resultData.value = parseResultData(actualData);
      console.log('解析后的结果数据:', resultData.value);
    }
  } catch (error) {
    console.error('解析结果数据失败:', error);
  }
});
</script>

<template>
  <div class="result-page">
    <!-- 页面标题 -->
    <NCard title="六院手术记录生成结果" class="mb-6">
      <NText depth="3">
        以下是使用 three_extract.py 处理后的手术记录生成结果，包含患者基本信息、术中发现和手术过程三个部分。
      </NText>

      <!-- 操作按钮 -->
      <div class="mt-6 flex gap-4 flex-wrap">
        <NButton @click="handleBackToUpload" size="large">
          <template #icon>
            <NIcon>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 12H5"/>
                <path d="M12 19l-7-7 7-7"/>
              </svg>
            </NIcon>
          </template>
          返回上传页面
        </NButton>

        <NButton type="primary" @click="handleRegenerate" size="large">
          <template #icon>
            <NIcon>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                <path d="M21 3v5h-5"/>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                <path d="M3 21v-5h5"/>
              </svg>
            </NIcon>
          </template>
          重新生成
        </NButton>

        <NButton type="success" @click="handleDownload" size="large">
          <template #icon>
            <NIcon>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7,10 12,15 17,10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </NIcon>
          </template>
          下载结果
        </NButton>
      </div>
    </NCard>

    <!-- 结果展示 -->
    <div v-if="resultData" class="result-content">
      <!-- 基本信息 -->
      <NCard title="基本信息" class="mb-6" size="large">
        <div class="info-section">
          <NIcon size="24" class="section-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </NIcon>
          <div class="content-text">
            {{ resultData.basicInfo || '暂无基本信息' }}
          </div>
        </div>
      </NCard>

      <!-- 术中发现 -->
      <NCard title="术中发现" class="mb-6" size="large">
        <div class="info-section">
          <NIcon size="24" class="section-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
          </NIcon>
          <div class="content-text">
            {{ resultData.findings || '暂无术中发现' }}
          </div>
        </div>
      </NCard>

      <!-- 手术过程 -->
      <NCard title="手术过程" class="mb-6" size="large">
        <div class="info-section">
          <NIcon size="24" class="section-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
          </NIcon>
          <div class="content-text">
            {{ resultData.procedure || '暂无手术过程' }}
          </div>
        </div>
      </NCard>
    </div>

    <!-- 无数据提示 -->
    <div v-else class="no-data">
      <NCard>
        <NEmpty description="暂无生成结果数据">
          <template #icon>
            <NIcon size="64" :depth="3">
              <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <path d="m21 21-4.35-4.35"/>
              </svg>
            </NIcon>
          </template>
        </NEmpty>

        <!-- 调试信息 -->
        <div class="mt-4">
          <NAlert type="warning" title="调试信息">
            <p>原始查询参数: {{ route.query.result }}</p>
            <p>解析后的数据: {{ resultData }}</p>
          </NAlert>
        </div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.result-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.result-content {
  animation: fadeIn 0.5s ease-in-out;
}

.info-section {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.section-icon {
  color: #1890ff;
  flex-shrink: 0;
  margin-top: 4px;
}

.content-text {
  flex: 1;
  line-height: 1.8;
  font-size: 14px;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #1890ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.no-data {
  text-align: center;
  padding: 60px 20px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .result-page {
    padding: 10px;
  }

  .info-section {
    flex-direction: column;
    gap: 12px;
  }

  .section-icon {
    align-self: center;
  }

  .content-text {
    padding: 16px;
    font-size: 13px;
  }
}
</style>
