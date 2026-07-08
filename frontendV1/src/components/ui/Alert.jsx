import { useEffect, useRef } from "react";
import Swal from "sweetalert2";
import "sweetalert2/dist/sweetalert2.min.css";

const ALERT_DEDUPE_MS = 30000;
const shownAtByKey = new Map();
let activeAlertKey = "";

const toneConfig = {
  danger: {
    icon: "error",
    title: "Something went wrong",
  },
  error: {
    icon: "error",
    title: "Something went wrong",
  },
  warning: {
    icon: "warning",
    title: "Please check this",
  },
  info: {
    icon: "info",
    title: "Notice",
  },
  success: {
    icon: "success",
    title: "Done",
  },
};

function alertText(value) {
  if (value === null || value === undefined || value === false) return "";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.map(alertText).filter(Boolean).join(" ");
  if (value?.props?.children) return alertText(value.props.children);
  return "";
}

export default function Alert({ tone = "danger", children }) {
  const lastMessageRef = useRef("");
  const message = alertText(children).trim() || "Please try again.";

  useEffect(() => {
    if (!children) {
      lastMessageRef.current = "";
      return;
    }

    const key = `${tone}:${message}`;
    const now = Date.now();
    const lastShownAt = shownAtByKey.get(key) || 0;
    if (!message || lastMessageRef.current === key || now - lastShownAt < ALERT_DEDUPE_MS) return;
    if (Swal.isVisible() && activeAlertKey === key) return;

    lastMessageRef.current = key;
    shownAtByKey.set(key, now);
    activeAlertKey = key;

    const config = toneConfig[tone] || toneConfig.danger;
    void Swal.fire({
      icon: config.icon,
      title: config.title,
      text: message,
      confirmButtonText: "OK",
      confirmButtonColor: "#3d7cff",
      buttonsStyling: true,
      customClass: {
        popup: "store-swal-popup",
        title: "store-swal-title",
        htmlContainer: "store-swal-text",
        confirmButton: "store-swal-confirm",
      },
      willClose: () => {
        if (activeAlertKey === key) activeAlertKey = "";
      },
    });
  }, [children, message, tone]);

  return null;
}
