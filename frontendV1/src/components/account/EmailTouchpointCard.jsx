import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import "./EmailTouchpointCard.css";

export default function EmailTouchpointCard({
  actions = [],
  className = "",
  eyebrow = "Customer email",
  icon = "outgoing_mail",
  message,
  meta,
  title,
  tone = "info"
}) {
  if (!title && !message) return null;

  return (
    <aside className={`email-touchpoint email-touchpoint--${tone}${className ? ` ${className}` : ""}`}>
      <span className="email-touchpoint__icon">
        <MaterialIcon name={icon} size={22} filled />
      </span>
      <div className="email-touchpoint__copy">
        <p className="email-touchpoint__eyebrow">{eyebrow}</p>
        {title ? <strong>{title}</strong> : null}
        {message ? <span>{message}</span> : null}
        {meta ? <small>{meta}</small> : null}
      </div>
      {actions.length ? (
        <div className="email-touchpoint__actions">
          {actions.map((action) => (
            action.to ? (
              <Link className="email-touchpoint__action" to={action.to} key={action.label}>
                {action.icon ? <MaterialIcon name={action.icon} size={17} /> : null}
                {action.label}
              </Link>
            ) : (
              <button className="email-touchpoint__action" type="button" onClick={action.onClick} key={action.label}>
                {action.icon ? <MaterialIcon name={action.icon} size={17} /> : null}
                {action.label}
              </button>
            )
          ))}
        </div>
      ) : null}
    </aside>
  );
}
