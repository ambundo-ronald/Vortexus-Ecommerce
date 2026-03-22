<template>
  <div class="p-8">
    <h1 class="text-2xl font-semibold text-highlighted">Campaigns</h1>
    <p class="text-toned mt-2">
      This is a placeholder page for managing marketing campaigns.
    </p>
    <div class="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <UCard v-for="i in 3" :key="i">
        <template #header>
          <h3 class="text-lg font-semibold">Campaign #{{ i }}</h3>
        </template>
        <p class="text-sm text-toned">
          This is a placeholder for campaign details. You can add charts, stats, and other relevant information here.
        </p>
        <template #footer>
          <UButton variant="outline">View Details</UButton>
        </template>
      </UCard>
    </div>
  </div>
</template>