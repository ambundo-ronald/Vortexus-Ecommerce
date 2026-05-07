import { useEffect } from "react";

import MaterialIcon from "./MaterialIcon.jsx";
import { useUiStore } from "../../store/ui.store";

const toneIcon = {
  success: "check_circle",
  danger: "error",
  warning: "warning",
  info: "info"
};

function ToastItem({ notification }) {
  const dismiss = useUiStore((state) => state.dismissNotification);
  const icon = notification.icon || toneIcon[notification.tone] || toneIcon.info;

  useEffect(() => {
    const timer = window.setTimeout(() => dismiss(notification.id), 3600);
    return () => window.clearTimeout(timer);
  }, [dismiss, notification.id]);

  return (
    <article className={`toast toast--${notification.tone}`} role="status" aria-live="polite">
      <span className="toast__icon">
        <MaterialIcon name={icon} size={20} filled />
      </span>
      <div className="toast__body">
        {notification.title ? <strong>{notification.title}</strong> : null}
        {notification.message ? <p>{notification.message}</p> : null}
      </div>
      <button type="button" onClick={() => dismiss(notification.id)} aria-label="Dismiss message">
        <MaterialIcon name="close" size={18} />
      </button>
    </article>
  );
}

export default function ToastViewport() {
  const notifications = useUiStore((state) => state.notifications);

  if (!notifications.length) return null;

  return (
    <div className="toast-viewport" aria-label="Notifications">
      {notifications.map((notification) => (
        <ToastItem key={notification.id} notification={notification} />
      ))}
    </div>
  );
}
