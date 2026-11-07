"use client";

import React, { useEffect, useRef, useState } from "react";

interface RevealProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  /** Delay before the fade-in. Values under 10 are read as seconds, larger values as milliseconds. */
  delay?: number;
  /** How far (in px) the content starts below its final position. */
  y?: number;
  /** Animate only the first time it scrolls into view (default) or every time. */
  once?: boolean;
}

/** Fades and lifts its children into place when they scroll into view. Respects reduced motion. */
export function Reveal({ children, delay = 0, y = 24, once = true, className = "", style, ...rest }: RevealProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (typeof IntersectionObserver === "undefined") {
      const id = requestAnimationFrame(() => setVisible(true));
      return () => cancelAnimationFrame(id);
    }

    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          if (once) io.disconnect();
        } else if (!once) {
          setVisible(false);
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [once]);

  const delayMs = delay < 10 ? delay * 1000 : delay;

  return (
    <div
      ref={ref}
      {...rest}
      className={`transition-[opacity,translate] duration-700 ease-out motion-reduce:translate-y-0 motion-reduce:opacity-100 motion-reduce:transition-none ${
        visible ? "translate-y-0 opacity-100" : "translate-y-[var(--rv-y)] opacity-0"
      } ${className}`}
      style={{ ...style, "--rv-y": `${y}px`, transitionDelay: `${delayMs}ms` } as React.CSSProperties}
    >
      {children}
    </div>
  );
}

export default Reveal;