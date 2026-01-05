<script setup lang="ts">
import { computed, defineProps, h, nextTick, onMounted, reactive, ref, watch } from 'vue';
import {
  NGi,
  NGrid,
  NHighlight,
  NIcon,
  NLayout,
  NLayoutContent,
  NLayoutHeader,
  NLayoutSider,
  NMenu,
  type MenuOption as NaiveMenuOption,
  useThemeVars
} from 'naive-ui';
import { BookOutline as BookIcon } from '@vicons/ionicons5';
import { useAppStore } from '@/store/modules/app';
import { useTaskStore } from '@/store/modules/task';
import ceshiJson from './ceshi.json';

interface Source {
  [key: string]: {
    [key: string]: string;
  };
}

interface MenuOption {
  label: string;
  key: string;
}

defineOptions({
  name: 'SourceTracing'
});

// 接收父组件传递的 prop
const props = defineProps({
  receivedClickItem: {
    type: String
  }
});

const appStore = useAppStore();
const taskStore = useTaskStore();
const gap = computed(() => (appStore.isMobile ? 0 : 16));

// 来源数据
const source = reactive<Source>(taskStore.processedJson.source);
const source_pattern = reactive<SourcePattern>(taskStore.processedJson.source_pattern);
//const source_pattern = reactive(ceshiJson.data.source_pattern as Record<string, any>);

// 初始化菜单
const hlItem = ref('');
const selectedKey = ref('');
const patterns = ref<string[]>(['']);
const menuOptions = ref<MenuOption[]>([]);

// 处理模式数据
const processPatternData = (category: string, id: string, subId: string) => {
  console.log('处理模式数据:', { category, id, subId });
  const pattern = source_pattern[category];
  console.log('获取到的pattern:', pattern);

  if (!Array.isArray(pattern)) {
    console.log('pattern不是数组，返回');
    return;
  }

  if (category === '住院期间医疗情况') {
    console.log('处理住院期间医疗情况');
    if (id === '' || subId === '') {
      patterns.value = [];
      console.log('缺少索引信息');
      return;
    }
    const index1 = Number(id);
    const index2 = Number(subId);
    console.log('索引:', { index1, index2 });
    if (!Array.isArray(pattern[index1])) {
      patterns.value = [];
      console.log('第一层数组不存在');
      return;
    }
    const arr = pattern[index1];
    if (arr.length === 1) {
      // 只有一个元素，无论点哪个都高亮这个
      const value = arr[0];
      console.log('唯一元素:', value);
      if (Array.isArray(value)) {
        patterns.value = value as string[];
        console.log('设置patterns(数组):', patterns.value);
      } else if (typeof value === 'string') {
        patterns.value = [value];
        console.log('设置patterns(字符串):', patterns.value);
      } else {
        patterns.value = [];
        console.log('设置patterns(其他):', patterns.value);
      }
    } else {
      // 多个元素，按索引取
      const value = arr[index2];
      console.log('多元素，取索引:', value);
      if (Array.isArray(value)) {
        patterns.value = value as string[];
        console.log('设置patterns(数组):', patterns.value);
      } else if (typeof value === 'string') {
        patterns.value = [value];
        console.log('设置patterns(字符串):', patterns.value);
      } else {
        patterns.value = [];
        console.log('设置patterns(其他):', patterns.value);
      }
    }
  } else if (id !== '') {
    if (subId !== '') {
      // 处理三维数组的情况
      const subPattern = pattern[Number(id)];
      if (Array.isArray(subPattern) && Array.isArray(subPattern[Number(subId)])) {
        patterns.value = subPattern[Number(subId)] as string[];
      }
    } else {
      // 处理二维数组的情况
      const subPattern = pattern[Number(id)];
      if (Array.isArray(subPattern)) {
        patterns.value = subPattern as string[];
      }
    }
  } else {
    patterns.value = pattern as string[];
  }
};

// 更新菜单选项
const updateMenuOptions = (category: string) => {
  const options: MenuOption[] = [];
  if (source && source[category] && typeof source[category] === 'object') {
    Object.entries(source[category]).forEach(([key, _value]) => {
      options.push({
        label: key,
        key
      });
    });
  }
  menuOptions.value = options;
  return options;
};

// 查找匹配的选项
const findMatchingOption = (options: MenuOption[], category: string) => {
  console.log('查找匹配选项:', { options, category });
  // 第一次循环：精确匹配
  for (const option of options) {
    const content = source[category][option.key];
    console.log('检查选项:', { key: option.key, content });
    if (content && typeof content === 'string') {
      const highlightText = patterns.value[0];
      console.log('高亮文本:', highlightText);
      if (highlightText && content.includes(highlightText)) {
        console.log('找到精确匹配:', option.key);
        return option.key;
      }
    }
  }

  // 如果没有找到精确匹配，且高亮文本不为空，进行模糊匹配
  const highlightText = patterns.value[0];
  if (highlightText) {
    console.log('开始模糊匹配');

    // 预处理：获取高亮文本的所有字（去重）
    const highlightChars = [...new Set(highlightText.replace(/\s+/g, ''))];
    console.log('高亮文本字集合:', highlightChars);

    for (const option of options) {
      const content = source[category][option.key];

      if (content && typeof content === 'string') {
        // 将内容按句子分割（使用中文标点符号作为分隔符）
        const sentences = content.split(/[。！？!?;]/g).filter(s => s.trim());

        for (const sentence of sentences) {
          // 计算高亮文本中出现在当前句子中的字数
          const matchedChars = highlightChars.filter(char =>
            sentence.includes(char)
          );

          // 计算匹配比例
          const matchRatio = matchedChars.length / highlightChars.length;
          console.log('句子匹配度:', {
            sentence,
            matchedChars,
            matchRatio
          });

          // 如果匹配比例达到50%，返回匹配结果
          if (matchRatio >= 0.5) {
            console.log('找到模糊匹配:', {
              option: option.key,
              sentence,
              matchRatio: `${(matchRatio * 100).toFixed(1)}%`
            });
            // 更新高亮文本为匹配到的句子
            patterns.value = [sentence];
            return option.key;
          }
        }
      }
    }
  }

  console.log('未找到匹配，返回第一个选项');
  return options.length > 0 ? options[0].key : '';
};

// 执行基于点击项的函数
const executeFunctionBasedOnClickItem = (clickItem: string) => {
  console.log('执行点击项函数:', clickItem);
  const parts = clickItem.split('-');
  const category = parts[0];
  const id = parts.length > 1 ? parts[1] : '';
  const subId = parts.length > 2 ? parts[2] : '';
  console.log('解析结果:', { category, id, subId });

  hlItem.value = category;
  processPatternData(category, id, subId);

  const options = updateMenuOptions(category);
  console.log('菜单选项:', options);
  selectedKey.value = findMatchingOption(options, category);
  console.log('选中的key:', selectedKey.value);

  nextTick(() => {
    setTimeout(() => {
      const highlightedElements = document.querySelectorAll('.n-highlight mark');
      console.log('找到的高亮元素:', highlightedElements.length);
      if (highlightedElements.length > 0) {
        const firstHighlightedElement = highlightedElements[0];
        firstHighlightedElement.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }
    }, 200);
  });
};

// 检查元素是否需要高亮
const checkElementHighlight = (element: Element, category: string, indexNumber: string) => {
  const id = element.id;
  // 1. 医生开头直接跳过
  if (id.startsWith('医生')) {
    //console.log('[高亮检查] 跳过医生元素:', id);
    return;
  }
  // 2. 病人开头，分情况
  if (id.startsWith('病人-')) {
    const parts = id.substring(3).split('-');
    const mainCategory = parts[0];
    // 住院期间医疗情况特殊处理
    if (mainCategory === '住院期间医疗情况') {
      const index1 = Number(parts[1]);
      // 检查 source_pattern['住院期间医疗情况'][index1] 是否有内容
      const arr = source_pattern['住院期间医疗情况']?.[index1];
      //console.log('[高亮检查] 病人-住院期间医疗情况:', id, 'index1:', index1, 'arr:', arr);
      if (Array.isArray(arr) && arr.length > 0) {
        element.classList.remove('highlightrellynull');
        //console.log('[高亮检查] 有内容，移除 highlightrellynull');
      } else {
        element.classList.add('highlightrellynull');
        //console.log('[高亮检查] 无内容，添加 highlightrellynull');
      }
      //console.log('[样式检查] 当前classList:', Array.from(element.classList));
      setTimeout(() => {
        const computedStyle = window.getComputedStyle(element);
        //console.log('[样式检查] background:', computedStyle.background, 'color:', computedStyle.color, 'border:', computedStyle.border);
      }, 0);
      return;
    }
    // 其他情况，比如"病人-出院后用药建议-0"
    const index = Number(parts[1]);
    const arr = source_pattern[mainCategory];
    //console.log('[高亮检查] 病人-其他:', id, 'mainCategory:', mainCategory, 'index:', index, 'arr:', arr);
    if (Array.isArray(arr) && arr[index] !== undefined) {
      element.classList.remove('highlightrellynull');
      //console.log('[高亮检查] 有内容，移除 highlightrellynull');
    } else {
      element.classList.add('highlightrellynull');
      //console.log('[高亮检查] 无内容，添加 highlightrellynull');
    }
    //console.log('[样式检查] 当前classList:', Array.from(element.classList));
    setTimeout(() => {
      const computedStyle = window.getComputedStyle(element);
      //console.log('[样式检查] background:', computedStyle.background, 'color:', computedStyle.color, 'border:', computedStyle.border);
    }, 0);
    return;
  }
  // 其他情况，保持原有逻辑
  const categoryData = source_pattern[category];
  if (!Array.isArray(categoryData) || categoryData.length === 0) {
    element.classList.add('highlightrellynull');
    //console.log('[高亮检查] 其他情况 categoryData 为空或不存在，添加 highlightrellynull');
    //console.log('[样式检查] 当前classList:', Array.from(element.classList));
    setTimeout(() => {
      const computedStyle = window.getComputedStyle(element);
      //console.log('[样式检查] background:', computedStyle.background, 'color:', computedStyle.color, 'border:', computedStyle.border);
    }, 0);
    return;
  }
  const indexNum = Number.parseInt(indexNumber, 10);
  const hasIndex = categoryData.some(item => {
    if (Array.isArray(item)) {
      return item.some(subItem => Number(subItem) === indexNum);
    }
    return Number(item) === indexNum;
  });
  if (!hasIndex) {
    element.classList.add('highlightrellynull');
    //console.log('[高亮检查] 其他情况 未找到 index，添加 highlightrellynull');
  } else {
    element.classList.remove('highlightrellynull');
    //console.log('[高亮检查] 其他情况 找到 index，移除 highlightrellynull');
  }
  //console.log('[样式检查] 当前classList:', Array.from(element.classList));
  setTimeout(() => {
    const computedStyle = window.getComputedStyle(element);
    //console.log('[样式检查] background:', computedStyle.background, 'color:', computedStyle.color, 'border:', computedStyle.border);
  }, 0);
};

// 添加检查函数
const checkHighlightNull = () => {
  const elements = document.querySelectorAll('.highlightnull, .highlightrellynull, .n-highlight');
  const timeRegex = /^\d{4}-\d{2}-\d{2}$/;
  const admissionTimeId = '病人-入院时间';
  const dischargeTimeId = '病人-出院时间';

  elements.forEach((element) => {
    const id = element.id;

    if (timeRegex.test(element.textContent?.trim() || '') && id !== admissionTimeId && id !== dischargeTimeId) {
      return;
    }

    if (id.startsWith('病人-')) {
      const index = id.substring(3);
      const [category, indexNumber] = index.split('-');
      checkElementHighlight(element, category, indexNumber);
    } else {
      const parts = id.split('-');
      if (parts.length >= 2) {
        const [category, indexNumber] = parts;
        checkElementHighlight(element, category, indexNumber);
      }
    }
  });
};

// 监听 receivedClickItem 变化并执行函数
watch(
  () => props.receivedClickItem,
  (newVal) => {
    if (newVal) {
      executeFunctionBasedOnClickItem(newVal);
    }
  }
);

// 监听 patterns 变化
watch(
  () => patterns.value,
  () => {
    checkHighlightNull();
    nextTick(() => {
      const highlightedElements = document.querySelectorAll('.n-highlight mark');
      if (highlightedElements.length > 0) {
        const firstHighlightedElement = highlightedElements[0];
        setTimeout(() => {
          firstHighlightedElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
          });
        }, 100);
      }
    });
  },
  { deep: true }
);

// 在组件挂载时执行检查
onMounted(() => {
  checkHighlightNull();
});

// 初始化
executeFunctionBasedOnClickItem('姓名');

// 监听菜单选择
const handleMenuSelect = (key: string) => {
  selectedKey.value = key;
  nextTick(() => {
    const highlightedElements = document.querySelectorAll('.n-highlight mark');
    if (highlightedElements.length > 0) {
      const firstHighlightedElement = highlightedElements[0];
      setTimeout(() => {
        firstHighlightedElement.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }, 100);
    }
  });
};

// 样式变量
const themeVars = useThemeVars();

// 渲染菜单图标
const collapsed = ref(false);
const renderMenuIcon = (option: NaiveMenuOption) => {
  if (option.key === 'sheep-man') return h(NIcon, null, { default: () => h(BookIcon) });
  return undefined;
};
</script>

<template>
  <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
    <NGi span="24 s:24 m:24">
      <NLayout class="card-wrapper" style="height: calc(30vh)">
        <NLayoutHeader
          class="text-14px"
          style="text-align: center; font-weight: 600; padding: 6px; height: 32px"
          bordered
        >
          来源文书
        </NLayoutHeader>
        <NLayout has-sider position="absolute" style="top: 32px">
          <NLayoutSider bordered :native-scrollbar="false">
            <NMenu
              :collapsed="collapsed"
              :collapsed-width="64"
              :collapsed-icon-size="22"
              :options="menuOptions"
              :render-icon="renderMenuIcon"
              :value="selectedKey"
              size="small"
              @update:value="handleMenuSelect"
            />
          </NLayoutSider>
          <NLayoutContent content-style="padding: 12px;" :native-scrollbar="false">
            <NHighlight
              :text="source[hlItem][selectedKey]"
              :patterns="patterns"
              class="white-space"
              :highlight-style="{
                padding: '0 6px',
                borderRadius: themeVars.borderRadius,
                display: 'inline-block',
                // color: themeVars.baseColor,
                color: themeVars.primaryColor,
                // background: themeVars.primaryColor,
                transition: `all .3s ${themeVars.cubicBezierEaseInOut}`,
                background: '#e8efff'
              }"
            />
          </NLayoutContent>
        </NLayout>
      </NLayout>
    </NGi>
  </NGrid>
</template>

<style scoped>
.white-space {
  white-space: pre-line;
  font-family: 'SimSun', serif; /* 宋体 */
}
:deep(.highlightrellynull) {
  background: #ffeaea !important;
  color: #d8000c !important;
  border-radius: 4px;
  border: 1px solid #d8000c;
}
</style>
