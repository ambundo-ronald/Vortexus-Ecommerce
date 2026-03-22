<template>
  <UCard>
    <div class="flex items-center justify-between">
      <div class="mb-2"><slot name="label" /></div>
      <slot name="icon"/>
    </div>
    <div class="flex items-baseline mb-2">
      <span class="text-3xl font-medium dark:font-semibold"><slot name="value" /></span>
      <span class="ml-2 text-sm font-medium flex items-center">
        <slot name="trend" />
      </span>
    </div>
    <div class="w-full rounded-md">
      <slot name="chart" />
    </div>
  </UCard>
</template>
