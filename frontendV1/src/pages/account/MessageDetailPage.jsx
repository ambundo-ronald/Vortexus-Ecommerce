import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { storefrontExtrasApi } from "../../api/storefrontExtras.api";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { normalizeApiError } from "../../utils/errorHandler";
import { formatDate } from "../../utils/formatDate";
import "./messages.css";

export default function MessageDetailPage() {
  const { messageId } = useParams();
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const metadata = useMemo(() => message?.metadata || {}, [message]);
  const body = metadata.body || metadata.message || metadata.text || "";
  const metadataRows = useMemo(
    () => Object.entries(metadata).filter(([key]) => !["body", "message", "text", "read", "archived"].includes(key)),
    [metadata]
  );

  const loadMessage = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await storefrontExtrasApi.messages.email(messageId);
      setMessage(payload?.email || payload?.message || payload);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load message.").message);
    } finally {
      setLoading(false);
    }
  }, [messageId]);

  useEffect(() => {
    void loadMessage();
  }, [loadMessage]);

  return (
    <section className="account-page messages-page">
      <Link className="back-link" to="/account/messages">
        <MaterialIcon name="arrow_back" size={18} /> Messages
      </Link>

      {loading ? <Spinner label="Loading message" /> : null}
      <Alert tone="warning">{error}</Alert>

      {!loading && message ? (
        <>
          <div className="message-detail-hero">
            <span className="message-row__icon">
              <MaterialIcon name="mail" size={24} />
            </span>
            <div>
              <p className="eyebrow">{readableEvent(message.event_type)}</p>
              <h1>{message.subject || "Message"}</h1>
              <p>
                {message.recipient ? `${message.recipient} · ` : ""}
                {formatDate(message.sent_at || message.created_at, { time: true })}
              </p>
            </div>
          </div>

          <article className="message-detail-card">
            <div className="message-status-row">
              <span>{message.status || "Status unknown"}</span>
              <span>{readableEvent(message.event_type)}</span>
            </div>

            <div className="message-body">
              {body ? <p>{body}</p> : <p>No message body was stored for this email record.</p>}
            </div>

            {metadataRows.length ? (
              <div className="message-metadata">
                <h2>Details</h2>
                {metadataRows.map(([key, value]) => (
                  <div className="message-metadata__row" key={key}>
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
  return String(value || "Message").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatMetadataValue(value) {
  if (value === null || value === undefined || value === "") return "Not provided";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
