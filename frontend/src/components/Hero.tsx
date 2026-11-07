"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, Recycle } from "lucide-react";
import { Reveal } from "@/components/Reveal";

/* The hero photo is looked up in these folders, trying each name and ending. */
const FOLDERS = ["/images", "/fabrics"];
const ENDINGS = ["jpg", "jpeg", "png", "webp", "avif"];
const HERO_NAMES = ["hero", "hero-fabric", "hero-bg", "hero-image"];

function buildSources(names: string[]): string[] {
  const out: string[] = [];
  for (const name of names) {
    for (const folder of FOLDERS) {
      for (const ending of ENDINGS) {
        out.push(`${folder}/${name}.${ending}`);
      }
    }
  }
  return out;
}

/* If no photo is found, show a woven-fabric look instead of a flat colour block. */
const WEAVE_FALLBACK: React.CSSProperties = {
  backgroundColor: "#b79d77",
  backgroundImage: [
    "repeating-linear-gradient(0deg, rgba(255,255,255,0.14) 0 2px, transparent 2px 9px)",
    "repeating-linear-gradient(90deg, rgba(0,0,0,0.09) 0 2px, transparent 2px 9px)",
    "linear-gradient(145deg, #cdb690, #8f7753)",
  ].join(", "),
};

const HeroPhoto: React.FC<{ alt: string }> = ({ alt }) => {
  const sources = useMemo(() => buildSources(HERO_NAMES), []);
  const [index, setIndex] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const src = index < sources.length ? sources[index] : null;

  useEffect(() => {
    const img = imgRef.current;
    if (img && img.complete && img.naturalWidth > 0) setLoaded(true);
  }, [src]);

  return (
    <div className="relative h-full w-full overflow-hidden" role="img" aria-label={alt} style={WEAVE_FALLBACK}>
      {src && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          ref={imgRef}
          key={src}
          src={src}
          alt=""
          loading="eager"
          onLoad={() => setLoaded(true)}
          onError={() => {
            setLoaded(false);
            setIndex((i) => i + 1);
          }}
          className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-700 ${
            loaded ? "opacity-100" : "opacity-0"
          }`}
        />
      )}
    </div>
  );
};

const STATS = [
  {
    value: "7.07M",
    label: "Tonnes of textile waste each year (India)",
    pos: "-left-3 top-6 sm:-left-10",
  },
  {
    value: "1.92B m³",
    label: "Water used by the textile industry per year",
    pos: "-right-3 top-[52%] sm:-right-10",
  },
  {
    value: "123B",
    label: "Microfibres shed from washing machines per year",
    pos: "-bottom-5 -left-3 sm:-left-12",
  },
];

const CHOICES = [
  { title: "Throw it in the bin", text: "Ends up in landfill for years to come." },
  { title: "Give it to an NGO", text: "But will they take it, and is it wearable?" },
];

const go = (id: string) =>
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

export const Hero: React.FC = () => (
  <section className="mx-auto max-w-7xl px-5 pb-20 pt-12 sm:pt-16">
    <div className="grid items-center gap-14 lg:grid-cols-2 lg:gap-10">
      {/* Left: text */}
      <Reveal>
        <p className="mb-6 flex items-center gap-3 text-xs font-bold uppercase tracking-[0.25em] text-brand-600">
          <span className="h-px w-10 bg-brand-600/40" />
          The wardrobe crisis
        </p>

        <h1 className="text-[2.75rem] font-extrabold leading-[1.03] tracking-tight text-charcoal sm:text-6xl xl:text-7xl">
          Your closet is full,{" "}
          <span className="text-brand-600">but giving clothes</span> a second life{" "}
          <span className="font-medium italic text-ghost">isn’t easy.</span>
        </h1>

        <p className="mt-7 max-w-lg text-lg leading-relaxed text-muted">
          Snap a photo. RE-THREAD checks fabric, wear and damage, then helps you decide
          whether to resell, repair, donate, recycle or return it to the brand.
        </p>

        <div className="mt-9 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => go("analyze")}
            className="group inline-flex items-center gap-2 rounded-full bg-forest px-7 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-sky-600/30 transition hover:-translate-y-0.5 hover:bg-evergreen focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600"
          >
            Analyze My Garment
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden />
          </button>

          <button
            type="button"
            onClick={() => go("reuse")}
            className="inline-flex items-center gap-2 rounded-full border border-line bg-white px-6 py-3.5 text-[15px] font-semibold text-charcoal transition hover:border-forest/50 hover:bg-mist focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600"
          >
            <Recycle className="h-4 w-4 text-brand-600" aria-hidden />
            Explore Sustainable Fashion
          </button>
        </div>

        <div className="mt-10 grid max-w-xl gap-4 sm:grid-cols-2">
          {CHOICES.map((c) => (
            <div
              key={c.title}
              className="rounded-2xl border border-line bg-white p-5 shadow-sm"
            >
              <p className="font-semibold text-charcoal">{c.title}</p>
              <p className="mt-1.5 text-sm italic leading-snug text-muted">{c.text}</p>
            </div>
          ))}
        </div>
      </Reveal>

      {/* Right: photo with stat cards */}
      <Reveal delay={120}>
        <div className="relative mx-auto w-full max-w-[34rem] lg:max-w-none">
          <div className="rounded-[2.25rem] bg-white p-2.5 shadow-[0_30px_70px_-30px_rgba(21,27,43,0.4)]">
            <div className="h-[26rem] overflow-hidden rounded-[1.8rem] sm:h-[32rem] lg:h-[34rem]">
              <HeroPhoto alt="Folded natural fabric in soft daylight" />
            </div>
          </div>

          {STATS.map((s) => (
            <div
              key={s.value}
              className={`absolute max-w-[15rem] rounded-2xl bg-white/85 px-5 py-4 shadow-[0_18px_40px_-18px_rgba(21,27,43,0.3)] ring-1 ring-white/70 backdrop-blur-md transition-transform duration-300 hover:-translate-y-1 ${s.pos}`}
            >
              <p className="text-3xl font-extrabold tracking-tight text-charcoal">{s.value}</p>
              <p className="mt-1 text-[11px] font-semibold uppercase leading-snug tracking-wide text-muted">
                {s.label}
              </p>
            </div>
          ))}
        </div>
      </Reveal>
    </div>
  </section>
);

export default Hero;