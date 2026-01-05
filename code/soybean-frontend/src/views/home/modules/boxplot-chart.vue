<script setup lang="ts">
import { watch } from 'vue';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'BoxplotChart'
});

const appStore = useAppStore();

// Define mock data structure for heatmap
const sections = [
  $t('page.home.patientInfo'),
  $t('page.home.dischargeDiagnosis'),
  $t('page.home.medicalTestsAndExaminations'),
  $t('page.home.diseaseCourseAndTreatment'),
  $t('page.home.conditionAtDischarge'),
  $t('page.home.postDischargeMedicationAdvice')
];
const models = ['EMR-LLM', 'BenTaso', 'Alpacare', 'Qwen2', 'Chatglm3', 'HuaTuoGPT'];
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
// const blue1 = getComputedStyle(document.documentElement).getPropertyValue('--blue-1').trim();
// const blue15 = getComputedStyle(document.documentElement).getPropertyValue('--blue-15').trim();

// Common mock data
// Fixed mock data for six datasets
const data0 = [
  [0.8, 0.85, 0.9, 0.95, 0.88],
  [0.6, 0.65, 0.7, 0.75, 0.68],
  [0.7, 0.72, 0.76, 0.8, 0.78],
  [0.8, 0.82, 0.85, 0.9, 0.87],
  [0.75, 0.77, 0.8, 0.82, 0.79],
  [0.65, 0.68, 0.72, 0.75, 0.7]
];

const data1 = [
  [0.82, 0.87, 0.92, 0.96, 0.9],
  [0.62, 0.67, 0.72, 0.76, 0.7],
  [0.72, 0.74, 0.78, 0.82, 0.79],
  [0.82, 0.84, 0.87, 0.92, 0.89],
  [0.77, 0.79, 0.82, 0.85, 0.81],
  [0.67, 0.7, 0.74, 0.78, 0.73]
];

const data2 = [
  [0.84, 0.89, 0.94, 0.98, 0.93],
  [0.64, 0.69, 0.74, 0.78, 0.73],
  [0.74, 0.76, 0.8, 0.84, 0.81],
  [0.84, 0.86, 0.89, 0.94, 0.91],
  [0.79, 0.81, 0.84, 0.87, 0.83],
  [0.69, 0.72, 0.76, 0.8, 0.75]
];

const data3 = [
  [0.81, 0.86, 0.91, 0.95, 0.89],
  [0.61, 0.66, 0.71, 0.75, 0.69],
  [0.71, 0.73, 0.77, 0.81, 0.79],
  [0.81, 0.83, 0.86, 0.91, 0.88],
  [0.76, 0.78, 0.81, 0.83, 0.8],
  [0.66, 0.69, 0.73, 0.77, 0.71]
];

const data4 = [
  [0.85, 0.9, 0.95, 0.99, 0.92],
  [0.65, 0.7, 0.75, 0.79, 0.74],
  [0.75, 0.77, 0.81, 0.85, 0.83],
  [0.85, 0.87, 0.9, 0.95, 0.93],
  [0.8, 0.82, 0.85, 0.88, 0.84],
  [0.7, 0.73, 0.77, 0.81, 0.76]
];

const data5 = [
  [0.86, 0.91, 0.96, 1.0, 0.94],
  [0.66, 0.71, 0.76, 0.8, 0.75],
  [0.76, 0.78, 0.82, 0.86, 0.84],
  [0.86, 0.88, 0.91, 0.96, 0.94],
  [0.81, 0.83, 0.86, 0.89, 0.85],
  [0.71, 0.74, 0.78, 0.82, 0.77]
];

const { domRef, updateOptions } = useEcharts(() => ({
  color: [
    '#d4def8',
    '#C9D5F7',
    '#BCCCF5',
    '#B0C3F4',
    '#A1B9F2',
    '#8FADF0',
    '#7BA1EF',
    '#6495ED',
    '#608FE3',
    '#5B88D9',
    '#5681CE',
    '#517AC4',
    '#4C72B7',
    '#4569A9',
    '#3E5F9A'
  ],
  dataset: [
    { source: data0 },
    { source: data1 },
    { source: data2 },
    { source: data3 },
    { source: data4 },
    { source: data5 },
    { source: data0 },
    { source: data1 },
    { source: data2 },
    { source: data3 },
    { source: data4 },
    { source: data5 },
    { source: data0 },
    { source: data1 },
    { source: data2 },
    ...[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14].map(index => ({
      fromDatasetIndex: index,
      transform: {
        type: 'boxplot',
        config: {
          itemNameFormatter(params) {
            return models[params.value];
          }
        }
      }
    }))
  ],
  legend: {
    right: '0%',
    orient: 'vertical', // 图例垂直排列
    itemWidth: 10, // 图例图标宽度
    itemHeight: 10, // 图例图标高度
    top: 'center',
    textStyle: {
      fontSize: 8, // 设置字体大小为 8
      lineHeight: 8 // 设置行高，确保换行后不重叠
    },
    icon: 'circle', // 图标样式设置
    width: 100 // 限制宽度，触发文字自动换
  },
  tooltip: {
    trigger: 'item',
    axisPointer: {
      type: 'shadow'
    }
  },
  grid: {
    left: '5%',
    top: '5%',
    right: '25%',
    bottom: '10%'
  },
  xAxis: {
    type: 'category',
    boundaryGap: true,
    axisLabel: {
      show: true, // Ensure labels are shown
      interval: 0, // This ensures that all labels are displayed
      fontSize: 8 // Set the font size for x-axis labels
    },
    splitArea: {
      show: true
    }
  },
  yAxis: {
    type: 'value',
    name: 'score',
    min: 0.6,
    max: 1,
    splitArea: {
      show: false
    },
    axisLabel: {
      show: true, // Ensure labels are shown
      interval: 0, // This ensures that all labels are displayed
      fontSize: 8 // Set the font size for x-axis labels
    }
  },
  // dataZoom: [
  //   {
  //     type: 'inside',
  //     start: 0,
  //     end: 20
  //   },
  //   {
  //     show: true,
  //     type: 'slider',
  //     top: '90%',
  //     xAxisIndex: [0],
  //     start: 0,
  //     end: 20
  //   }
  // ],
  series: sections.map((model, index) => ({
    name: model,
    type: 'boxplot',
    datasetIndex: index + 15,
    color: ['#B0C3F4', '#8FADF0', '#6495ED', '#5B88D9', '#517AC4', '#3E5F9A'][index],
    boxWidth: ['10%', '50%']
  }))
}));

async function mockData() {
  await new Promise(resolve => {
    setTimeout(resolve, 1000);
  });

  updateOptions(opts => {
    opts.color = [
      '#d4def8',
      '#C9D5F7',
      '#BCCCF5',
      '#B0C3F4',
      '#A1B9F2',
      '#8FADF0',
      '#7BA1EF',
      '#6495ED',
      '#608FE3',
      '#5B88D9',
      '#5681CE',
      '#517AC4',
      '#4C72B7',
      '#4569A9',
      '#3E5F9A'
    ];

    return opts;
  });
}

function updateLocale() {
  updateOptions((opts, factory) => {
    const originOpts = factory();
    opts.series[0].name = originOpts.series[0].name;

    return opts;
  });
}

async function init() {
  mockData();
}

watch(
  () => appStore.locale,
  () => {
    updateLocale();
  }
);

// init
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
      <strong>各字段质量比较</strong>
    </template>
    <div ref="domRef" class="h-150px"></div>
  </NCard>
</template>

<style scoped></style>
