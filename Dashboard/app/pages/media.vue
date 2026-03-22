<script setup>
import { useMediaManager } from '~/composables/useMediaManager';

const {
  allFiles,
  folders,
  selectedFolder,
  searchQuery,
  selectedFiles,
  filteredFiles,
  selectFolder,
  toggleFileSelection,
  deleteSelectedImages,
} = useMediaManager();

const newFolderName = ref("");
const editingFolderId = ref(null);
const editingFolderName = ref("");
const editInput = ref(null);

const createFolder = () => {
  const name = "";
  const exists = folders.value.some(
    (f) => f.name.toLowerCase() === name.toLowerCase()
  );
  if (exists) return;
  const newId = Math.max(...folders.value.map((f) => f.id)) + 1;
  folders.value.push({ id: newId, name });
  newFolderName.value = "";
  selectedFolder.value = folders.value.find((f) => f.id === newId);
  // Immediately start editing the new folder
  editingFolderId.value = newId;
  editingFolderName.value = name;
  nextTick(() => {
    if (editInput.value) {
      if (Array.isArray(editInput.value)) {
        editInput.value[0].focus();
      } else {
        editInput.value.focus();
      }
    }
  });
};

// --- UPLOAD MODAL LOGIC ---
const isUploadModalOpen = ref(false);
const stagedFiles = ref([]);
const isDragging = ref(false);
const fileInput = ref(null);

const onFileSelect = (event) => {
  addFilesToStage(event.target.files);
};

const onDrop = (event) => {
  isDragging.value = false;
  addFilesToStage(event.dataTransfer.files);
};

const addFilesToStage = (files) => {
  for (const file of files) {
    stagedFiles.value.push(file);
  }
};

const removeStagedFile = (index) => {
  stagedFiles.value.splice(index, 1);
};

const uploadFiles = () => {
  if (stagedFiles.value.length === 0) return;

  console.log(
    `Uploading ${stagedFiles.value.length} files to folder "${selectedFolder.value.name}"...`
  );

  stagedFiles.value.forEach((file) => {
    const newFile = {
      id: Date.now() + Math.random(),
      name: file.name,
      folderId: selectedFolder.value.id,
      url: URL.createObjectURL(file),
    };
    allFiles.value.push(newFile);
  });

  stagedFiles.value = []; // Clear staged files
  isUploadModalOpen.value = false; // Close modal
};

const onDragOver = () => {
  isDragging.value = true;
};
const onDragLeave = () => {
  isDragging.value = false;
};

const startEditFolder = (folder) => {
  editingFolderId.value = folder.id;
  editingFolderName.value = folder.name;
  nextTick(() => {
    if (editInput.value) {
      if (Array.isArray(editInput.value)) {
        editInput.value[0].focus();
      } else {
        editInput.value.focus();
      }
    }
  });
};

const saveEditFolder = (folder) => {
  const name = editingFolderName.value.trim();
  if (!name) {
    cancelEditFolder();
    return;
  }
  const exists = folders.value.some(
    (f) => f.name.toLowerCase() === name.toLowerCase() && f.id !== folder.id
  );
  if (exists) {
    const toast = useToast();
    toast.add({
      title: "Error",
      description: "Folder name exists.",
      color: "error",
    });
    cancelEditFolder();
    return;
  }
  folder.name = name;
  cancelEditFolder();
};

const cancelEditFolder = () => {
  editingFolderId.value = null;
  editingFolderName.value = "";
};

const isGridView = ref(true);
const toggleView = () => {
  isGridView.value = !isGridView.value;
};

const settingsDropdownItems = [
  [
    {
      label: "Delete Folder",
      icon: "i-lucide-trash-2",
      click: () => deleteSelectedFolder(),
      disabled: !selectedFolder.value || folders.value.length <= 1,
      color: "error",
    },
  ],
];

const deleteSelectedFolder = () => {
  if (!selectedFolder.value || folders.value.length <= 1) return;
  const idx = folders.value.findIndex((f) => f.id === selectedFolder.value.id);
  if (idx === -1) return;
  folders.value.splice(idx, 1);
  // Select another folder (prefer previous, else first)
  if (folders.value.length) {
    selectedFolder.value = folders.value[Math.max(0, idx - 1)];
  } else {
    selectedFolder.value = null;
  }
};
</script>
<template>
  <div class="flex h-screen font-sans text-default bg-default">
    <aside
      class="flex-shrink-0 w-56 bg-default border-r border-default flex flex-col"
    >
      <div
        class="h-16 flex-shrink-0 flex items-center px-4 border-b border-default"
      >
        <h2 class="text-lg font-semibold text-toned">All Files</h2>
      </div>
      <nav class="flex-1 overflow-y-auto p-4 space-y-1 group">
        <div v-for="folder in folders" :key="folder.id" class="w-full">
          <UButton
            :label="editingFolderId === folder.id ? undefined : folder.name"
            icon="i-lucide-folder"
            color="neutral"
            :variant="selectedFolder?.id === folder.id ? 'soft' : 'link'"
            class="w-full justify-start"
            truncate
            @click="selectFolder(folder)"
            @dblclick="startEditFolder(folder)"
          >
            <template v-if="editingFolderId === folder.id">
              <input
                ref="editInput"
                v-model="editingFolderName"
                class="bg-transparent border-b border-default outline-none px-1 text-default w-32"
                autofocus
                @keydown.enter.prevent="saveEditFolder(folder)"
                @keydown.esc="cancelEditFolder"
                @blur="saveEditFolder(folder)"
              />
            </template>
          </UButton>
        </div>
        <div class="border-t border-default my-4 py-2 hidden group-hover:block">
          <UButton
            type="submit"
            icon="i-lucide-plus"
            color="primary"
            variant="link"
            @click="createFolder"
          >
            Create Folder
          </UButton>
        </div>
      </nav>
    </aside>

    <main class="flex-1 flex flex-col">
      <header
        class="h-16 flex-shrink-0 bg-default border-b border-default flex items-center justify-between px-6"
      >
        <UInput
          v-model="searchQuery"
          icon="i-lucide-search"
          placeholder="Search files..."
          class="w-full max-w-xs"
        />
        <div class="flex items-center gap-2 ml-4">
          <UButton
            v-if="selectedFiles?.length > 0"
            icon="i-lucide-trash-2"
            color="error"
            variant="ghost"
            aria-label="Delete image(s)"
            class="mr-1"
            @click="deleteSelectedImages"
          />
          <UDropdownMenu
            :items="settingsDropdownItems"
            :popper="{ placement: 'bottom-end' }"
          >
            <UButton
              icon="i-lucide-settings"
              color="neutral"
              variant="ghost"
              aria-label="Settings"
            />
          </UDropdownMenu>
          <UButton
            :icon="isGridView ? 'i-lucide-layout-grid' : 'i-lucide-list'"
            color="neutral"
            variant="ghost"
            aria-label="Toggle view"
            @click="toggleView"
          />
        </div>
      </header>

      <div class="flex-1 overflow-y-auto p-4">
        <div
          v-if="filteredFiles.length > 0"
          :class="
            isGridView
              ? 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-3 gap-4'
              : 'flex flex-col gap-2'
          "
        >
          <div
            v-for="file in filteredFiles"
            :key="file.id"
            :class="[
              isGridView
                ? 'relative rounded-lg overflow-hidden ring-2 ring-transparent hover:ring-primary-500/50 cursor-pointer transition-all duration-150'
                : 'flex items-center gap-4 rounded-lg overflow-hidden ring-2 ring-transparent hover:ring-primary-500/50 cursor-pointer transition-all duration-150 px-4 py-2 bg-default',
              selectedFiles.some((f) => f.id === file.id)
                ? '!ring-primary-500'
                : '',
            ]"
            @click="toggleFileSelection(file)"
          >
            <div v-if="isGridView" class="relative">
              <img
                :src="file.url"
                :alt="file.name"
                class="w-full h-32 object-cover bg-muted"
              />
              <div
                v-if="selectedFiles.some((f) => f.id === file.id)"
                class="absolute top-2 right-2 w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center text-white"
              >
                <UIcon name="i-lucide-check" class="w-4 h-4" />
              </div>
            </div>
            <template v-else>
              <img
                :src="file.url"
                :alt="file.name"
                class="w-16 h-16 object-cover bg-muted rounded-md"
              />
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-toned truncate">
                  {{ file.name }}
                </p>
              </div>
              <div
                v-if="selectedFiles.some((f) => f.id === file.id)"
                class="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center text-white"
              >
                <UIcon name="i-lucide-check" class="w-4 h-4" />
              </div>
            </template>
            <div v-if="isGridView" class="bg-default/80 backdrop-blur-sm p-2">
              <p class="text-xs font-medium text-toned truncate">
                {{ file.name }}
              </p>
            </div>
          </div>
        </div>
        <div
          v-else
          class="flex flex-col items-center justify-center h-full text-toned"
        >
          <UIcon name="i-lucide-folder-open" class="w-16 h-16 mb-4" />
          <h3 class="text-lg font-semibold">No files found</h3>
          <p class="text-sm">Try a different search or folder.</p>
        </div>
      </div>
    </main>

    <UCard>
      <template #header>
        <h3 class="text-lg font-semibold">Upload Files</h3>
      </template>

      <div class="space-y-6">
        <div
          :class="[
            'border-2 border-dashed rounded-lg p-12 text-center transition-colors duration-200',
            isDragging
              ? 'border-primary-500 bg-primary-50'
              : 'border-default/20 hover:border-primary-400',
          ]"
          @click="$refs.fileInput.click()"
          @dragover.prevent="onDragOver"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop"
        >
          <input
            ref="fileInput"
            type="file"
            multiple
            class="hidden"
            @change="onFileSelect"
          />
          <UIcon
            name="i-lucide-image-up"
            class="mx-auto h-12 w-12 text-gray-400"
          />
          <p class="mt-2 text-sm text-toned">
            <UButton variant="link">Click to upload</UButton> or drag and drop
          </p>
          <p class="mt-1 text-xs text-muted">PNG, JPG, GIF up to 10MB</p>
        </div>

        <div v-if="stagedFiles.length > 0">
          <h4 class="font-semibold text-toned mb-2">Files to upload:</h4>
          <ul class="space-y-2 max-h-48 overflow-y-auto p-1">
            <li
              v-for="(file, index) in stagedFiles"
              :key="index"
              class="flex items-center justify-between bg-muted p-2 rounded-md"
            >
              <span class="text-sm text-default truncate w-full pr-4">{{
                file.name
              }}</span>
              <UButton
                color="red"
                variant="ghost"
                icon="i-lucide-trash-2"
                size="xs"
                @click="removeStagedFile(index)"
              />
            </li>
          </ul>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end space-x-3">
          <UButton
            variant="outline"
            color="neutral"
            @click="isUploadModalOpen = false"
          >
            Cancel
          </UButton>
          <UButton :disabled="stagedFiles.length === 0" @click="uploadFiles">
            Upload {{ stagedFiles.length }} File(s)
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>

