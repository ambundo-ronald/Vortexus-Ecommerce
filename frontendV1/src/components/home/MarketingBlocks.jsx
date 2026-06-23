import { useEffect, useRef, useState } from "react";
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
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (blocks.length < 2) return undefined;

    const timer = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % blocks.length);
    }, 5200);

    return () => window.clearInterval(timer);
  }, [blocks.length]);

  useEffect(() => {
    setActiveIndex(0);
  }, [blocks.length]);

  if (!blocks.length) return null;

  const block = blocks[activeIndex % blocks.length];
  const imageUrl = block.image_url ? mediaUrl(block.image_url) : "";

  return (
    <MarketingLink block={block} className="marketing-announcement" style={blockStyle(block)}>
      <span className="marketing-announcement__media" aria-hidden={!imageUrl}>
        {imageUrl ? (
          <img src={imageUrl} alt={block.image_alt || block.title || block.headline || "Announcement"} loading="lazy" />
        ) : (
          <MaterialIcon name="campaign" size={18} />
        )}
      </span>
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
      <div className="section-heading section-heading--marketing">
        <h2>Featured campaigns</h2>
        <Link to="/offers">View all</Link>
      </div>
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
      <div className="section-heading section-heading--marketing">
        <h2>Brand You Love</h2>
        <Link to="/catalog">View all</Link>
      </div>
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

export function TopCategoryStrip({ blocks = [] }) {
  const trackRef = useRef(null);

  if (!blocks.length) return null;

  function scrollTrack(direction) {
    const track = trackRef.current;
    if (!track) return;
    track.scrollBy({
      left: direction * Math.max(260, track.clientWidth * 0.78),
      behavior: "smooth"
    });
  }

  return (
    <section className="marketing-category-section" aria-label="Top categories">
      <div className="section-heading section-heading--marketing">
        <h2>Top categories</h2>
        <Link to="/catalog">View all</Link>
      </div>
      <button className="marketing-category-nav marketing-category-nav--prev" type="button" aria-label="Previous categories" onClick={() => scrollTrack(-1)}>
        <MaterialIcon name="chevron_left" size={28} />
      </button>
      <div className="marketing-category-track" ref={trackRef}>
        {blocks.map((block) => (
          <MarketingLink block={block} className="marketing-category-card" key={block.id || block.slug} style={blockStyle(block)}>
            <span className="marketing-category-card__media">
              {block.image_url ? (
                <img src={mediaUrl(block.image_url)} alt={block.image_alt || block.title} loading="lazy" />
              ) : (
                <MaterialIcon name="category" size={28} />
              )}
            </span>
            <strong>{block.headline || block.title}</strong>
            {block.body ? <small>{block.body}</small> : null}
            <MaterialIcon name="arrow_forward" size={18} />
          </MarketingLink>
        ))}
      </div>
      <button className="marketing-category-nav marketing-category-nav--next" type="button" aria-label="Next categories" onClick={() => scrollTrack(1)}>
        <MaterialIcon name="chevron_right" size={28} />
      </button>
    </section>
  );
}
