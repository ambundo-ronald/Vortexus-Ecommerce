import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { mediaUrl } from "../../utils/media";

function heroStyle(block) {
  return {
    "--marketing-bg": block.background_color || undefined,
    "--marketing-color": block.text_color || undefined
  };
}

function heroImageUrl(block) {
  return mediaUrl(block.image_url);
}

function HeroSlideLink({ block, children }) {
  const href = block.cta_url || "/catalog";
  const external = /^https?:\/\//i.test(href);

  if (external) {
    return (
      <a className="hero-image-slide" href={href} target="_blank" rel="noreferrer" style={heroStyle(block)}>
        {children}
      </a>
    );
  }

  return (
    <Link className="hero-image-slide" to={href} style={heroStyle(block)}>
      {children}
    </Link>
  );
}

export default function HeroImageCarousel({ blocks = [], loading = false }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const slides = blocks;

  useEffect(() => {
    if (slides.length < 2) return undefined;

    const timer = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % slides.length);
    }, 4200);

    return () => window.clearInterval(timer);
  }, [slides.length]);

  useEffect(() => {
    setActiveIndex(0);
  }, [blocks.length]);

  if (loading && !blocks.length) {
    return <section className="hero-image-carousel skeleton-block" aria-label="Loading featured offers" />;
  }

  if (!slides.length) return null;

  return (
    <section className="hero-image-carousel" aria-label="Featured offers">
      <div className="hero-image-carousel__track" style={{ transform: `translateX(-${activeIndex * 100}%)` }}>
        {slides.map((block, index) => (
          <HeroSlideLink block={block} key={block.id || block.slug || block.image_url}>
            <img src={heroImageUrl(block)} alt={block.image_alt || block.title || ""} loading={index === 0 ? "eager" : "lazy"} />
            <div className="hero-image-slide__copy">
              {block.eyebrow ? <span>{block.eyebrow}</span> : null}
              <strong>{block.headline || block.title}</strong>
              {block.body ? <p>{block.body}</p> : null}
              {block.cta_text ? <em>{block.cta_text}</em> : null}
            </div>
          </HeroSlideLink>
        ))}
      </div>
      {slides.length > 1 ? (
        <div className="hero-image-carousel__dots" aria-hidden="true">
          {slides.map((block, index) => (
            <span className={index === activeIndex ? "active" : ""} key={block.id || block.slug || block.image_url} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
