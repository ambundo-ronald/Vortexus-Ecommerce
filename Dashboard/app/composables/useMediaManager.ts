import { ref, computed } from 'vue';

export const useMediaManager = () => {
  const folders = ref([
    { id: 1, name: "Documents" },
    { id: 2, name: "Images" },
    { id: 3, name: "Videos" },
    { id: 4, name: "Marketing Assets" },
  ]);

  const allFiles = ref([
    {
      id: 1,
      name: "quarterly-report.pdf",
      folderId: 1,
      url: "https://placehold.co/400x400/6366f1/ffffff?text=PDF",
    },
    {
      id: 2,
      name: "company-handbook.pdf",
      folderId: 1,
      url: "https://placehold.co/400x400/6366f1/ffffff?text=PDF",
    },
    {
      id: 4,
      name: "mountain-vista.jpg",
      folderId: 2,
      url: "https://images.unsplash.com/photo-1549880338-65ddcdfd017b?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=400",
    },
    {
      id: 5,
      name: "city-skyline.png",
      folderId: 2,
      url: "https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=400",
    },
    {
      id: 6,
      name: "forest-path.jpg",
      folderId: 2,
      url: "https://images.unsplash.com/photo-1476231682828-37e571bc172f?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=400",
    },
    {
      id: 11,
      name: "desert-dunes.jpg",
      folderId: 2,
      url: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=400",
    },
    {
      id: 12,
      name: "aurora-borealis.jpg",
      folderId: 2,
      url: "https://images.unsplash.com/photo-1465101046530-73398c7f28ca?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=400",
    },
    {
      id: 13,
      name: "ocean-waves.jpg",
      folderId: 2,
      url: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=400",
    },
    {
      id: 14,
      name: "sunset-hills.jpg",
      folderId: 2,
      url: "https://images.unsplash.com/photo-1469474968028-56623f02e42e?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=400",
    },
    {
      id: 7,
      name: "product-demo.mp4",
      folderId: 3,
      url: "https://placehold.co/400x400/ec4899/ffffff?text=MP4",
    },
    {
      id: 8,
      name: "tutorial.mov",
      folderId: 3,
      url: "https://placehold.co/400x400/ec4899/ffffff?text=MOV",
    },
    {
      id: 9,
      name: "brand-logo.svg",
      folderId: 4,
      url: "https://placehold.co/400x400/f97316/ffffff?text=SVG",
    },
    {
      id: 10,
      name: "banner-ad.png",
      folderId: 4,
      url: "https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=400",
    },
  ]);

  const selectedFolder = ref(folders.value[1]);
  const searchQuery = ref("");
  const selectedFiles = ref([]);

  const filteredFiles = computed(() => {
    if (!selectedFolder.value) return [];
    return allFiles.value.filter((file) => {
      const inFolder = file.folderId === selectedFolder.value.id;
      const matchesSearch = file.name
        .toLowerCase()
        .includes(searchQuery.value.toLowerCase());
      return inFolder && matchesSearch;
    });
  });

  const selectFolder = (folder) => {
    selectedFolder.value = folder;
    selectedFiles.value = [];
    searchQuery.value = "";
  };

  const toggleFileSelection = (file) => {
    const index = selectedFiles.value.findIndex((f) => f.id === file.id);
    if (index > -1) {
      selectedFiles.value.splice(index, 1);
    } else {
      selectedFiles.value.push(file);
    }
  };

  const deleteSelectedImages = () => {
    if (selectedFiles.value.length === 0) return;
    allFiles.value = allFiles.value.filter(
      (file) => !selectedFiles.value.map((i) => i.id).includes(file.id)
    );
    selectedFiles.value = [];
  };

  return {
    folders,
    allFiles,
    selectedFolder,
    searchQuery,
    selectedFiles,
    filteredFiles,
    selectFolder,
    toggleFileSelection,
    deleteSelectedImages,
  };
};
