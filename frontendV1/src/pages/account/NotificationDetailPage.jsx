import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useUiStore } from "../../store/ui.store";
import { normalizeApiError } from "../../utils/errorHandler";
import { formatDate } from "../../utils/formatDate";
import "./notifications.css";

function isRead(notification) {
  return Boolean(notification?.metadata?.read);
}

function isArchived(notification) {
  return Boolean(notification?.metadata?.archived);
}

export default function NotificationDetailPage() {
  const { notificationId } = useParams();
  const notify = useUiStore((state) => state.notify);
  const [notification, setNotification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const metadata = useMemo(() => notification?.metadata || {}, [notification]);
  const body = metadata.body || metadata.message || metadata.text || "";
  const metadataRows = useMemo(
    () => Object.entries(metadata).filter(([key]) => !["body", "message", "text", "read", "archived"].includes(key)),
    [metadata]
  );

  const loadNotification = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.messages.notification(notificationId);
      setNotification(payload?.notification || payload?.email || payload);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load notification.").message);
    } finally {
      setLoading(false);
    }
  }, [notificationId]);

  useEffect(() => {
    void loadNotification();
  }, [loadNotification]);

  async function markRead() {
    if (!notification) return;
    setSaving(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.messages.markRead(notification.id);
      setNotification(payload?.notification || payload?.email || notification);
      notify({ title: "Marked as read", message: "Notification updated.", icon: "mark_email_read" });
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not mark notification as read.").message);
    } finally {
      setSaving(false);
    }
  }

  async function archive() {
    if (!notification) return;
    setSaving(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.messages.archive(notification.id);
      setNotification(payload?.notification || payload?.email || notification);
      notify({ title: "Archived", message: "Notification moved to archive.", icon: "archive" });
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not archive notification.").message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="account-page notifications-page">
      <Link className="back-link" to="/account/notifications">
        <MaterialIcon name="arrow_back" size={18} /> Notifications
      </Link>

      {loading ? <Spinner label="Loading notification" /> : null}
      <Alert tone="warning">{error}</Alert>

      {!loading && notification ? (
        <>
          <div className="notification-detail-hero">
            <span className={`notification-detail-hero__icon${isRead(notification) ? "" : " unread"}`}>
              <MaterialIcon name={isRead(notification) ? "mail" : "mark_email_unread"} size={26} />
            </span>
            <div>
              <p className="eyebrow">{readableEvent(notification.event_type)}</p>
              <h1>{notification.subject || "Notification"}</h1>
              <p>
                {notification.recipient ? `${notification.recipient} · ` : ""}
                {formatDate(notification.sent_at || notification.created_at, { time: true })}
              </p>
            </div>
            <div className="notification-detail-hero__actions">
              {!isRead(notification) ? (
                <button className="secondary-button" type="button" disabled={saving} onClick={() => void markRead()}>
                  <MaterialIcon name="mark_email_read" size={18} />
                  Mark read
                </button>
              ) : null}
              {!isArchived(notification) ? (
                <button className="secondary-button" type="button" disabled={saving} onClick={() => void archive()}>
                  <MaterialIcon name="archive" size={18} />
                  Archive
                </button>
              ) : null}
            </div>
          </div>

          <article className="notification-detail-card">
            <div className="notification-status-row">
              <span>{notification.status || "Status unknown"}</span>
              {!isRead(notification) ? <strong>Unread</strong> : <strong>Read</strong>}
              {isArchived(notification) ? <strong>Archived</strong> : null}
            </div>

            <div className="notification-message-body">
              {body ? <p>{body}</p> : <p>No message body was stored for this notification.</p>}
            </div>

            {metadataRows.length ? (
              <div className="notification-metadata">
                <h2>Details</h2>
                {metadataRows.map(([key, value]) => (
                  <div className="notification-metadata__row" key={key}>
                    <span>{readableEvent(key)}</span>
                    <strong>{formatMetadataValue(value)}</strong>
                  </div>
                ))}
              </div>
            ) : null}
          </article>
        </>
      ) : null}
    </section>
  );
}

function readableEvent(value = "") {
  return String(value || "Notification").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatMetadataValue(value) {
  if (value === null || value === undefined || value === "") return "Not provided";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
