import { useRef } from "react";
import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
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
  const trackRef = useRef(null);

  if (!blocks.length) return null;

  function scrollTrack(direction) {
    const track = trackRef.current;
    if (!track) return;
    track.scrollBy({
      left: direction * Math.max(220, track.clientWidth * 0.72),
      behavior: "smooth"
    });
  }

  return (
    <section className="marketing-feature-section" aria-label="Featured promotions">
      <button className="marketing-feature-nav marketing-feature-nav--prev" type="button" aria-label="Previous promotions" onClick={() => scrollTrack(-1)}>
        <MaterialIcon name="chevron_left" size={34} />
      </button>
      <div className="marketing-feature-grid" ref={trackRef}>
        {blocks.map((block) => (
          <MarketingLink block={block} className="marketing-feature-card" key={block.id || block.slug} style={blockStyle(block)}>
            <span className="marketing-feature-card__label">{block.eyebrow || block.headline || block.title}</span>
            {block.image_url ? <img src={mediaUrl(block.image_url)} alt={block.image_alt || block.title} loading="lazy" /> : null}
            {!block.image_url ? (
              <div className="marketing-feature-card__fallback">
              <strong>{block.headline || block.title}</strong>
              {block.body ? <p>{block.body}</p> : null}
              </div>
            ) : null}
          </MarketingLink>
        ))}
      </div>
      <button className="marketing-feature-nav marketing-feature-nav--next" type="button" aria-label="Next promotions" onClick={() => scrollTrack(1)}>
        <MaterialIcon name="chevron_right" size={34} />
      </button>
    </section>
  );
}

export function BrandStrip({ blocks = [] }) {
  if (!blocks.length) return null;

  return (
    <section className="marketing-brand-section" aria-label="Featured brands">
      <h2>Brand You Love</h2>
      <div className="marketing-brand-strip">
      {blocks.slice(0, 8).map((block) => (
        <MarketingLink block={block} className="marketing-brand-pill" key={block.id || block.slug} style={blockStyle(block)}>
          {block.image_url ? <img src={mediaUrl(block.image_url)} alt={block.image_alt || block.title} loading="lazy" /> : null}
          <span>{block.headline || block.title}</span>
        </MarketingLink>
      ))}
      </div>
    </section>
  );
}
