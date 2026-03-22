<script lang="ts" setup>
const colorMode = useColorMode()

interface AreaChartItem {
  date: string
  desktop: number
}

const props = defineProps<{
  data: AreaChartItem[];
}>();

const categories = computed(() => ({
  desktop: {
    name: 'Desktop',
    color: colorMode.value === 'dark' ? '#2b7fff' : '#155dfc',
  }
}))

const xFormatter = (tick: number, _i: number, _ticks: number[]): string => {
  return props.data[tick]?.date ?? ''
}
</script>

<template>
  <AreaChart
    :key="colorMode.value"
    :data="data"
    :height="80"
    :categories="categories"
    :hide-x-axis="true"
    :hide-y-axis="true"
    :y-grid-line="false"
    :x-formatter="xFormatter"
    :curve-type="CurveType.MonotoneX"
    :hide-legend="true"
  />
</template>
