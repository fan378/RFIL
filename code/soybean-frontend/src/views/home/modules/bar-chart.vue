<script setup lang="ts">
import { watch } from 'vue';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'BarChart'
});

const appStore = useAppStore();

const color = ['#B0C3F4', '#8FADF0', '#6495ED', '#5B88D9', '#517AC4', '#3E5F9A'];

const indicators = ['ACC', 'ROUGE', 'FACTKB', 'UNIEVAL', 'BLEU', 'METOR'];

const { domRef, updateOptions } = useEcharts(() => ({
  // title: {
  //   text: '科室数据分布',
  //   subtext: '随机值'
  // },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
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
  toolbox: {
    show: true,
    feature: {
      dataView: { show: true, readOnly: false },
      magicType: { show: true, type: ['line', 'bar'] },
      // restore: { show: true },
      saveAsImage: { show: true }
    }
  },
  calculable: true,
  xAxis: [
    {
      type: 'category',
      data: [
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
      ],
      axisLabel: {
        show: true, // Ensure labels are shown
        interval: 0, // This ensures that all labels are displayed
        fontSize: 8 // Set the font size for x-axis labels
      }
    }
  ],
  yAxis: [
    {
      type: 'value',
      min: 0.6,
      max: 1,
      axisLabel: {
        show: true, // Ensure labels are shown
        interval: 0, // This ensures that all labels are displayed
        fontSize: 8 // Set the font size for x-axis labels
      }
    }
  ],
  series: indicators.map((value, index) => ({
    name: value,
    type: 'bar',
    data: Array.from({ length: 15 }, () => (Math.random() * 0.38 + 0.6).toFixed(2)),
    color: color[index]
  })),
  grid: {
    containLabel: true,
    left: '0%',
    top: '15%',
    right: '5%',
    bottom: '0%'
  },
  barCategoryGap: '50%'
}));

async function mockData() {
  await new Promise(resolve => {
    setTimeout(resolve, 1000);
  });

  updateOptions(opts => {
    return opts;
  });
}

function updateLocale() {
  updateOptions((opts, factory) => {
    const originOpts = factory();

    opts.legend.data = originOpts.legend.data;
    opts.series[0].name = originOpts.series[0].name;
    opts.series[1].name = originOpts.series[1].name;

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
      <strong>各科室指标得分对比</strong>
    </template>
    <div ref="domRef" class="h-210px overflow-hidden"></div>
  </NCard>
</template>

<style scoped></style>
