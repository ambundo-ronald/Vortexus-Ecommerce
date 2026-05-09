import { Link } from "react-router-dom";

import { mediaUrl } from "../../utils/media";

function blockStyle(block) {
  return {
    "--marketing-bg": block.background_color || undefined,
    "--marketing-color": block.text_color || undefined
  };
}

function MarketingLink({ block, className = "", children, ...props }) {
  const href = block.cta_url || "/catalog";
  const external = /^https?:\/\//i.test(href);

  if (external) {
    return (
      <a className={className} href={href} target="_blank" rel="noreferrer" {...props}>
        {children}
      </a>
    );
  }

  return (
    <Link className={className} to={href} {...props}>
      {children}
    </Link>
  );
}

export function AnnouncementStrip({ blocks = [] }) {
  if (!blocks.length) return null;

  const block = blocks[0];

  return (
    <MarketingLink block={block} className="marketing-announcement" style={blockStyle(block)}>
      <span>{block.eyebrow || "Notice"}</span>
      <strong>{block.headline || block.title}</strong>
      {block.cta_text ? <em>{block.cta_text}</em> : null}
    </MarketingLink>
  );
}

export function PromoBannerStrip({ blocks = [] }) {
  if (!blocks.length) return null;

  return (
    <section className="marketing-promo-grid" aria-label="Promotions">
      {blocks.slice(0, 3).map((block) => (
        <MarketingLink block={block} className="marketing-promo-card" key={block.id || block.slug} style={blockStyle(block)}>
          <div>
            {block.eyebrow ? <span>{block.eyebrow}</span> : null}
            <strong>{block.headline || block.title}</strong>
            {block.body ? <p>{block.body}</p> : null}
          </div>
          {block.image_url ? <img src={mediaUrl(block.image_url)} alt={block.image_alt || block.title} loading="lazy" /> : null}
        </MarketingLink>
      ))}
    </section>
  );
}

export function FeaturedMarketingBlocks({ blocks = [] }) {
  if (!blocks.length) return null;

  return (
    <section className="content-section">
      <div className="section-heading">
        <h2>Featured</h2>
        <Link to="/catalog">View catalog</Link>
      </div>
      <div className="marketing-feature-grid">
        {blocks.slice(0, 4).map((block) => (
          <MarketingLink block={block} className="marketing-feature-card" key={block.id || block.slug} style={blockStyle(block)}>
            {block.image_url ? <img src={mediaUrl(block.image_url)} alt={block.image_alt || block.title} loading="lazy" /> : null}
            <div>
              {block.eyebrow ? <span>{block.eyebrow}</span> : null}
              <strong>{block.headline || block.title}</strong>
              {block.body ? <p>{block.body}</p> : null}
            </div>
          </MarketingLink>
        ))}
      </div>
    </section>
  );
}

export function BrandStrip({ blocks = [] }) {
  if (!blocks.length) return null;

  return (
    <section className="marketing-brand-strip" aria-label="Featured brands">
      {blocks.slice(0, 8).map((block) => (
        <MarketingLink block={block} className="marketing-brand-pill" key={block.id || block.slug} style={blockStyle(block)}>
          {block.image_url ? <img src={mediaUrl(block.image_url)} alt={block.image_alt || block.title} loading="lazy" /> : null}
          <span>{block.headline || block.title}</span>
        </MarketingLink>
      ))}
    </section>
  );
}
