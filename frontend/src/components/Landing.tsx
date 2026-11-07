"use client";

import { Hero } from "@/components/Hero";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, Recycle, Search, Upload } from "lucide-react";
import { Reveal } from "@/components/Reveal";

const SERIF = "font-[family-name:var(--font-serif)]";

/* ------------------------------------------------------------------
   PHOTO LOOKUP
   Each box lists a few possible file names (without the ending).
   The component tries them in /images and /fabrics, with several
   endings, until one loads. If none load, the pattern stays.
   ------------------------------------------------------------------ */
const FOLDERS = ["/images", "/fabrics"];
const ENDINGS = ["jpg", "jpeg", "png", "webp"];

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

// Photo component
const Photo: React.FC<{
  names: string[];
  alt: string;
  className?: string;
  tone?: string;
}> = ({ names, alt, className = "", tone = "#CFC4AA" }) => {
  const sources = useMemo(() => buildSources(names), [names]);
  const [index, setIndex] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  const src = index < sources.length ? sources[index] : null;

  useEffect(() => {
    const img = imgRef.current;
    if (img && img.complete && img.naturalWidth > 0) {
      setLoaded(true);
    }
  }, [src]);

  return (
    <div
      className={`group relative overflow-hidden ${className}`}
      style={{
        backgroundColor: tone,
        backgroundImage:
          "repeating-linear-gradient(45deg, rgba(255,255,255,.18) 0 2px, transparent 2px 8px), repeating-linear-gradient(-45deg, rgba(0,0,0,.05) 0 2px, transparent 2px 8px)",
      }}
      role="img"
      aria-label={alt}
    >
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
          className={`absolute inset-0 w-full h-full object-cover transition-all duration-700 group-hover:scale-105 ${
            loaded ? "opacity-100" : "opacity-0"
          }`}
        />
      )}
    </div>
  );
};

const scrollTo = (id: string) =>
  document.getElementById(id)?.scrollIntoView({
    behavior: "smooth",
  });

const INTRO_NAMES = ["intro"];

const STEPS = [
  {
    n: "01",
    Icon: Upload,
    title: "Upload Your Garment",
    text: "Share a photo of your clothing to begin your fabric journey.",
  },
  {
    n: "02",
    Icon: Search,
    title: "Discover Its Story",
    text: "Explore fabric identification, garment insights, and environmental impact.",
  },
  {
    n: "03",
    Icon: Recycle,
    title: "Give It a New Life",
    text: "Discover practical ways to repair, reuse, recycle, or repurpose your clothing.",
  },
];

const FABRICS = [
  { name: "Cotton", names: ["cotton"], tone: "#E4DCC8" },
  { name: "Linen", names: ["linen"], tone: "#CFC4AA" },
  { name: "Denim", names: ["denim"], tone: "#5B7189" },
  { name: "Wool", names: ["wool"], tone: "#A89B84" },
  { name: "Silk", names: ["silk"], tone: "#C98F7A" },
];

const IDEAS = [
  {
    title: "Denim tote bag",
    names: ["denim-tote", "tote", "denim_tote"],
    tone: "#5B7189",
    level: "Easy",
    fabrics: "Denim, canvas, heavy cotton",
    text: "Turn worn jeans into a sturdy everyday bag. The legs become the body and the waistband becomes a strap.",
  },
  {
    title: "Fabric patchwork",
    names: ["patchwork"],
    tone: "#B5654A",
    level: "Medium",
    fabrics: "Cotton, linen, poly-cotton",
    text: "Combine offcuts of similar weight into cushion covers, coasters or a quilt panel.",
  },
  {
    title: "Visible mending",
    names: ["mending", "repair", "visible-mending", "visible_mending"],
    tone: "#4F6B3A",
    level: "Easy",
    fabrics: "Most woven and knit fabrics",
    text: "Repair holes and worn knees with contrasting thread so the repair becomes part of the design.",
  },
];

export const Landing: React.FC = () => (
  <div className="text-charcoal">

    {/* New Hero component */}
    <Hero />

    {/* Brand intro */}
    <section className="bg-white/60 border-y border-charcoal/10">
      <div className="max-w-6xl mx-auto px-5 py-20 grid md:grid-cols-12 gap-10 items-center">
        <Reveal className="md:col-span-5">
          <Photo
            names={INTRO_NAMES}
            alt="Hands sewing a garment"
            tone="#A89B84"
            className="w-full h-80"
          />
        </Reveal>

        <Reveal className="md:col-span-6 md:col-start-7" delay={100}>
          <h2 className={`${SERIF} text-3xl md:text-4xl leading-tight`}>
            Most clothes are thrown away long before the fabric is worn out.
          </h2>

          <p className="mt-5 text-charcoal/75 leading-relaxed">
            RE-THREAD helps you look closely at what you own: what the fabric
            appears to be, how worn it is, and what it could become next.
            Understanding a material is the first step to keeping it in use
            and out of landfill.
          </p>
        </Reveal>
      </div>
    </section>

    {/* How it works */}
    <section className="max-w-6xl mx-auto px-5 py-20">
      <Reveal>
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-forest mb-3">
          How it works
        </p>

        <h2 className={`${SERIF} text-3xl md:text-4xl mb-12`}>
          Three simple steps
        </h2>
      </Reveal>

      <ol className="grid md:grid-cols-3 gap-6">
        {STEPS.map((s, i) => (
          <Reveal key={s.n} delay={i * 120}>
            <li className="h-full list-none bg-white border border-charcoal/10 p-7 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-sage">
              <div className="flex items-start justify-between">
                <span className={`${SERIF} text-5xl text-terracotta`}>
                  {s.n}
                </span>

                <span className="w-11 h-11 rounded-full bg-sage/30 text-forest flex items-center justify-center">
                  <s.Icon className="w-5 h-5" aria-hidden />
                </span>
              </div>

              <h3 className="text-lg font-semibold mt-5">{s.title}</h3>

              <p className="text-charcoal/75 mt-2 leading-relaxed">
                {s.text}
              </p>
            </li>
          </Reveal>
        ))}
      </ol>
    </section>

    {/* Fabric discovery */}
    <section className="max-w-6xl mx-auto px-5 pb-20">
      <Reveal>
        <div className="flex flex-wrap items-end justify-between gap-3 mb-8">
          <h2 className={`${SERIF} text-3xl md:text-4xl`}>
            Know your fabrics
          </h2>

          <p className="text-xs text-charcoal/65 max-w-xs sm:text-right">
            A reference selection. These are not predictions about your garment.
          </p>
        </div>
      </Reveal>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {FABRICS.map((f, i) => (
          <Reveal key={f.name} delay={i * 80}>
            <figure>
              <Photo
                names={f.names}
                alt={`${f.name} fabric close-up`}
                tone={f.tone}
                className="w-full aspect-square"
              />

              <figcaption className={`${SERIF} text-lg mt-3`}>
                {f.name}
              </figcaption>
            </figure>
          </Reveal>
        ))}
      </div>
    </section>

    {/* Reuse inspiration */}
    <section
      id="reuse"
      className="bg-white/60 border-y border-charcoal/10 scroll-mt-20"
    >
      <div className="max-w-6xl mx-auto px-5 py-20">
        <Reveal>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-forest mb-3">
            Reuse inspiration
          </p>

          <h2 className={`${SERIF} text-3xl md:text-5xl leading-tight`}>
            Old Clothes. New Possibilities.
          </h2>

          <p className="text-charcoal/75 mt-4 mb-12 max-w-xl">
            Curated ideas to start with. After you identify a fabric below,
            you also get ideas matched to it.
          </p>
        </Reveal>

        <div className="grid md:grid-cols-3 gap-6">
          {IDEAS.map((p, i) => (
            <Reveal key={p.title} delay={i * 120}>
              <article className="h-full bg-ivory border border-charcoal/10 overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
                <Photo
                  names={p.names}
                  alt={p.title}
                  tone={p.tone}
                  className="w-full h-56"
                />

                <div className="p-6">
                  <span className="inline-block text-[11px] font-semibold uppercase tracking-[0.18em] text-forest bg-sage/30 px-2.5 py-1">
                    {p.level}
                  </span>

                  <h3 className={`${SERIF} text-2xl mt-3`}>
                    {p.title}
                  </h3>

                  <p className="text-charcoal/75 mt-3 leading-relaxed text-sm">
                    {p.text}
                  </p>

                  <p className="text-sm mt-4 pt-4 border-t border-charcoal/10">
                    <span className="font-semibold">Materials:</span>{" "}
                    {p.fabrics}
                  </p>
                </div>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>

    {/* Keep this analyze anchor */}
    <div id="analyze" className="scroll-mt-20" />

  </div>
);