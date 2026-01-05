<script setup lang="ts">
import { watch } from 'vue';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'HeatmapChart'
});

const appStore = useAppStore();

// Define mock data structure for heatmap
const departments = [
  $t('page.home.breastSurgery'),
  $t('page.home.gastrointestinalSurgery'),
  $t('page.home.thyroidAndVascularSurgery'),
  $t('page.home.otorhinolaryngology'),
  $t('page.home.neurosurgery'),
  $t('page.home.neurology'),
  $t('page.home.gastroenterology'),
  $t('page.home.pulmonology'),
  $t('page.home.endocrinology'),
  $t('page.home.nephrology'),
  $t('page.home.oncology'),
  $t('page.home.traditionalChineseMedicine'),
  $t('page.home.pediatrics'),
  $t('page.home.ophthalmology'),
  $t('page.home.gynecology')
];
const days = ['BenTaso', 'Alpacare', 'Qwen2', 'Chatglm3', 'HuaTuo', 'EMR-LLM'];
// const blue1 = getComputedStyle(document.documentElement).getPropertyValue('--blue-1').trim();
// const blue15 = getComputedStyle(document.documentElement).getPropertyValue('--blue-15').trim();
// Common mock data
const heatmapData = [
  [0.8, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.9, 0.91, 0.92, 0.93, 0.94],
  [0.45, 0.46, 0.47, 0.48, 0.49, 0.5, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59],
  [0.67, 0.68, 0.69, 0.7, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.8, 0.81],
  [0.78, 0.79, 0.8, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.9, 0.91, 0.92],
  [0.6, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.7, 0.71, 0.72, 0.73, 0.74],
  [0.89, 0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 0.94, 0.95, 0.96, 0.97]
];
const heatmapDataFormatted = [];
heatmapData.forEach((row, y) => {
  row.forEach((value, x) => {
    heatmapDataFormatted.push([x, y, value]);
  });
});

const { domRef, updateOptions } = useEcharts(() => ({
  tooltip: {
    position: 'top'
  },
  grid: {
    height: '90%',
    top: '0%',
    width: '88%'
  },
  xAxis: {
    type: 'category',
    data: departments,
    splitArea: {
      show: true
    },
    axisLabel: {
      show: true, // Ensure labels are shown
      interval: 3, // This ensures that all labels are displayed
      fontSize: 8 // Set the font size for x-axis labels
    }
  },
  yAxis: {
    type: 'category',
    data: days,
    splitArea: {
      show: true
    },
    axisLabel: {
      show: true, // Ensure labels are shown
      interval: 0, // This ensures that all labels are displayed
      fontSize: 8 // Set the font size for x-axis labels
    }
  },
  visualMap: {
    min: 0,
    max: 1,
    show: false,
    calculable: true,
    orient: 'vertical', // 设置为垂直方向
    right: '0%', // 图例靠右
    top: 'center', // 垂直居中
    inRange: {
      color: ['#E2EAF9', '#BDD7EE', '#6495ED'] // Define the color gradient from light blue to dark blue
    }
  },
  series: [
    {
      // name: 'Punch Card',
      type: 'heatmap',
      data: heatmapDataFormatted,
      label: {
        show: true,
        fontSize: 8
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }
  ]
}));

// Function to update options with data
function updateHeatmapData() {
  updateOptions((opts, factory) => {
    const originOpts = factory();
    opts.series[0].name = originOpts.series[0].name;
    opts.series[0].data = heatmapDataFormatted; // Reuse common data
    return opts;
  });
}

async function mockData() {
  await new Promise(resolve => {
    setTimeout(resolve, 1000);
  });
  updateHeatmapData();
}

function updateLocale() {
  updateOptions((opts, factory) => {
    const originOpts = factory();
    opts.series[0].name = originOpts.series[0].name;
    opts.series[0].data = heatmapDataFormatted; // Reuse common data
    return opts;
  });
}

async function init() {
  await mockData();
}

watch(
  () => appStore.locale,
  () => {
    updateLocale();
  }
);

// Initialize the chart with mock data
init();
</script>

<template>
  <NCard
    :segmented="{
      content: true,
      footer: 'soft'
    }"
    size="small"
    :bordered="false"
    class="card-wrapper"
    header-style="padding: 6px var(--n-padding-left) 6px var(--n-padding-left);"
  >
    <template #header>
      <strong>跨模型质量比较</strong>
    </template>
    <div ref="domRef" class="h-150px"></div>
  </NCard>
</template>

<style scoped></style>
