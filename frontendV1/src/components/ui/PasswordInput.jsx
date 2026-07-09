import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

export default function PasswordInput({ className = "", ...props }) {
  const [visible, setVisible] = useState(false);
  const Icon = visible ? EyeOff : Eye;

  return (
    <div className={`password-input ${className}`.trim()}>
      <input {...props} type={visible ? "text" : "password"} />
      <button
        type="button"
        className="password-input__toggle"
        aria-label={visible ? "Hide password" : "Show password"}
        aria-pressed={visible}
        onClick={() => setVisible((current) => !current)}
      >
        <Icon aria-hidden="true" size={19} />
      </button>
    </div>
  );
}
