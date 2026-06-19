import { useEffect, useState } from "react";

export function useLoadingMessages({
  messageCount,
  delayMs = 180,
  messageIntervalMs = 1800,
  timeoutMs = 10000
}) {
  const [visible, setVisible] = useState(delayMs <= 0);
  const [messageIndex, setMessageIndex] = useState(0);
  const [takingLonger, setTakingLonger] = useState(false);

  useEffect(() => {
    setVisible(delayMs <= 0);
    setMessageIndex(0);
    setTakingLonger(false);

    const visibilityTimer = delayMs > 0
      ? window.setTimeout(() => setVisible(true), delayMs)
      : null;
    const messageTimer = messageCount > 1
      ? window.setInterval(() => {
          setMessageIndex((current) => Math.min(current + 1, messageCount - 1));
        }, messageIntervalMs)
      : null;
    const timeoutTimer = timeoutMs > 0
      ? window.setTimeout(() => setTakingLonger(true), timeoutMs)
      : null;

    return () => {
      if (visibilityTimer) window.clearTimeout(visibilityTimer);
      if (messageTimer) window.clearInterval(messageTimer);
      if (timeoutTimer) window.clearTimeout(timeoutTimer);
    };
  }, [delayMs, messageCount, messageIntervalMs, timeoutMs]);

  return { visible, messageIndex, takingLonger };
}

