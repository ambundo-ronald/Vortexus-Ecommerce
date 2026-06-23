import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { mediaUrl } from "../../utils/media";

const fallbackSlides = [
  { image_url: "/hero%20landing%20images/agricultural.jpeg", title: "Agricultural supply", cta_url: "/catalog" },
  { image_url: "/hero%20landing%20images/biomedical.jpeg", title: "Biomedical equipment", cta_url: "/catalog" },
  { image_url: "/hero%20landing%20images/chemicals.jpeg", title: "Industrial chemicals", cta_url: "/catalog" },
  { image_url: "/hero%20landing%20images/mining.jpeg", title: "Mining essentials", cta_url: "/catalog" },
  { image_url: "/hero%20landing%20images/pumps.jpeg", title: "Pumps and parts", cta_url: "/catalog" },
  { image_url: "/hero%20landing%20images/safety%20and%20protection.jpeg", title: "Safety and protection", cta_url: "/catalog" },
  { image_url: "/hero%20landing%20images/smart%20automation.jpeg", title: "Smart automation", cta_url: "/catalog" },
  { image_url: "/hero%20landing%20images/television%20and%20sound%20system%20.png", title: "Audio visual systems", cta_url: "/catalog" },
  { image_url: "/hero%20landing%20images/textile.jpeg", title: "Textile supplies", cta_url: "/catalog" }
];

function heroStyle(block) {
  return {
    "--marketing-bg": block.background_color || undefined,
    "--marketing-color": block.text_color || undefined
  };
}

function heroImageUrl(block) {
  if (!block.id && block.image_url?.startsWith("/hero")) return block.image_url;
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

export default function HeroImageCarousel({ blocks = [], loading = false, useFallback = false }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const slides = blocks.length ? blocks : useFallback ? fallbackSlides : [];

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
