import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";

export default function BreadcrumbNav({ items = [], className = "product-breadcrumbs" }) {
  const cleanItems = items.filter((item) => item?.label);
  if (!cleanItems.length) return null;

  return (
    <nav className={className} aria-label="Breadcrumb">
      <ol>
        {cleanItems.map((item, index) => {
          const isCurrent = index === cleanItems.length - 1;
          return (
            <li key={`${item.href || item.label}-${index}`}>
              {index > 0 ? <MaterialIcon name="chevron_right" size={16} aria-hidden="true" /> : null}
              {item.href && !isCurrent ? (
                <Link to={item.href}>{item.label}</Link>
              ) : (
                <span aria-current={isCurrent ? "page" : undefined}>{item.label}</span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
