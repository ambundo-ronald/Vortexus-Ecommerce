import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const slides = [
  "/hero%20landing%20images/agricultural.jpeg",
  "/hero%20landing%20images/biomedical.jpeg",
  "/hero%20landing%20images/chemicals.jpeg",
  "/hero%20landing%20images/mining.jpeg",
  "/hero%20landing%20images/pumps.jpeg",
  "/hero%20landing%20images/safety%20and%20protection.jpeg",
  "/hero%20landing%20images/smart%20automation.jpeg",
  "/hero%20landing%20images/television%20and%20sound%20system%20.png",
  "/hero%20landing%20images/textile.jpeg"
];

export default function HeroImageCarousel() {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % slides.length);
    }, 4200);

    return () => window.clearInterval(timer);
  }, []);

  return (
    <section className="hero-image-carousel" aria-label="Featured offers">
      <div className="hero-image-carousel__track" style={{ transform: `translateX(-${activeIndex * 100}%)` }}>
        {slides.map((image) => (
          <Link className="hero-image-slide" to="/catalog" key={image}>
            <img src={image} alt="" />
          </Link>
        ))}
      </div>
      <div className="hero-image-carousel__dots" aria-hidden="true">
        {slides.map((image, index) => (
          <span className={index === activeIndex ? "active" : ""} key={image} />
        ))}
      </div>
    </section>
  );
}
