<script setup lang="ts">
import { ref, computed } from "vue";
import { getUserTableColumns } from "~/config/userTableColumns";
import type { SortBy, SortDir } from "~/types/Table";

const UBadge = resolveComponent("UBadge");
const UButton = resolveComponent("UButton");
const UInput = resolveComponent("UInput");
const UAvatar = resolveComponent("UAvatar");
const UCheckbox = resolveComponent("UCheckbox");

const queryParams = reactive({
  page: 1,
  pageSize: 10,
  search: "",
  sortBy: undefined as SortBy | undefined,
  sortDir: "asc" as SortDir,
});

const columns = getUserTableColumns({
  sortBy: toRef(queryParams, 'sortBy'),
  sortDir: toRef(queryParams, 'sortDir'),
  components: [UButton, UBadge, UCheckbox, UAvatar] as Component[],
});

const { data } = await useFetch("/api/users", {
  key: `users`,
  params: queryParams,
});

const userData = computed(() => data.value?.data ?? []);
const totalItems = computed(() => data.value?.totalItems ?? 0);
</script>

<template>
  <div>
    <div class="flex justify-between items-center p-8 mb-4 pb-4">
      <h1 class="text-xl font-semibold">Users</h1>

      <div class="flex items-center justify-end gap-2 w-full">
        <UInput
          v-model="queryParams.search"
          class="max-w-sm"
          size="lg"
          icon="i-lucide-search"
          placeholder="Search users..."
          :ui="{ leadingIcon: 'size-4' }"
        />

        <UButton variant="outline">
          <UIcon name="i-lucide-settings" />
          Settings
        </UButton>
        <UButton color="primary" variant="solid">
          <UIcon name="i-lucide-plus" />
          Add User
        </UButton>
      </div>
    </div>

    <div class="px-8">
      <UTable
        :data="userData"
        :columns="columns"
      /> 
      <div class="flex justify-end pt-4">
        <UPagination
          :page="queryParams.page"
          :page-count="queryParams.pageSize"
          :total="totalItems"
          @update:page="(page: number) => queryParams.page = page"
        />
      </div>
    </div>
  </div>
</template>
