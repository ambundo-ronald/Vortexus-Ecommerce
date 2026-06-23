import MaterialIcon from "./MaterialIcon.jsx";
import { loadingMessagesFor } from "../../constants/loadingMessages";
import { useLoadingMessages } from "../../hooks/useLoadingMessages";
import "./LoadingExperience.css";

export default function LoadingExperience({
  label = "Loading",
  messages,
  compact = false,
  delayMs = 180,
  messageIntervalMs = 1800,
  timeoutMs = 10000,
  onRetry
}) {
  const resolvedMessages = messages?.length ? messages : loadingMessagesFor(label);
  const { visible, messageIndex, takingLonger } = useLoadingMessages({
    messageCount: resolvedMessages.length,
    delayMs,
    messageIntervalMs,
    timeoutMs
  });

  if (!visible) return null;

  const currentMessage = takingLonger
    ? "This is taking longer than expected"
    : resolvedMessages[messageIndex];

  return (
    <div
      className={`loading-experience${compact ? " loading-experience--compact" : ""}`}
      role="status"
      aria-live="polite"
      aria-label={label}
    >
      <div className="loading-experience__visual" aria-hidden="true">
        <span className="loading-experience__orbit loading-experience__orbit--one" />
        <span className="loading-experience__orbit loading-experience__orbit--two" />
        <span className="loading-experience__orbit loading-experience__orbit--three" />
        <MaterialIcon name="shopping_bag" size={compact ? 20 : 25} />
      </div>

      <div className="loading-experience__copy">
        <strong key={currentMessage}>{currentMessage}</strong>
        <span>
          {takingLonger
            ? "Your connection may be slow. We are still working on it."
            : "This should only take a moment."}
        </span>
      </div>

      {takingLonger && onRetry ? (
        <button className="loading-experience__retry" type="button" onClick={onRetry}>
          <MaterialIcon name="refresh" size={18} />
          Try again
        </button>
      ) : null}
    </div>
  );
}

