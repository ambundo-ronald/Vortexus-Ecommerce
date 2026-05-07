import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const slides = [
  {
    image: "/images/How%20to%20identify%20the%20right%20Forex%20broker%20for%20you_.jpg",
    title: "Project supplies",
    action: "Shop now"
  },
  {
    image: "/images/Logistics%20Images%20%E2%80%93%20Browse%204%2C101%2C750%20Stock%20Photos%2C%20Vectors%2C%20and%20Video.jpg",
    title: "Fast procurement",
    action: "Browse"
  },
  {
    image: "/images/Unique%205120x1440%20Fall%20Wallpaper.jpg",
    title: "Water systems",
    action: "View deals"
  }
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
        {slides.map((slide) => (
          <Link className="hero-image-slide" to="/catalog" key={slide.image}>
            <img src={slide.image} alt="" />
            <span className="hero-image-slide__copy">
              <strong>{slide.title}</strong>
              <span>{slide.action}</span>
            </span>
          </Link>
        ))}
      </div>
      <div className="hero-image-carousel__dots" aria-hidden="true">
        {slides.map((slide, index) => (
          <span className={index === activeIndex ? "active" : ""} key={slide.image} />
        ))}
      </div>
    </section>
  );
}
