import { useEffect, useRef } from "react";
import toast, { Toaster } from "react-hot-toast";

import { useUiStore } from "../../store/ui.store";

const toneToast = {
  danger: toast.error,
  warning: toast,
  info: toast,
  success: toast.success
};

function ToastMessage({ title, message }) {
  return (
    <div className="react-toast-message">
      {title ? <strong>{title}</strong> : null}
      {message ? <span>{message}</span> : null}
    </div>
  );
}

export default function ToastViewport() {
  const notifications = useUiStore((state) => state.notifications);
  const dismiss = useUiStore((state) => state.dismissNotification);
  const shownIds = useRef(new Set());

  useEffect(() => {
    notifications.forEach((notification) => {
      if (shownIds.current.has(notification.id)) return;

      shownIds.current.add(notification.id);
      const showToast = toneToast[notification.tone] || toast;
      showToast(<ToastMessage title={notification.title} message={notification.message} />, {
        id: String(notification.id),
        duration: 3200,
        icon: notification.tone === "warning" ? "!" : undefined
      });

      window.setTimeout(() => dismiss(notification.id), 3600);
    });
  }, [dismiss, notifications]);

  return (
    <Toaster
      position="bottom-right"
      gutter={10}
      toastOptions={{
        className: "react-hot-toast",
        style: {
          borderRadius: "14px",
          boxShadow: "0 16px 42px rgba(15, 23, 42, 0.18)",
          color: "#0f172a",
          maxWidth: "360px",
          padding: "12px 14px"
        }
      }}
    />
  );
}
