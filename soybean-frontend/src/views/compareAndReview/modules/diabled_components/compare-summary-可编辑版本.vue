<script setup lang="ts">
import { computed, defineComponent, h, nextTick, reactive, ref } from 'vue';
import { NInput } from 'naive-ui';
import { $t } from '@/locales';
import { useTaskStore } from '@/store/modules/task';
import { useAppStore } from '@/store/modules/app';

defineOptions({
  name: 'CompareSummary'
});
const appStore = useAppStore();
const gap = computed(() => (appStore.isMobile ? 0 : 16));
const taskStore = useTaskStore();

const displaying = ref(1);
const prev = () => {
  if (displaying.value > 1) {
    displaying.value -= 1;
  }
};
const next = () => {
  if (displaying.value < 4) {
    displaying.value += 1;
  }
};
const testText = reactive({
  体检摘要: [
    [
      '查体： 双乳对称；双乳皮肤无红肿、破溃、凹陷、橘皮样变；双侧乳头等高、无凹陷、无歪斜，无乳头湿疹样改变，未见陈旧手术疤痕；左乳外上可扪及二枚肿块，右乳外上可扪及一枚肿大，大小均约1cm，质地韧，活动度好，边界清楚，肿块与皮肤无粘连，有明显触痛。',
      '无溢液。',
      '双侧腋窝及双侧锁骨上不可扪及异常肿大淋巴结。'
    ],
    [''],
    ['']
  ]
});
const patient = reactive({
  患者基本信息: {
    住院号: 'zyh47059',
    床号: '+983床',
    入院时间: '2019-03-20',
    出院时间: '无法判断',
    科别: '乳腺外科一',
    科室: '乳腺外科一',
    姓名: '孟兵',
    年龄: '43',
    性别: '女',
    '低压(BP低)': '70',
    '高压(BP高)': '120',
    '脉搏(P)': '72',
    '呼吸(R)': '16',
    '体温(T)': '36.8',
    入院诊断: '乳房肿块(双乳)',
    入院时简要病史:
      '患者12年前自觉双乳肿物，大小均约1 cm。活动度好，有压痛，无乳房局部皮肤破溃红肿，皮肤无变薄，皮下未见扩张静脉，乳头皮肤无湿疹样改变。无乳头溢液。患者2018年乳腺疼痛加剧，遂至瑞金医院门诊就诊，2019-03-20查乳腺B超提示：左侧乳腺可见多个低回声，之一位于约3点钟乳头旁，大小约10.5×6.3mm，拟US-BI-RADS 3-4A类；之一位于约4点钟方向腺体边缘，大小约12.1×8.0mm，拟US-BI-RADS 4A类；右侧乳腺可见多个低回声，之一位于约11-12点钟方向，大小约13.1×5.2mm，拟US-BI-RADS 3-4A类。本次为行进一步诊治，门诊拟“双乳肿物”收治入院。 自发病以来，患者神清，精神可，睡眠胃纳可，二便正常，体重无明显增减。  ',
    体检摘要:
      '查体： 双乳对称；双乳皮肤无红肿、破溃、凹陷、橘皮样变；双侧乳头等高、无凹陷、无歪斜，无乳头湿疹样改变，未见陈旧手术疤痕；左乳外上可扪及二枚肿块，右乳外上可扪及一枚肿大，大小均约1cm，质地韧，活动度好，边界清楚，肿块与皮肤无粘连，有明显触痛。无溢液。双侧腋窝及双侧锁骨上不可扪及异常肿大淋巴结。'
  },
  住院期间医疗情况:
    '抗梅毒螺旋体抗体 0.06 梅毒螺旋体RPR 阴性(-) 丙肝病毒抗体(HCV-Ab) 阴性(-) 艾滋病毒抗体(HIV) 阴性(-) 乙肝病毒表面抗原 0.010(-)IU/mL 乙肝病毒表面抗体 0.45(-)mIU/mL 乙肝病毒e抗原 0.340(-) 乙肝病毒e抗体 1.87(-) 乙肝病毒核心抗体 0.12(-) 乙肝病毒核心抗体IgM 0.08(-) 白细胞计数 3.10↓×10^9/L 中性粒细胞% 50.3％ 淋巴细胞% 38.8％ 单核细胞% 9.8％ 嗜酸性粒细胞% 0.6％ 嗜碱性粒细胞% 0.5％ 中性粒细胞计数 1.50↓×10^9/L 淋巴细胞计数 1.20×10^9/L 单核细胞计数 0.30×10^9/L 嗜酸性粒细胞计数 0.00↓×10^9/L 嗜碱性粒细胞计数 0.00×10^9/L 红细胞计数 4.39×10^12/L 血红蛋白 107↓g/L 红细胞比容 0.332↓ 平均红细胞体积 75.7↓fl 平均血红蛋白量 24.4↓pg 平均血红蛋白浓度 322g/L 红细胞分布宽度 16.3↑％ 血小板计数 173×10^9/L 血小板平均体积 10.5fl 葡萄糖 6.03mmol/L 丙氨酸氨基转移酶 7↓IU/L 天门冬氨酸氨基转移酶 13IU/L 碱性磷酸酶 49IU/L γ-谷氨酰基转移酶 9IU/L 总胆红素 12.2μmol/L 直接胆红素 1.6μmol/L 总蛋白 76g/L 白蛋白 48g/L 白球比例 1.71 尿素 4.0mmol/L 肌酐 45↓μmol/L 尿酸 191μmol/L 钠 139mmol/L 钾 3.52mmol/L 氯 105mmol/L 二氧化碳 22.6mmol/L 钙 2.33mmol/L 磷 1.04mmol/L 估算肾小球滤过率 118.2ml/min/1.73m2 APTT 30.1秒 PT 10.7秒 INR 0.90 抗梅毒螺旋体抗体 0.06 梅毒螺旋体RPR 阴性(-) 丙肝病毒抗体(HCV-Ab) 阴性(-) 艾滋病毒抗体(HIV) 阴性(-) 乙肝病毒表面抗原 0.010(-)IU/mL 乙肝病毒表面抗体 0.45(-)mIU/mL 乙肝病毒e抗原 0.340(-) 乙肝病毒e抗体 1.87(-) 乙肝病毒核心抗体 0.12(-) 乙肝病毒核心抗体IgM 0.08(-) 白细胞计数 3.10↓×10^9/L 中性粒细胞% 50.3％ 淋巴细胞% 38.8％ 单核细胞% 9.8％ 嗜酸性粒细胞% 0.6％ 嗜碱性粒细胞% 0.5％ 中性粒细胞计数 1.50↓×10^9/L 淋巴细胞计数 1.20×10^9/L 单核细胞计数 0.30×10^9/L 嗜酸性粒细胞计数 0.00↓×10^9/L 嗜碱性粒细胞计数 0.00×10^9/L 红细胞计数 4.39×10^12/L 血红蛋白 107↓g/L 红细胞比容 0.332↓ 平均红细胞体积 75.7↓fl 平均血红蛋白量 24.4↓pg 平均血红蛋白浓度 322g/L 红细胞分布宽度 16.3↑％ 血小板计数 173×10^9/L 血小板平均体积 10.5fl 葡萄糖 6.03mmol/L 丙氨酸氨基转移酶 7↓IU/L 天门冬氨酸氨基转移酶 13IU/L 碱性磷酸酶 49IU/L γ-谷氨酰基转移酶 9IU/L 总胆红素 12.2μmol/L 直接胆红素 1.6μmol/L 总蛋白 76g/L 白蛋白 48g/L 白球比例 1.71 尿素 4.0mmol/L 肌酐 45↓μmol/L 尿酸 191μmol/L 钠 139mmol/L 钾 3.52mmol/L 氯 105mmol/L 二氧化碳 22.6mmol/L 钙 2.33mmol/L 磷 1.04mmol/L 估算肾小球滤过率 118.2ml/min/1.73m2 APTT 30.1秒 PT 10.7秒 INR 0.90 抗梅毒螺旋体抗体 0.06 梅毒螺旋体RPR 阴性(-) 丙肝病毒抗体(HCV-Ab) 阴性(-) 艾滋病毒抗体(HIV) 阴性(-) 乙肝病毒表面抗原 0.010(-)IU/mL 乙肝病毒表面抗体 0.45(-)mIU/mL 乙肝病毒e抗原 0.340(-) 乙肝病毒e抗体 1.87(-) 乙肝病毒核心抗体 0.12(-) 乙肝病毒核心抗体IgM 0.08(-) 胸片：两肺纹理略多；主动脉迂曲；请结合临床、病史及其他检查，随访。 心电图：正常。 ',
  出院诊断: '乳房良性肿瘤(双乳纤维腺瘤(M90100/0))',
  病程与治疗情况:
    '患者入院后完善相关检查，排除手术禁忌后，于2019-03-20全麻下行双乳象限切除术，术中冰冻病理提示： (左乳3点肿物）纤维腺瘤； (左乳4点肿物)纤维腺瘤； (右乳11-12点肿物）纤维腺瘤。术后石蜡病理未回。现患者一般情况良好，伤口愈合I/甲，经上级医师查房同意后，予今日出院。',
  出院后用药建议:
    '1.10个工作日后来院询问石蜡病理报告，并带至主诊医师门诊就诊，拟定进一步诊疗或随访方案。 2.术后胸带加压包扎切口5天；之后可佩戴文胸；保持伤口清洁干燥，2周内避免洗澡；术后10天内每3天来院换药一次，换药门诊时间：每周一～周五9:00-11:00 在门诊大楼3楼乳腺中心。 3.保持伤口清洁干燥，如有发热，切口局部红肿、疼痛、化脓等不适，及时来院就诊。 4.心电图提示：正常范围心电图，请于心内科随访。 5.患者住院期间尿常规提示：白细胞 25.0↑/UL(参考值0~21.000/UL)，请于泌尿科随访。 6.患者术后康复评估见专页。',
  出院时情况: '神清，精神可，一般情况良好。伤口愈合I/甲。'
});
const doctor = reactive({
  患者基本信息: {
    住院号: 'zyh47059',
    床号: '+983床',
    入院时间: '2019-03-20',
    出院时间: '无法判断',
    科别: '乳腺外科一',
    科室: '乳腺外科一',
    姓名: '孟兵',
    年龄: '43',
    性别: '女',
    '低压(BP低)': '70',
    '高压(BP高)': '120',
    '脉搏(P)': '72',
    '呼吸(R)': '16',
    '体温(T)': '36.8',
    入院诊断: '乳房肿块(双乳)',
    入院时简要病史:
      '患者12年前自觉双乳肿物，大小均约1 cm。活动度好，有压痛，无乳房局部皮肤破溃红肿，皮肤无变薄，皮下未见扩张静脉，乳头皮肤无湿疹样改变。无乳头溢液。患者2018年乳腺疼痛加剧，遂至瑞金医院门诊就诊，2019-03-20查乳腺B超提示：左侧乳腺可见多个低回声，之一位于约3点钟乳头旁，大小约10.5×6.3mm，拟US-BI-RADS 3-4A类；之一位于约4点钟方向腺体边缘，大小约12.1×8.0mm，拟US-BI-RADS 4A类；右侧乳腺可见多个低回声，之一位于约11-12点钟方向，大小约13.1×5.2mm，拟US-BI-RADS 3-4A类。本次为行进一步诊治，门诊拟“双乳肿物”收治入院。  自发病以来，患者神清，精神可，睡眠胃纳可，二便正常，体重无明显增减。   ',
    体检摘要:
      '查体： 双乳对称；双乳皮肤无红肿、破溃、凹陷、橘皮样变；双侧乳头等高、无凹陷、无歪斜，无乳头湿疹样改变，未见陈旧手术疤痕；左乳外上可扪及二枚肿块，右乳外上可扪及一枚肿大，大小均约1cm，质地韧，活动度好，边界清楚，肿块与皮肤无粘连，有明显触痛。无溢液。双侧腋窝及双侧锁骨上不可扪及异常肿大淋巴结。'
  },
  住院期间医疗情况:
    '血常规： 白细胞计数 3.10↓×10^9/L 中性粒细胞计数 1.50↓×10^9/L 红细胞计数 4.39×10^12/L 血红蛋白 107↓g/L 血小板计数 173×10^9/L 梅毒： 抗梅毒螺旋体抗体 0.06 梅毒螺旋体RPR 阴性(-) 止凝血： APTT 30.1秒 PT 10.7秒 INR 0.90 生化： 葡萄糖 6.03mmol/L 丙氨酸氨基转移酶 7↓IU/L 天门冬氨酸氨基转移酶 13IU/L 碱性磷酸酶 49IU/L γ-谷氨酰基转移酶 9IU/L 总胆红素 12.2μmol/L 直接胆红素 1.6μmol/L 总蛋白 76g/L 白蛋白 48g/L 白球比例 1.71 尿素 4.0mmol/L 肌酐 45↓μmol/L 尿酸 191μmol/L 钠 139mmol/L 钾 3.52mmol/L 氯 105mmol/L 二氧化碳 22.6mmol/L 钙 2.33mmol/L 磷 1.04mmol/L 估算肾小球滤过率 118.2ml/min/1.73m2 2019-03-21心电图：正常。 2019-03-21胸片：两肺纹理略多；主动脉迂曲；请结合临床、病史及其他检查，随访。 ',
  出院诊断: '乳房良性肿瘤(双乳纤维腺瘤(M90100/0))',
  病程与治疗情况:
    '患者入院后完善相关检查，排除手术禁忌后，于2019-03-20全麻下行双乳象限切除术，术中冰冻提示：(左乳3点肿物）纤维腺瘤； (左乳4点肿物)纤维腺瘤； (右乳11-12点肿物)纤维腺瘤。术后石蜡病理未回。现患者一般情况良好，伤口愈合I/甲，经上级医师查房同意后，予今日出院。',
  出院后用药建议:
    '1.10个工作日后来院询问石蜡病理报告，并带至主诊医师门诊就诊，拟定进一步诊疗或随访方案。 2. 术后胸带加压包扎切口7天；之后可佩戴文胸；保持伤口清洁干燥，2周内避免洗澡；术后10天内每3天来院换药一次，换药门诊时间：每周一～周五9:00-11:00 在门诊大楼3楼乳腺中心。 3.保持伤口清洁干燥，如有发热，切口局部红肿、疼痛、化脓等不适，及时来院就诊。 4术后康复指导详见专页。',
  出院时情况: '神清，精神可，一般情况良好。伤口愈合I/甲。'
});
const ShowOrEdit = defineComponent({
  props: {
    value: String,
    onUpdateValue: Function
  },
  setup(props, { emit }) {
    const isEdit = ref(false);
    const inputRef = ref(null);
    const inputValue = ref(props.value);
    function handleOnClick() {
      isEdit.value = true;
      nextTick().then(() => inputRef.value.focus());
    }
    function handleChange() {
      emit('update:value', inputValue.value);
      isEdit.value = false;
    }
    return () =>
      h(
        'span',
        { style: 'white-space: pre-wrap;', onClick: handleOnClick },
        isEdit.value
          ? h(NInput, {
              ref: inputRef,
              value: inputValue.value,
              onUpdateValue: v => (inputValue.value = v),
              onChange: handleChange,
              onBlur: handleChange,
              style: 'height: auto;width:auto;',
              type: 'textarea',
              size: 'small',
              autosize: { minRows: 1, maxRows: 10 }
            })
          : props.value
      );
  }
});
</script>

<template>
  <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
    <NGi span="24 s:24 m:12" style="display: flex">
      <NCard
        size="small"
        :bordered="false"
        title="LLM Discharge Summary"
        header-class="text-14px"
        header-style="padding: 6px var(--n-padding-left); text-align: center; font-weight: 600; position: sticky; top: 0; background: white; z-index: 10;"
        footer-style="padding: 0 6px 6px 6px;position: sticky; bottom: -1px; background: white; z-index: 10;"
        content-style="padding: 0 6px 0 6px;position: sticky;"
        style="flex: 1; display: flex; flex-direction: column; max-height: 50vh; min-height: 45vh; overflow: auto"
      >
        <div style="flex: 1; overflow: auto">
          <table
            v-if="displaying == 1"
            style="table-layout: fixed; width: 100%; border: 1px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 20%" />
              <col style="width: 15%" />
              <col style="width: 15%" />
              <col style="width: 15%" />
              <col style="width: 15%" />
              <col style="width: 20%" />
            </colgroup>
            <tr>
              <td>Name:</td>
              <td><ShowOrEdit v-model:value="patient.患者基本信息.姓名" /></td>
              <td>Age:</td>
              <td><ShowOrEdit v-model:value="patient.患者基本信息.年龄" /></td>
              <td>Gender:</td>
              <td><ShowOrEdit v-model:value="patient.患者基本信息.性别" /></td>
            </tr>
            <tr>
              <td>Hospital No:</td>
              <td><ShowOrEdit v-model:value="patient.患者基本信息.住院号" /></td>
              <td>Bed No:</td>
              <td><ShowOrEdit v-model:value="patient.患者基本信息.床号" /></td>
              <td></td>
              <td></td>
            </tr>
            <tr>
              <td>Department:</td>
              <td colspan="5"><ShowOrEdit v-model:value="patient.患者基本信息.科室" /></td>
            </tr>
            <tr>
              <td>In Time:</td>
              <td colspan="2"><ShowOrEdit v-model:value="patient.患者基本信息.入院时间" /></td>
              <td>Out Time:</td>
              <td colspan="2"><ShowOrEdit v-model:value="patient.患者基本信息.出院时间" /></td>
            </tr>
            <tr>
              <td>Cause:</td>
              <td colspan="5"><ShowOrEdit v-model:value="patient.患者基本信息.入院诊断" /></td>
            </tr>
            <tr>
              <td style="vertical-align: top">Diagnosis:</td>
              <td colspan="5"><ShowOrEdit v-model:value="patient.出院诊断" /></td>
            </tr>
            <tr>
              <td colspan="6">体检摘要:</td>
            </tr>
            <tr></tr>
            <tr>
              <td colspan="6" style="vertical-align: top; font-weight: normal">
                <span class="hang-indent"><ShowOrEdit v-model:value="patient.患者基本信息.体检摘要" /></span>
              </td>
            </tr>
          </table>
          <table
            v-if="displaying == 2"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
            </colgroup>

            <tr>
              <td colspan="8" style="vertical-align: top">Brief History:</td>
            </tr>
            <tr>
              <td style="vertical-align: middle">T:</td>
              <td>
                <ShowOrEdit v-model:value="patient['患者基本信息']['体温(T)']" />
                ℃
              </td>
              <td>P:</td>
              <td>
                <ShowOrEdit v-model:value="patient['患者基本信息']['脉搏(P)']" />
                bpm
              </td>
              <td>R:</td>
              <td>
                <ShowOrEdit v-model:value="patient['患者基本信息']['呼吸(R)']" />
                bpm
              </td>
              <td>BP:</td>
              <td>
                <ShowOrEdit v-model:value="patient['患者基本信息']['高压(BP高)']" />
                /
                <ShowOrEdit v-model:value="patient['患者基本信息']['低压(BP低)']" />
                mmHg
              </td>
            </tr>
            <tr></tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <span class="hang-indent">
                  <ShowOrEdit v-model:value="patient['患者基本信息']['入院时简要病史']" />
                </span>
              </td>
            </tr>
          </table>
          <table
            v-if="displaying == 3"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
            </colgroup>

            <tr>
              <td colspan="8" style="vertical-align: top">Main Test And Examination Results During Hospitalization:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <ShowOrEdit v-model:value="patient['住院期间医疗情况']" />
              </td>
            </tr>
          </table>
          <table
            v-if="displaying == 4"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
            </colgroup>

            <tr>
              <td colspan="8" style="vertical-align: top">Course And Treatment:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <ShowOrEdit v-model:value="patient['病程与治疗情况']" />
              </td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top">Condition at Discharge:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <ShowOrEdit v-model:value="patient['出院时情况']" />
              </td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top">Medication Recommendations After Discharge:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <ShowOrEdit v-model:value="patient['出院后用药建议']" />
              </td>
            </tr>
          </table>
        </div>
        <template #footer>
          <NSpace style="width: 100%; justify-content: right; padding-top: 6px; padding-bottom: 0">
            <NButton size="small" @click="prev"><</NButton>
            <NButton size="small" @click="next">></NButton>
          </NSpace>
        </template>
      </NCard>
    </NGi>
    <NGi span="24 s:24 m:12" style="display: flex">
      <NCard
        size="small"
        :bordered="false"
        title="Doctor Discharge Summary"
        header-class="text-14px"
        header-style="padding: 6px var(--n-padding-left); text-align: center; font-weight: 600; position: sticky; top: 0; background: white; z-index: 10;"
        footer-style="padding: 0 6px 6px 6px;position: sticky; bottom: -1px; background: white; z-index: 10;"
        content-style="padding: 0 6px 0 6px;position: sticky;"
        style="max-height: 50vh; min-height: 45vh; overflow: auto; flex: 1; display: flex; flex-direction: column"
      >
        <div style="flex: 1; overflow: auto">
          <table
            v-if="displaying == 1"
            style="table-layout: fixed; width: 100%; border: 1px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 20%" />
              <col style="width: 15%" />
              <col style="width: 15%" />
              <col style="width: 15%" />
              <col style="width: 15%" />
              <col style="width: 20%" />
            </colgroup>
            <tr>
              <td>Name:</td>
              <td>{{ doctor.患者基本信息.姓名 }}</td>
              <td>Age:</td>
              <td>{{ doctor.患者基本信息.年龄 }}</td>
              <td>Gender:</td>
              <td>{{ doctor.患者基本信息.性别 }}</td>
            </tr>
            <tr>
              <td>Hospital No:</td>
              <td>{{ doctor.患者基本信息.住院号 }}</td>
              <td>Bed No:</td>
              <td>{{ doctor.患者基本信息.床号 }}</td>
              <td></td>
              <td></td>
            </tr>
            <tr>
              <td>Department:</td>
              <td colspan="5">{{ doctor.患者基本信息.科室 }}</td>
            </tr>
            <tr>
              <td>In Time:</td>
              <td colspan="2">{{ doctor.患者基本信息.入院时间 }}</td>
              <td>Out Time:</td>
              <td colspan="2">{{ doctor.患者基本信息.出院时间 }}</td>
            </tr>
            <tr>
              <td>Cause:</td>
              <td colspan="5">{{ doctor.患者基本信息.入院诊断 }}</td>
            </tr>
            <tr>
              <td style="vertical-align: top">Diagnosis:</td>
              <td colspan="5">{{ doctor.出院诊断 }}</td>
            </tr>
            <tr>
              <td colspan="6">Physical Examination:</td>
            </tr>
            <tr></tr>
            <tr>
              <td colspan="6" style="vertical-align: top; font-weight: normal">{{ doctor.患者基本信息.体检摘要 }}</td>
            </tr>
          </table>
          <table
            v-if="displaying == 2"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
            </colgroup>

            <tr>
              <td colspan="8" style="vertical-align: top">Brief History:</td>
            </tr>
            <tr>
              <td style="vertical-align: middle">T:</td>
              <td>
                {{ doctor['患者基本信息']['体温(T)'] }}
                ℃
              </td>
              <td>P:</td>
              <td>
                {{ doctor['患者基本信息']['脉搏(P)'] }}
                bpm
              </td>
              <td>R:</td>
              <td>
                {{ doctor['患者基本信息']['呼吸(R)'] }}
                bpm
              </td>
              <td>BP:</td>
              <td>
                {{ doctor['患者基本信息']['高压(BP高)'] }}
                /
                {{ doctor['患者基本信息']['低压(BP低)'] }}
                mmHg
              </td>
            </tr>
            <tr></tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                {{ doctor['患者基本信息']['入院时简要病史'] }}
              </td>
            </tr>
          </table>
        </div>

        <template #footer>
          <NSpace style="width: 100%; justify-content: right; padding-top: 6px; padding-bottom: 0">
            <NButton size="small" @click="prev"><</NButton>
            <NButton size="small" @click="next">></NButton>
          </NSpace>
        </template>
      </NCard>
    </NGi>
  </NGrid>
</template>

<style scoped>
.n-card-header__main {
  font-weight: bold;
}

:deep(.n-form-item .n-form-item-feedback-wrapper) {
  min-height: 0px;
}
:deep(.n-descriptions-table-header) {
  border: 0 solid;
}

h2 {
  text-align: center;
  margin-bottom: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 auto;
}
table tr {
  line-height: 1.2; /* 调整行高 */
}

td {
  padding: 4px;
  text-align: left;
}

td[colspan='5'] {
  text-align: justify;
}

table tr:nth-child(even) {
  background-color: rgb(238, 239, 241, 0.5);
}
table td:nth-child(odd) {
  font-family: 'Times New Roman', 'SimSun', '黑体', sans-serif;
  font-weight: 700;
}

/* 设置表格的第 2、4、6 列为宋体 */
table td:nth-child(even) {
  font-family: 'SimSun', serif; /* 宋体 */
}

.hang-indent {
  display: block;
  text-indent: 0em; /* 让首行 */
  padding-left: 0em; /* 让后续行缩进 1 个字符 */
}

.highlight {
  background-color: rgb(250, 250, 184);
}
</style>
