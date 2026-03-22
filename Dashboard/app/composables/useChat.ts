import { ref } from 'vue';

export const useChat = () => {
  const chats = ref([
    {
      id: 1,
      name: "John Doe",
      lastMessage: "My order ID is SO-563, please process faster",
      avatar: "/images/products/iphone.webp",
      unread: 2,
      platform: "whatsapp",
      lastActive: "2025-06-18T10:10:00Z",
    },
    {
      id: 2,
      name: "Jane Smith",
      lastMessage: "Thank you for the update!",
      avatar: "/images/products/apple-watch-series-10.webp",
      unread: 0,
      platform: "whatsapp",
      lastActive: "2025-06-18T09:50:00Z",
    },
    {
      id: 3,
      name: "Alex Lee",
      lastMessage: "Can I change my shipping address?",
      avatar: "/images/products/msi-mag-271qpx-qd-oled.webp",
      unread: 1,
      platform: "whatsapp",
      lastActive: "2025-06-18T08:30:00Z",
    },
  ]);

  const chatMessages = ref([
    {
      id: 1,
      sender: "customer",
      message:
        "Hi there, I need to check the status of my order. It has been in transit for several days.",
      timestamp: "2025-06-18T10:00:00Z",
      platform: "whatsapp",
    },
    {
      id: 2,
      sender: "support",
      message: "Hello! Let me check your order ID?",
      timestamp: "2025-06-18T10:05:00Z",
      platform: "whatsapp",
    },
    {
      id: 3,
      sender: "customer",
      message: "My order ID is SO-563, please process faster",
      timestamp: "2025-06-18T10:10:00Z",
      platform: "whatsapp",
    },
    {
      id: 4,
      sender: "support",
      message:
        "I understand your concern. Let me get the order details again here",
      timestamp: "2025-06-18T10:15:00Z",
      platform: "whatsapp",
    },
  ]);

  const selectedChatId = ref(1);
  const supportUser = ref("support");

  const sendMessage = (message: string) => {
    if (!message.trim()) return;

    chatMessages.value.push({
      id: Date.now(),
      sender: supportUser.value,
      message,
      timestamp: new Date().toISOString(),
      platform: "whatsapp",
    });
  };

  return {
    chats,
    chatMessages,
    selectedChatId,
    supportUser,
    sendMessage,
  };
};
