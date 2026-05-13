import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import Alert from "../../components/ui/Alert.jsx";
import EmptyState from "../../components/ui/EmptyState.jsx";
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

export default function NotificationsPage() {
  const notify = useUiStore((state) => state.notify);
  const [searchParams, setSearchParams] = useSearchParams();
  const mode = searchParams.get("view") === "archive" ? "archive" : "inbox";
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = mode === "archive"
        ? await storefrontExtrasApi.messages.archivedNotifications()
        : await storefrontExtrasApi.messages.notifications();
      const results = payload?.results || [];
      setNotifications(mode === "archive" ? results : results.filter((item) => !isArchived(item)));
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load notifications.").message);
    } finally {
      setLoading(false);
    }
  }, [mode]);

  useEffect(() => {
    void loadNotifications();
  }, [loadNotifications]);

  async function markRead(notification) {
    setSaving(true);
    setError("");
    try {
      await storefrontExtrasApi.messages.markRead(notification.id);
      notify({ title: "Marked as read", message: "Notification updated.", icon: "mark_email_read" });
      await loadNotifications();
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not update notification.").message);
    } finally {
      setSaving(false);
    }
  }

  async function archive(notification) {
    setSaving(true);
    setError("");
    try {
      await storefrontExtrasApi.messages.archive(notification.id);
      notify({ title: "Archived", message: "Notification moved to archive.", icon: "archive" });
      await loadNotifications();
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not archive notification.").message);
    } finally {
      setSaving(false);
    }
  }

  async function readAll() {
    setSaving(true);
    setError("");
    try {
      await storefrontExtrasApi.messages.readAll();
      notify({ title: "All read", message: "Notifications marked as read.", icon: "done_all" });
      await loadNotifications();
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not mark notifications as read.").message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="account-page notifications-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>

      <div className="notifications-hero">
        <div>
          <p className="eyebrow">Notifications</p>
          <h1>{mode === "archive" ? "Archive" : "Inbox"}</h1>
          <p>Order updates, account messages, and system notices.</p>
        </div>
        <button className="secondary-button" type="button" disabled={saving || !notifications.length} onClick={() => void readAll()}>
          <MaterialIcon name="done_all" size={18} />
          Read all
        </button>
      </div>

      <div className="notification-tabs" role="tablist" aria-label="Notification views">
        <button className={mode === "inbox" ? "active" : ""} type="button" onClick={() => setSearchParams({})}>
          Inbox
        </button>
        <button className={mode === "archive" ? "active" : ""} type="button" onClick={() => setSearchParams({ view: "archive" })}>
          Archive
        </button>
      </div>

      <Alert>{error}</Alert>
      {loading ? <Spinner label="Loading notifications" /> : null}

      {!loading && !notifications.length ? (
        <EmptyState
          title={mode === "archive" ? "No archived notifications" : "No notifications"}
          message={mode === "archive" ? "Archived messages will appear here." : "New account and order messages will appear here."}
        />
      ) : null}

      {notifications.length ? (
        <div className="notification-list">
          {notifications.map((notification) => (
            <article className={`notification-card${isRead(notification) ? "" : " unread"}`} key={notification.id}>
              <Link className="notification-card__main" to={`/account/notifications/${notification.id}`}>
                <span className="notification-card__icon">
                  <MaterialIcon name={isRead(notification) ? "mail" : "mark_email_unread"} size={21} />
                </span>
                <span className="notification-card__copy">
                  <strong>{notification.subject || readableEvent(notification.event_type)}</strong>
                  <small>{formatDate(notification.sent_at || notification.created_at, { time: true })}</small>
                  <em>{notification.status || readableEvent(notification.event_type)}</em>
                </span>
              </Link>
              <div className="notification-card__actions">
                {!isRead(notification) ? (
                  <button type="button" disabled={saving} onClick={() => void markRead(notification)}>
                    Read
                  </button>
                ) : null}
                {!isArchived(notification) ? (
                  <button type="button" disabled={saving} onClick={() => void archive(notification)}>
                    Archive
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function readableEvent(value = "") {
  return String(value || "Notification").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
