<script setup lang="ts">
import { useSortable } from "@vueuse/integrations/useSortable";
import { analyticsDataset } from "~/data/analyticsData";

const selectedRange = ref("Last 30 days");
const selectedPage = ref("All products");
const selectedTrafficPage = ref("All pages");

const analyticsData = analyticsDataset[selectedRange.value];

const kpiCards = ref([
  {
    key: "totalSessions",
    label: "Total sessions",
    value: () => analyticsData?.kpi.totalSessions,
    chart: "DashboardTotalSessionsChart",
    chartData: () => analyticsData?.charts.totalSessions,
  },
  {
    key: "sessionDuration",
    label: "Session duration",
    value: () => analyticsData?.kpi.sessionDuration,
    chart: "DashboardSessionDurationChart",
    chartData: () => analyticsData?.charts.sessionDuration,
  },
  {
    key: "pagesPerSession",
    label: "Pages per session",
    value: () => analyticsData?.kpi.pagesPerSession,
    chart: "DashboardPagesPerSessionChart",
    chartData: () => analyticsData?.charts.pagesPerSession,
  },
  {
    key: "bounceRate",
    label: "Bounce rate",
    value: () => analyticsData?.kpi.bounceRate + "%",
    chart: "DashboardBounceRateChart",
    chartData: () => analyticsData?.charts.bounceRate,
  },
]);

const gridRef = ref();
useSortable(gridRef, kpiCards, { animation: 200, handle: ".kpi-drag-handle" });
</script>

<template>
  <div v-if="analyticsData">
    <div class="flex justify-between items-center p-8 mb-4 pb-4">
      <h1 class="text-xl font-semibold">Analytics</h1>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <UButton variant="outline">
            <UIcon name="i-lucide-list-filter-plus" />
            Filter
          </UButton>
          <USelect
            v-model="selectedRange"
            :items="['Last 7 days', 'Last 30 days', 'Last 90 days']"
            class="w-36"
          />
        </div>
      </div>
    </div>

    <div class="px-8">
      <BlocksKpiGrid ref="gridRef">
        <template v-for="(card, idx) in kpiCards" :key="idx">
          <div class="relative group">
            <CardsKpiCard>
              <template #label>
                {{ card.label }}
              </template>
              <template #icon>
                <UIcon
                  name="i-lucide-grip"
                  size="24"
                  class="kpi-drag-handle cursor-move mr-1 transition text-dimmed cursor-pointer"
              /></template>
              <template #value>{{ card.value() }}</template>
              <template #trend>
                <UBadge class="text-success-600 font-semibold">
                  <UIcon name="i-lucide-trending-up" size="16" />
                  {{ analyticsData?.kpi.trend }}%
                </UBadge>
              </template>
              <template #chart>
                <component :is="card.chart" :data="card.chartData()" />
              </template>
            </CardsKpiCard>
          </div>
        </template>
      </BlocksKpiGrid>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <UCard>
          <template #header>
            <div class="flex justify-between items-center">
              <h2 class="text-lg font-medium text-text">
                Top ecommerce actions
              </h2>
              <USelect
                v-model="selectedPage"
                :items="['All products', 'Featured', 'On Sale']"
                class="w-32"
              />
            </div>
          </template>
          <ul>
            <li
              v-for="(item, i) in analyticsData?.topLinks ?? []"
              :key="i"
              class="mb-4"
            >
              <div class="flex justify-between items-center text-sm mb-1">
                <span class="text-text">{{ item.label }}</span>
                <span class="text-text-dimmed"
                  >{{ item.sessions }} sessions
                  <UIcon name="i-lucide-chevron-right" class="inline"
                /></span>
              </div>
              <div class="w-full rounded-full h-2.5 bg-bg-elevated">
                <div
                  class="h-2.5 rounded-full bg-blue-600 dark:bg-blue-500"
                  :style="{ width: item.width }"
                />
              </div>
            </li>
          </ul>
          <div class="flex justify-center">
            <UButton variant="outline" class="py-2 mt-2">Load more</UButton>
          </div>
        </UCard>
        <UCard>
          <template #header>
            <div class="flex justify-between items-center">
              <h2 class="text-lg font-medium text-text">
                Top pages by traffic
              </h2>
              <USelect
                v-model="selectedTrafficPage"
                :items="['All pages', 'Homepage', 'Pricing']"
                class="w-32"
              />
            </div>
          </template>
          <ul>
            <li
              v-for="(item, i) in analyticsData?.topTraffic ?? []"
              :key="i"
              class="mb-4"
            >
              <div class="flex justify-between items-center text-sm mb-1">
                <span class="text-text">{{ item.label }}</span>
                <span class="text-text-dimmed"
                  >{{ item.sessions }} sessions
                  <UIcon name="i-lucide-chevron-right" class="inline"
                /></span>
              </div>
              <div class="w-full rounded-full h-2.5 bg-bg-elevated">
                <div
                  class="h-2.5 rounded-full bg-blue-600 dark:bg-blue-500"
                  :style="{ width: item.width }"
                />
              </div>
            </li>
          </ul>
          <div class="flex justify-center">
            <UButton variant="outline" class="py-2 mt-2">Load more</UButton>
          </div>
        </UCard>
      </div>
    </div>
  </div>
</template>
