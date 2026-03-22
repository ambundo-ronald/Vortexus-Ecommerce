<script lang="ts" setup>
import { useChat } from '~/composables/useChat';

const { chats, chatMessages, selectedChatId, sendMessage: send } = useChat();
const chatMessage = ref("");

const formatTime = (dateString: string) => {
  return new Date(dateString).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const sendMessage = () => {
  send(chatMessage.value);
  chatMessage.value = "";
};
</script>
<template>
  <div class="min-h-full h-auto max-w-screen-2xl mx-auto">
    <div class="w-full flex items-start gap-4 p-4">
      <UCard class="w-[460px]">
        <div class="divide-y divide-default space-y-4">
          <div
            v-for="chat in chats"
            :key="chat.id"
            :class="[
              'w-full flex gap-4 pb-4 last:pb-0'
            ]"
            @click="selectedChatId = chat.id"
          >
            <img
              :src="chat.avatar"
              alt="avatar"
              class="w-10 h-10 rounded-full object-cover border border-default"
            >
            <div class="flex flex-col">
              <div class="flex items-center justify-between">
                <span class="font-medium text-default truncate">{{ chat.name }}</span>
                <span v-if="chat.unread" class="ml-2 bg-success text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">{{ chat.unread }}</span>
              </div>
              <div class="text-dimmed text-xs">{{ chat.lastMessage }}</div>
            </div>
          </div>
        </div>
      </UCard>
      
      <UCard class="w-full">
        <template #header>
          <div class="flex items-center gap-4">
            <span class="w-2 h-2 rounded-full inline-block bg-success" />
            <h3 class="text-lg font-medium text-default">Customer Chat</h3>
          </div>
        </template>

        <div>
          <!-- Messages Area -->
          <div class="space-y-4 max-h-96 overflow-y-auto mb-6 pr-2">
            <div
              v-for="message in chatMessages"
              :key="message.id"
              :class="[
                'flex',
                message.sender === 'support' ? 'justify-end' : 'justify-start',
              ]"
            >
              <div
                :class="[
                  'max-w-xs lg:max-w-md px-4 py-2 rounded-2xl text-sm',
                  message.sender === 'support'
                    ? 'bg-blue-500 text-white rounded-br-md'
                    : 'text-default rounded-bl-md',
                ]"
              >
                <p class="leading-relaxed">{{ message.message }}</p>
                <div
                  :class="[
                    'text-xs mt-1 opacity-70',
                    message.sender === 'support'
                      ? 'text-default'
                      : 'text-dimmed',
                  ]"
                >
                  {{ formatTime(message.timestamp) }}
                  <span v-if="message.platform === 'whatsapp'" class="ml-2">
                    <svg
                      v-if="message.sender !== 'support'"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 175.216 175.552"
                      style="max-width: 20px; width: 100%; height: auto"
                    >
                      <defs>
                        <linearGradient
                          id="b"
                          x1="85.915"
                          x2="86.535"
                          y1="32.567"
                          y2="137.092"
                          gradientUnits="userSpaceOnUse"
                        >
                          <stop offset="0" stop-color="#57d163" />
                          <stop offset="1" stop-color="#23b33a" />
                        </linearGradient>
                        <filter
                          id="a"
                          width="1.115"
                          height="1.114"
                          x="-.057"
                          y="-.057"
                          color-interpolation-filters="sRGB"
                        >
                          <feGaussianBlur stdDeviation="3.531" />
                        </filter>
                      </defs>
                      <path
                        fill="#b3b3b3"
                        d="m54.532 138.45 2.235 1.324c9.387 5.571 20.15 8.518 31.126 8.523h.023c33.707 0 61.139-27.426 61.153-61.135.006-16.335-6.349-31.696-17.895-43.251A60.75 60.75 0 0 0 87.94 25.983c-33.733 0-61.166 27.423-61.178 61.13a60.98 60.98 0 0 0 9.349 32.535l1.455 2.312-6.179 22.558zm-40.811 23.544L24.16 123.88c-6.438-11.154-9.825-23.808-9.821-36.772.017-40.556 33.021-73.55 73.578-73.55 19.681.01 38.154 7.669 52.047 21.572s21.537 32.383 21.53 52.037c-.018 40.553-33.027 73.553-73.578 73.553h-.032c-12.313-.005-24.412-3.094-35.159-8.954zm0 0"
                        filter="url(#a)"
                      />
                      <path
                        fill="#fff"
                        d="m12.966 161.238 10.439-38.114a73.42 73.42 0 0 1-9.821-36.772c.017-40.556 33.021-73.55 73.578-73.55 19.681.01 38.154 7.669 52.047 21.572s21.537 32.383 21.53 52.037c-.018 40.553-33.027 73.553-73.578 73.553h-.032c-12.313-.005-24.412-3.094-35.159-8.954z"
                      />
                      <path
                        fill="url(#linearGradient1780)"
                        d="M87.184 25.227c-33.733 0-61.166 27.423-61.178 61.13a60.98 60.98 0 0 0 9.349 32.535l1.455 2.312-6.179 22.559 23.146-6.069 2.235 1.324c9.387 5.571 20.15 8.518 31.126 8.524h.023c33.707 0 61.14-27.426 61.153-61.135a60.75 60.75 0 0 0-17.895-43.251 60.75 60.75 0 0 0-43.235-17.929z"
                      />
                      <path
                        fill="url(#b)"
                        d="M87.184 25.227c-33.733 0-61.166 27.423-61.178 61.13a60.98 60.98 0 0 0 9.349 32.535l1.455 2.313-6.179 22.558 23.146-6.069 2.235 1.324c9.387 5.571 20.15 8.517 31.126 8.523h.023c33.707 0 61.14-27.426 61.153-61.135a60.75 60.75 0 0 0-17.895-43.251 60.75 60.75 0 0 0-43.235-17.928z"
                      />
                      <path
                        fill="#fff"
                        fill-rule="evenodd"
                        d="M68.772 55.603c-1.378-3.061-2.828-3.123-4.137-3.176l-3.524-.043c-1.226 0-3.218.46-4.902 2.3s-6.435 6.287-6.435 15.332 6.588 17.785 7.506 19.013 12.718 20.381 31.405 27.75c15.529 6.124 18.689 4.906 22.061 4.6s10.877-4.447 12.408-8.74 1.532-7.971 1.073-8.74-1.685-1.226-3.525-2.146-10.877-5.367-12.562-5.981-2.91-.919-4.137.921-4.746 5.979-5.819 7.206-2.144 1.381-3.984.462-7.76-2.861-14.784-9.124c-5.465-4.873-9.154-10.891-10.228-12.73s-.114-2.835.808-3.751c.825-.824 1.838-2.147 2.759-3.22s1.224-1.84 1.836-3.065.307-2.301-.153-3.22-4.032-10.011-5.666-13.647"
                      />
                    </svg>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Input Area -->
          <div class="space-y-4">
            <!-- Message Input -->
            <div class="flex gap-3">
              <UTextarea
                v-model="chatMessage"
                placeholder="Type your message..."
                :rows="1"
                size="lg"
                class="flex-1 resize-none"
                @keydown.enter.prevent="sendMessage"
              />
              <UButton
                icon="i-lucide-send"
                size="lg"
                class="self-end"
                @click="sendMessage"
              />
            </div>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
