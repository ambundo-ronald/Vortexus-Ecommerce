import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import Alert from "../../components/ui/Alert.jsx";
import EmptyState from "../../components/ui/EmptyState.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { emailEventMeta, emailStatusLabel } from "../../utils/emailEvents";
import { normalizeApiError } from "../../utils/errorHandler";
import { formatDate } from "../../utils/formatDate";
import "./messages.css";

export default function MessagesPage() {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadMessages = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.messages.emails();
      setMessages(payload?.results || []);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load messages.").message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMessages();
  }, [loadMessages]);

  const filteredMessages = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return messages;
    return messages.filter((message) => {
      const content = [message.subject, message.event_type, message.status, message.recipient].filter(Boolean).join(" ").toLowerCase();
      return content.includes(term);
    });
  }, [messages, query]);

  return (
    <section className="account-page messages-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>

      <div className="messages-hero">
        <div>
          <p className="eyebrow">Messages</p>
          <h1>Email history</h1>
          <p>Receipts, order updates, and account emails sent by the store.</p>
        </div>
        <button className="secondary-button" type="button" disabled={loading} onClick={() => void loadMessages()}>
          <MaterialIcon name="refresh" size={18} />
          Refresh
        </button>
      </div>

      <label className="message-search">
        <MaterialIcon name="search" size={19} />
        <input
          type="search"
          value={query}
          placeholder="Search messages..."
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>

      <Alert tone="warning">{error}</Alert>
      {loading ? <Spinner label="Loading messages" /> : null}

      {!loading && !filteredMessages.length ? (
        <EmptyState
          title={query ? "No matching messages" : "No messages yet"}
          message={query ? "Try another search term." : "Store emails sent to your account will appear here."}
        />
      ) : null}

      {filteredMessages.length ? (
        <div className="message-list">
          {filteredMessages.map((message) => {
            const meta = emailEventMeta(message.event_type);
            return (
              <Link className={`message-row message-row--${meta.tone}`} to={`/account/messages/${message.id}`} key={message.id}>
                <span className="message-row__icon">
                  <MaterialIcon name={meta.icon} size={21} filled={message.status === "sent"} />
                </span>
                <span className="message-row__body">
                  <strong>{message.subject || meta.label}</strong>
                  <small>{meta.label} · {message.recipient || "Your account"}</small>
                </span>
                <span className="message-row__meta">
                  <em>{emailStatusLabel(message.status)}</em>
                  <small>{formatDate(message.sent_at || message.created_at, { time: true })}</small>
                </span>
                <MaterialIcon name="chevron_right" size={20} />
              </Link>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
