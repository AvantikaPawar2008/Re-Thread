"use client";

import React, { useMemo, useState } from "react";
import {
  ArrowRight,
  ChevronDown,
  Droplets,
  FlaskConical,
  Hand,
  Recycle,
  Scissors,
  Search,
  ShieldCheck,
  Shirt,
  Sparkles,
  X,
} from "lucide-react";

/* ------------------------------------------------------------------
   COLOUR: change these three values to re-colour the whole page.
   ------------------------------------------------------------------ */
const ACCENT = "#1d5c8c";
const ACCENT_DARK = "#0b2a44";
const ACCENT_SOFT = "#e6eef5";

type Group = "natural" | "synthetic" | "semi-synthetic" | "weave";
type Level = "Low" | "Medium" | "High";

interface Fabric {
  id: string;
  name: string;
  group: Group;
  summary: string;
  feel: string;
  breathability: Level;
  durability: Level;
  care: string;
  secondLife: string[];
  note: string;
}

interface Garment {
  id: string;
  name: string;
  typical: string;
  wear: string[];
  ideas: string[];
  tip: string;
}

const GROUP_LABEL: Record<Group, string> = {
  natural: "Natural",
  synthetic: "Synthetic",
  "semi-synthetic": "Semi-synthetic",
  weave: "Weave / knit",
};

const GROUP_OVERLAY: Record<Group, string> = {
  natural: "bg-white/90 text-[#0b2a44]",
  synthetic: "bg-slate-900/80 text-white",
  "semi-synthetic": "bg-amber-100/95 text-amber-900",
  weave: "bg-white/90 text-slate-800",
};

const FABRICS: Fabric[] = [
  {
    id: "cotton",
    name: "Cotton",
    group: "natural",
    summary: "A soft plant fibre from the cotton boll, and the most common fabric in everyday clothes.",
    feel: "Soft, matte and slightly dry",
    breathability: "High",
    durability: "Medium",
    care: "Usually machine washable. Hot water and high heat can shrink it, so wash warm or cool and dry gently.",
    secondLife: ["Patchwork and quilt panels", "Tote bags and pouches", "Cleaning cloths and cotton rags"],
    note: "Absorbs moisture well and creases easily. Good candidate for repair or reuse before recycling.",
  },
  {
    id: "linen",
    name: "Linen",
    group: "natural",
    summary: "Made from the flax plant. Strong, crisp and cool, it is popular in summer clothing.",
    feel: "Crisp, textured, a little coarse at first",
    breathability: "High",
    durability: "High",
    care: "Wash cool or warm and iron while slightly damp. It gets softer with every wash.",
    secondLife: ["Napkins and table runners", "Market bags", "Patchwork with other natural fabrics"],
    note: "Wrinkles easily, which is part of its look. Strong enough that worn linen is usually still reusable.",
  },
  {
    id: "wool",
    name: "Wool",
    group: "natural",
    summary: "An animal fibre from sheep. Warm and insulating, even when it is a little damp.",
    feel: "Warm, springy, sometimes scratchy",
    breathability: "High",
    durability: "Medium",
    care: "Wash cool or by hand with a gentle detergent and dry flat. Heat and rubbing can make it shrink or felt.",
    secondLife: ["Darned or visibly mended knitwear", "Felted crafts and coasters", "Cushion covers or mittens"],
    note: "Attracts moths if stored dirty. Small holes are very repairable by darning.",
  },
  {
    id: "silk",
    name: "Silk",
    group: "natural",
    summary: "A fine protein fibre made by silkworms. Smooth, lustrous and light.",
    feel: "Smooth, cool and slightly slippery",
    breathability: "Medium",
    durability: "Low",
    care: "Hand wash cool or dry clean. Avoid wringing, strong sunlight and perfume or deodorant on the fabric.",
    secondLife: ["Scrunchies and hair ties", "Linings and patchwork accents", "Gift wrap and small pouches"],
    note: "Strong for how fine it is, but sweat and sunlight weaken it over time.",
  },
  {
    id: "denim",
    name: "Denim",
    group: "natural",
    summary: "Not a fibre but a sturdy twill weave, usually cotton with indigo-dyed threads.",
    feel: "Thick, stiff and rugged; softens with wear",
    breathability: "Medium",
    durability: "High",
    care: "Wash cold and inside out to protect the colour. Wash less often than other clothes.",
    secondLife: ["Tote bags and aprons", "Patches for other jeans", "Shorts from worn-out legs"],
    note: "Many jeans contain a little elastane for stretch, which makes them harder to recycle.",
  },
  {
    id: "polyester",
    name: "Polyester",
    group: "synthetic",
    summary: "A strong plastic-based fibre found in sportswear, linings, dresses and many blends.",
    feel: "Smooth, light, sometimes slick",
    breathability: "Low",
    durability: "High",
    care: "Wash cool and avoid high heat. Wash in a laundry bag to reduce microfibre shedding.",
    secondLife: ["Bags and covers", "Cleaning cloths", "Craft projects that need a durable fabric"],
    note: "Dries fast and resists wrinkles, but can hold odours and shed tiny plastic fibres in the wash.",
  },
  {
    id: "nylon",
    name: "Nylon",
    group: "synthetic",
    summary: "A very strong, lightweight synthetic used in jackets, bags, hosiery and activewear.",
    feel: "Smooth, light, slightly shiny",
    breathability: "Low",
    durability: "High",
    care: "Wash cool and dry on low heat or air dry. High heat can melt it.",
    secondLife: ["Repair patches for outdoor gear", "Pouches and stuff sacks", "Reinforcing bag straps"],
    note: "Excellent abrasion resistance, so worn nylon is often still structurally strong.",
  },
  {
    id: "acrylic",
    name: "Acrylic",
    group: "synthetic",
    summary: "A soft, lightweight synthetic that imitates wool, common in budget sweaters and blankets.",
    feel: "Soft, light and slightly fluffy",
    breathability: "Low",
    durability: "Medium",
    care: "Wash cool and dry flat or on low heat. High heat can flatten and stretch the knit.",
    secondLife: ["Pom-poms and soft stuffing", "Cushion covers", "Unravelled yarn for small crafts"],
    note: "Pills easily and builds static, but is light and warm for the price.",
  },
  {
    id: "viscose",
    name: "Viscose (Rayon)",
    group: "semi-synthetic",
    summary: "Made from wood pulp that is chemically processed into fibre. It feels like a natural fabric.",
    feel: "Soft, cool and fluid, with a good drape",
    breathability: "Medium",
    durability: "Low",
    care: "Check the label: many pieces need a gentle or cold wash. It is weak when wet, so avoid wringing.",
    secondLife: ["Linings and scarves from larger pieces", "Patchwork accents", "Pillow covers"],
    note: "Can shrink and lose shape if washed hot. Handle gently when repairing.",
  },
  {
    id: "elastane",
    name: "Elastane (Spandex)",
    group: "synthetic",
    summary: "A stretch fibre almost always blended in small amounts with others, such as cotton or polyester.",
    feel: "Stretchy and bouncy, hidden inside other fabrics",
    breathability: "Low",
    durability: "Medium",
    care: "Avoid high heat and chlorine, which break down the stretch over time.",
    secondLife: ["Hair ties and headbands", "Stretch fabric patches", "Donate while the stretch still recovers"],
    note: "Even a small amount can make a garment hard to recycle, because the fibres are hard to separate.",
  },
  {
    id: "jute",
    name: "Jute",
    group: "natural",
    summary: "A coarse, strong fibre from the jute plant, used mostly for sacks, rugs and bags rather than clothing.",
    feel: "Rough, dry and fibrous",
    breathability: "Medium",
    durability: "High",
    care: "Spot clean or dry clean. It weakens and can rot if it stays wet.",
    secondLife: ["Planters and storage baskets", "Rugs and mats", "Shopping bags"],
    note: "Fully plant-based and biodegradable, but not comfortable against skin.",
  },
  {
    id: "hemp",
    name: "Hemp",
    group: "natural",
    summary: "A strong bast fibre from the hemp plant, similar to linen but tougher.",
    feel: "Textured and firm, softening with washing",
    breathability: "High",
    durability: "High",
    care: "Wash cool or warm. It softens with every wash and holds its shape well.",
    secondLife: ["Tote bags and aprons", "Cushion covers", "Patchwork with other natural fabrics"],
    note: "Very long-lasting, so worn hemp is usually still good for reuse.",
  },
  {
    id: "cashmere",
    name: "Cashmere",
    group: "natural",
    summary: "A very fine, soft wool from cashmere goats, used for premium sweaters and scarves.",
    feel: "Very soft, light and warm",
    breathability: "High",
    durability: "Low",
    care: "Hand wash cool or dry clean, then dry flat. Avoid hanging when wet.",
    secondLife: ["Elbow patches on other knits", "Felted mittens or pouches", "Visible darning on small holes"],
    note: "Pills easily because the fibres are fine. A fabric comb or shaver can restore the surface.",
  },
  {
    id: "khadi",
    name: "Khadi",
    group: "natural",
    summary: "Hand-spun, hand-woven cloth, most often cotton, with a long history in India.",
    feel: "Slightly rough, airy and textured",
    breathability: "High",
    durability: "Medium",
    care: "Wash cold and separately for the first few washes, as it can shrink and release dye.",
    secondLife: ["Kantha-style quilting", "Cushion covers", "Tote bags and table linen"],
    note: "Warm in winter and cool in summer, and each piece has natural variations in the weave.",
  },
  {
    id: "muslin",
    name: "Muslin",
    group: "natural",
    summary: "A light, loosely woven cotton cloth that is soft and breathable.",
    feel: "Soft, thin and airy",
    breathability: "High",
    durability: "Low",
    care: "Machine wash warm or cool. It gets softer with each wash.",
    secondLife: ["Straining cloths and cheesecloth", "Gift wrap and pouches", "Light patchwork layers"],
    note: "Thin, so it tears more easily than heavier cotton, but it dries very quickly.",
  },
  {
    id: "modal",
    name: "Modal",
    group: "semi-synthetic",
    summary: "A soft fibre made from beech wood pulp, similar to viscose but usually stronger.",
    feel: "Silky, smooth and light",
    breathability: "Medium",
    durability: "Medium",
    care: "Wash cool and avoid high heat. It holds its shape better than viscose.",
    secondLife: ["Soft pillowcases", "Headbands and scrunchies", "Patchwork with similar knits"],
    note: "Often blended with cotton or elastane in underwear and T-shirts.",
  },
  {
    id: "lyocell",
    name: "Lyocell (Tencel)",
    group: "semi-synthetic",
    summary: "A wood-pulp fibre made in a process that reuses most of its solvent. Smooth and strong.",
    feel: "Smooth, cool and drapey",
    breathability: "High",
    durability: "Medium",
    care: "Wash cool on a gentle cycle. Avoid hot dryers, which can stiffen it.",
    secondLife: ["Linings and scarves", "Pouches and small bags", "Soft patchwork"],
    note: "Often blended with cotton or linen. The brand name Tencel is a type of lyocell.",
  },
  {
    id: "flannel",
    name: "Flannel",
    group: "weave",
    summary: "A soft, brushed fabric, usually cotton or wool, used for shirts, pyjamas and bedding.",
    feel: "Soft, fuzzy and warm",
    breathability: "Medium",
    durability: "Medium",
    care: "Wash warm or cool and dry on low heat. It may shrink a little at first.",
    secondLife: ["Burp cloths and reusable wipes", "Quilt backing", "Draught excluders"],
    note: "The brushed surface pills with age, but the base cloth is often still sound.",
  },
  {
    id: "corduroy",
    name: "Corduroy",
    group: "weave",
    summary: "A ridged pile fabric, usually cotton. The ridges are called wales.",
    feel: "Soft ridges with a thick, sturdy body",
    breathability: "Medium",
    durability: "High",
    care: "Wash inside out in cool water and avoid high heat to protect the pile.",
    secondLife: ["Cushion covers", "Tote bags", "Knee or elbow patches"],
    note: "Very hard-wearing. The ridges can flatten with heavy use but the fabric stays strong.",
  },
  {
    id: "velvet",
    name: "Velvet",
    group: "weave",
    summary: "A soft pile fabric that can be made from silk, cotton or polyester.",
    feel: "Plush, smooth and slightly heavy",
    breathability: "Low",
    durability: "Medium",
    care: "Follow the label, as many velvets need dry cleaning. Never press flat with a hot iron.",
    secondLife: ["Pouches and jewellery bags", "Scrunchies", "Trims and decorative accents"],
    note: "The pile crushes easily. Steam, rather than ironing, helps lift it.",
  },
  {
    id: "satin",
    name: "Satin",
    group: "weave",
    summary: "A weave with a glossy face, made from silk, polyester or other fibres.",
    feel: "Smooth, shiny and slippery",
    breathability: "Low",
    durability: "Low",
    care: "Hand wash cool or follow the label. Snags easily, so keep it away from rough surfaces.",
    secondLife: ["Scrunchies", "Linings", "Gift pouches"],
    note: "Satin describes the weave, not the fibre, so check the label for what it is made of.",
  },
  {
    id: "georgette",
    name: "Georgette",
    group: "weave",
    summary: "A light, slightly crinkled, sheer fabric common in sarees, dupattas and dresses.",
    feel: "Light, airy and a little grainy",
    breathability: "Medium",
    durability: "Low",
    care: "Hand wash cool or dry clean. Avoid wringing and strong heat.",
    secondLife: ["Dupattas and scarves", "Layered patchwork", "Hair accessories"],
    note: "Can be silk or polyester. It frays easily, so finish raw edges.",
  },
  {
    id: "chiffon",
    name: "Chiffon",
    group: "weave",
    summary: "A very light, sheer plain weave, made from silk or polyester.",
    feel: "Floaty, sheer and delicate",
    breathability: "Medium",
    durability: "Low",
    care: "Hand wash cool or use a mesh laundry bag on a gentle cycle.",
    secondLife: ["Scarves and trims", "Hair ties", "Overlays for craft projects"],
    note: "Snags and frays easily, so sew it with fine needles and a small stitch.",
  },
  {
    id: "fleece",
    name: "Fleece",
    group: "weave",
    summary: "A soft, warm, brushed knit, usually made from polyester.",
    feel: "Fluffy, soft and light",
    breathability: "Low",
    durability: "Medium",
    care: "Wash cool and skip fabric softener. Wash in a laundry bag to reduce microfibre shedding.",
    secondLife: ["Pet bedding", "Draught excluders", "Hand warmers and stuffing"],
    note: "Warm for its weight but pills with wear. Donate while it is still soft.",
  },
  {
    id: "canvas",
    name: "Canvas",
    group: "weave",
    summary: "A heavy, tightly woven plain-weave fabric, usually cotton or a cotton blend.",
    feel: "Stiff, thick and rugged",
    breathability: "Medium",
    durability: "High",
    care: "Wash cool and air dry. It can shrink in hot water.",
    secondLife: ["Tote bags and aprons", "Bag patches and straps", "Upholstery repairs"],
    note: "One of the tougher everyday fabrics, so worn items are often worth reusing.",
  },
  {
    id: "terry",
    name: "Terry cloth",
    group: "weave",
    summary: "A looped pile cotton fabric used for towels and bathrobes.",
    feel: "Looped, absorbent and thick",
    breathability: "High",
    durability: "Medium",
    care: "Wash warm and dry on medium heat. Skip fabric softener, which reduces absorbency.",
    secondLife: ["Cleaning cloths", "Pet towels", "Reusable wipes or bath mats"],
    note: "Very absorbent, which makes worn towels excellent for cleaning jobs.",
  },
  {
    id: "jersey",
    name: "Jersey knit",
    group: "weave",
    summary: "A soft, stretchy knit used for T-shirts, tops and loungewear, in cotton, polyester or blends.",
    feel: "Soft, stretchy and smooth",
    breathability: "Medium",
    durability: "Medium",
    care: "Wash cool and dry flat or on low heat. Hot dryers can warp the shape.",
    secondLife: ["T-shirt yarn for crafts", "Headbands", "Cleaning cloths"],
    note: "The edges curl when cut, which is exactly what makes it useful for T-shirt yarn.",
  },
];

const GARMENTS: Garment[] = [
  {
    id: "jeans",
    name: "Jeans & denim trousers",
    typical: "Cotton denim, often with a little elastane",
    wear: ["Worn or torn knees", "Split crotch seams", "Frayed hems"],
    ideas: ["Patch or darn the damage", "Cut into shorts", "Make a tote bag or apron"],
    tip: "Reinforce seams early. A stitched patch inside the knee stops holes from spreading.",
  },
  {
    id: "tshirts",
    name: "T-shirts",
    typical: "Cotton or cotton-polyester jersey knit",
    wear: ["Stretched necklines", "Pilling", "Stains and small holes"],
    ideas: ["Cleaning cloths", "T-shirt yarn for braiding or bags", "Donate if still in good shape"],
    tip: "Stains on cotton often lift with a soak before you decide to give up on a tee.",
  },
  {
    id: "shirts",
    name: "Shirts & kurtas",
    typical: "Woven cotton, linen or poly-cotton",
    wear: ["Frayed collars and cuffs", "Missing buttons", "Torn seams"],
    ideas: ["Replace buttons or turn the collar", "Shorten sleeves", "Napkins, pillow covers or patchwork"],
    tip: "Seam tears are the easiest fix. Re-stitch along the original line with matching thread.",
  },
  {
    id: "sarees",
    name: "Sarees & dupattas",
    typical: "Silk, cotton, or synthetic blends such as georgette",
    wear: ["Pulled threads", "Frayed edges and falls", "Fading"],
    ideas: ["Dupattas or cushion covers", "Curtains and table linen", "Kantha-style quilting with layered sarees"],
    tip: "Long, uncut lengths of fabric are valuable. Keep them whole when you can.",
  },
  {
    id: "knitwear",
    name: "Sweaters & knitwear",
    typical: "Wool, acrylic or cotton knits",
    wear: ["Moth holes", "Pilling", "Stretched cuffs"],
    ideas: ["Darn holes with visible mending", "Remove pills with a fabric shaver", "Felt old wool for crafts"],
    tip: "Wool darns beautifully. Acrylic is harder to repair but easy to de-pill.",
  },
  {
    id: "activewear",
    name: "Activewear",
    typical: "Polyester, nylon and elastane blends",
    wear: ["Lost stretch", "Lingering odour", "Thin spots"],
    ideas: ["Donate while stretch is good", "Look for brand take-back", "Cut into cleaning rags or bands"],
    tip: "Blends like these are the hardest to recycle, so extending their wear matters most.",
  },
  {
    id: "outerwear",
    name: "Jackets & coats",
    typical: "Wool, polyester, nylon or denim",
    wear: ["Broken zips", "Torn linings", "Worn cuffs"],
    ideas: ["Replace the zip or lining", "Re-bind cuffs", "Donate for winter drives"],
    tip: "A new zip or lining usually costs far less than replacing the whole jacket.",
  },
];

const TESTS = [
  {
    title: "Read the care label",
    how: "Look inside the side seam or neckline for a fibre percentage and washing symbols.",
    meaning: "This is the most reliable clue. Garments labelled with two or more fibres are blends.",
  },
  {
    title: "The squeeze test",
    how: "Hold a handful of fabric tightly for about ten seconds, then let go.",
    meaning: "Cotton, linen and viscose tend to stay creased. Polyester, nylon and wool tend to spring back.",
  },
  {
    title: "The water-drop test",
    how: "Place a single drop of water on a clean, hidden part of the fabric.",
    meaning: "Cotton, linen and viscose usually absorb it quickly. Polyester and nylon tend to let it bead.",
  },
  {
    title: "The stretch test",
    how: "Gently stretch a piece of the fabric and let it go.",
    meaning: "If it snaps back quickly, it likely contains some elastane.",
  },
];

type View = "fabrics" | "garments" | "tests";
type Filter = "all" | Group;

const VIEWS: { id: View; label: string }[] = [
  { id: "fabrics", label: "Fabrics" },
  { id: "garments", label: "Garments" },
  { id: "tests", label: "Quick tests" },
];

const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "natural", label: "Natural" },
  { id: "synthetic", label: "Synthetic" },
  { id: "semi-synthetic", label: "Semi-synthetic" },
  { id: "weave", label: "Weave / knit" },
];

const LEVEL_SEGMENTS: Record<Level, number> = { Low: 1, Medium: 2, High: 3 };

function Meter({ label, level }: { label: string; level: Level }) {
  const filled = LEVEL_SEGMENTS[level];
  return (
    <div className="min-w-0 flex-1">
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
        <span className="text-xs font-semibold text-[#174e7c]">{level}</span>
      </div>
      <div className="flex gap-1.5" role="img" aria-label={`${label}: ${level}`}>
        {[1, 2, 3].map((n) => (
          <span
            key={n}
            className={`h-2 flex-1 rounded-full transition-colors ${n <= filled ? "bg-[#1d5c8c]" : "bg-slate-200"}`}
          />
        ))}
      </div>
    </div>
  );
}

function FabricImage({ id, name }: { id: string; name: string }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return (
      <div
        role="img"
        aria-label={`${name} fabric`}
        className="flex h-52 items-center justify-center bg-gradient-to-br from-[#e6f2fb] via-white to-[#d2e7f6] text-xs font-bold uppercase tracking-[0.2em] text-[#174e7c]"
      >
        {name}
      </div>
    );
  }

  return (
    <div className="h-52 overflow-hidden bg-slate-100">
      <img
        src={`/fabrics/${id}.jpg`}
        alt={`${name} fabric`}
        loading="lazy"
        onError={() => setFailed(true)}
        className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
      />
    </div>
  );
}

function FabricCard({
  fabric,
  open,
  onToggle,
}: {
  fabric: Fabric;
  open: boolean;
  onToggle: () => void;
}) {
  const panelId = `fabric-${fabric.id}-panel`;
  return (
    <article
      className={`group flex flex-col overflow-hidden rounded-3xl border bg-white transition-all duration-300 ${
        open
          ? "border-[#9fc6e4] shadow-xl md:col-span-2 xl:col-span-3"
          : "border-slate-200 shadow-sm hover:-translate-y-1 hover:shadow-xl"
      }`}
    >
      <div className="relative">
        <FabricImage id={fabric.id} name={fabric.name} />
        <span
          className={`absolute left-4 top-4 rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider shadow-sm backdrop-blur ${GROUP_OVERLAY[fabric.group]}`}
        >
          {GROUP_LABEL[fabric.group]}
        </span>
      </div>

      <div className="flex flex-1 flex-col p-6">
        <h2 className="text-2xl font-extrabold tracking-tight">{fabric.name}</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">{fabric.summary}</p>
        <p className="mt-3 text-xs font-medium text-[#1d5c8c]">Feels: {fabric.feel}</p>

        <div className="mt-6 flex gap-6">
          <Meter label="Breathability" level={fabric.breathability} />
          <Meter label="Durability" level={fabric.durability} />
        </div>

        <button
          type="button"
          onClick={onToggle}
          aria-expanded={open}
          aria-controls={panelId}
          className="mt-6 inline-flex w-fit items-center gap-2 rounded-full bg-[#e6f2fb] px-4 py-2 text-sm font-semibold text-[#0b2a44] transition-colors hover:bg-[#0b2a44] hover:text-white"
        >
          {open ? "Close details" : "Care & second life"}
          <ChevronDown className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} aria-hidden />
        </button>

        {open && (
          <div id={panelId} className="mt-6 grid gap-4 border-t border-slate-100 pt-6 md:grid-cols-2">
            <div className="rounded-2xl bg-[#f5f8fb] p-5">
              <p className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#1d5c8c]">
                <Droplets className="h-4 w-4" aria-hidden /> Care
              </p>
              <p className="text-sm leading-relaxed text-slate-700">{fabric.care}</p>
            </div>

            <div className="rounded-2xl bg-[#f5f8fb] p-5">
              <p className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#1d5c8c]">
                <Recycle className="h-4 w-4" aria-hidden /> Second-life ideas
              </p>
              <ul className="space-y-2 text-sm text-slate-700">
                {fabric.secondLife.map((idea) => (
                  <li key={idea} className="flex gap-2.5">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#1d5c8c]" aria-hidden />
                    {idea}
                  </li>
                ))}
              </ul>
            </div>

            <p className="flex gap-3 rounded-2xl border border-[#d2e7f6] bg-[#e6f2fb] p-5 text-sm leading-relaxed text-[#0b2a44] md:col-span-2">
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-[#1d5c8c]" aria-hidden />
              <span>
                <span className="font-bold">Good to know: </span>
                {fabric.note}
              </span>
            </p>
          </div>
        )}
      </div>
    </article>
  );
}

function GarmentCard({ g }: { g: Garment }) {
  return (
    <article className="flex flex-col rounded-3xl border border-slate-200 bg-white p-7 shadow-sm transition-shadow hover:shadow-lg">
      <div className="flex items-start gap-4">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#e6f2fb] text-[#1d5c8c]">
          <Shirt className="h-6 w-6" aria-hidden />
        </span>
        <div>
          <h2 className="text-xl font-extrabold tracking-tight">{g.name}</h2>
          <p className="mt-1 text-xs text-slate-500">Usually: {g.typical}</p>
        </div>
      </div>

      <div className="mt-6 grid gap-6 sm:grid-cols-2">
        <div>
          <p className="mb-3 text-[11px] font-bold uppercase tracking-wider text-amber-700">Common wear</p>
          <div className="flex flex-wrap gap-2">
            {g.wear.map((w) => (
              <span key={w} className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-900">
                {w}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="mb-3 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-[#1d5c8c]">
            <Scissors className="h-3.5 w-3.5" aria-hidden /> Give it a new life
          </p>
          <ul className="space-y-2 text-sm text-slate-700">
            {g.ideas.map((i) => (
              <li key={i} className="flex gap-2.5">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#1d5c8c]" aria-hidden />
                {i}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <p className="mt-6 flex gap-3 rounded-2xl bg-[#f5f8fb] p-4 text-sm text-slate-700">
        <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-[#1d5c8c]" aria-hidden />
        <span>
          <span className="font-semibold">Tip: </span>
          {g.tip}
        </span>
      </p>
    </article>
  );
}

interface FabricGuideProps {
  /** Optional: shows an "Analyze a garment" call to action at the bottom */
  onAnalyze?: () => void;
}

export default function FabricGuide({ onAnalyze }: FabricGuideProps) {
  const [view, setView] = useState<View>("fabrics");
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return FABRICS.filter(
      (f) =>
        (filter === "all" || f.group === filter) &&
        (q === "" || f.name.toLowerCase().includes(q) || f.summary.toLowerCase().includes(q))
    );
  }, [filter, query]);

  const countFor = (id: Filter) =>
    id === "all" ? FABRICS.length : FABRICS.filter((f) => f.group === id).length;

  const colourVars = {
    "--fg-accent": ACCENT,
    "--fg-accent-dark": ACCENT_DARK,
    "--fg-soft": ACCENT_SOFT,
  } as React.CSSProperties;

  return (
    <div className="min-h-screen bg-[#f5f8fc]" style={colourVars}>
      {/* Hero */}
      <header className="relative overflow-hidden bg-gradient-to-br from-[#0b2a44] via-[#1d5c8c] to-[#2f7ab0] text-white">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.07] [background-image:linear-gradient(#fff_1px,transparent_1px),linear-gradient(90deg,#fff_1px,transparent_1px)] [background-size:28px_28px]"
          aria-hidden
        />
        <div className="relative mx-auto grid max-w-6xl gap-12 px-6 pb-20 pt-20 md:grid-cols-[1.4fr_1fr] md:items-end">
          <div>
            <p className="mb-6 flex items-center gap-3 text-xs font-bold uppercase tracking-[0.22em] text-[#bdd9ee]">
              <span className="h-px w-10 bg-[#bdd9ee]" aria-hidden />
              Fabric guide
            </p>
            <h1 className="text-4xl font-extrabold leading-[1.02] tracking-tight md:text-6xl">
              Know what your clothes are <em className="not-italic text-[#b6d9f0]">made of</em>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-[#d6e4ef] md:text-lg">
              Understanding a fabric is the first step to caring for it, repairing it and giving it a second life.
            </p>
            <dl className="mt-10 flex flex-wrap gap-3">
              {[
                { k: FABRICS.length, v: "Fabrics" },
                { k: GARMENTS.length, v: "Garment types" },
                { k: TESTS.length, v: "Quick tests" },
              ].map((s) => (
                <div
                  key={s.v}
                  className="min-w-[128px] rounded-2xl border border-white/15 bg-white/10 px-5 py-4 backdrop-blur-md"
                >
                  <dd className="text-3xl font-extrabold tracking-tight">{s.k}</dd>
                  <dt className="mt-0.5 text-xs font-medium text-[#cfe0ee]">{s.v}</dt>
                </div>
              ))}
            </dl>
          </div>

          <div className="rounded-3xl border border-white/15 bg-white/10 p-7 backdrop-blur-md">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-[#1d5c8c]">
              <FlaskConical className="h-6 w-6" aria-hidden />
            </span>
            <h2 className="mt-5 text-xl font-bold">No label on your garment?</h2>
            <p className="mt-2 text-sm leading-relaxed text-[#d6e4ef]">
              Try four simple at-home checks to get a clue about what it's made of.
            </p>
            <button
              type="button"
              onClick={() => setView("tests")}
              className="mt-6 inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-bold text-[#0b2a44] transition-colors hover:bg-[#e6f2fb]"
            >
              Try quick tests <ArrowRight className="h-4 w-4" aria-hidden />
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 pb-20 pt-10 text-slate-900">
        {/* Sticky tab bar */}
        <nav className="sticky top-24 z-30 -mx-2 mb-10 flex justify-center px-2 md:justify-start">
          <div
            role="tablist"
            aria-label="Guide sections"
            className="inline-flex rounded-full border border-slate-200 bg-white/90 p-1.5 shadow-md backdrop-blur-md"
          >
            {VIEWS.map((v) => (
              <button
                key={v.id}
                type="button"
                role="tab"
                aria-selected={view === v.id}
                onClick={() => setView(v.id)}
                className={`rounded-full px-5 py-2.5 text-sm font-semibold transition-all ${
                  view === v.id ? "bg-[#0b2a44] text-white shadow" : "text-slate-600 hover:text-[#0b2a44]"
                }`}
              >
                {v.label}
              </button>
            ))}
          </div>
        </nav>

        {/* Fabrics */}
        {view === "fabrics" && (
          <div>
            <div className="mb-8 flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
              <label className="relative flex h-12 items-center">
                <span className="sr-only">Search fabrics</span>
                <Search className="pointer-events-none absolute left-4 h-4 w-4 text-slate-400" aria-hidden />
                <input
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search by name or property, e.g. cotton or stretch"
                  className="h-full w-full rounded-2xl border border-transparent bg-[#f5f8fb] pl-11 pr-11 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#1d5c8c] focus:bg-white focus:outline-none"
                />
                {query && (
                  <button
                    type="button"
                    onClick={() => setQuery("")}
                    aria-label="Clear search"
                    className="absolute right-3 flex h-7 w-7 items-center justify-center rounded-full text-slate-500 hover:bg-slate-200"
                  >
                    <X className="h-4 w-4" aria-hidden />
                  </button>
                )}
              </label>

              <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by fabric type">
                {FILTERS.map((f) => (
                  <button
                    key={f.id}
                    type="button"
                    onClick={() => setFilter(f.id)}
                    aria-pressed={filter === f.id}
                    className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold transition-colors ${
                      filter === f.id
                        ? "border-[#0b2a44] bg-[#0b2a44] text-white"
                        : "border-slate-200 bg-white text-slate-700 hover:border-[#1d5c8c] hover:text-[#0b2a44]"
                    }`}
                  >
                    {f.label}
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] ${
                        filter === f.id ? "bg-white/20" : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {countFor(f.id)}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <p className="mb-6 text-sm font-medium text-slate-500" aria-live="polite">
              Showing {visible.length} of {FABRICS.length} fabrics
            </p>

            {visible.length === 0 ? (
              <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center">
                <p className="font-bold">No fabric matches that search.</p>
                <p className="mt-1 text-sm text-slate-600">Try a different name, or clear your filters.</p>
                <button
                  type="button"
                  onClick={() => {
                    setQuery("");
                    setFilter("all");
                  }}
                  className="mt-5 rounded-full bg-[#0b2a44] px-5 py-2 text-sm font-semibold text-white hover:bg-[#1d5c8c]"
                >
                  Clear filters
                </button>
              </div>
            ) : (
              <div className="grid items-start gap-6 md:grid-cols-2 xl:grid-cols-3">
                {visible.map((f) => (
                  <FabricCard
                    key={f.id}
                    fabric={f}
                    open={openId === f.id}
                    onToggle={() => setOpenId(openId === f.id ? null : f.id)}
                  />
                ))}
              </div>
            )}

            <p className="mt-10 text-xs text-slate-500">
              General properties for each fabric type. Individual garments vary with weave, finish and blend.
            </p>
          </div>
        )}

        {/* Garments */}
        {view === "garments" && (
          <div>
            <p className="mb-8 max-w-2xl text-slate-600">
              Common garment types, what they're usually made of, how they wear out, and how to give each one a second
              life.
            </p>
            <div className="grid gap-6 md:grid-cols-2">
              {GARMENTS.map((g) => (
                <GarmentCard key={g.id} g={g} />
              ))}
            </div>
            <p className="mt-10 text-xs text-slate-500">
              Typical materials only. Always check the care label on your own garment.
            </p>
          </div>
        )}

        {/* Quick tests */}
        {view === "tests" && (
          <div className="grid gap-10 lg:grid-cols-[1fr_1.4fr]">
            <div>
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#0b2a44] text-white">
                <Hand className="h-6 w-6" aria-hidden />
              </span>
              <h2 className="mt-5 text-2xl font-extrabold tracking-tight">Check it without a label</h2>
              <p className="mt-3 text-slate-600">
                Four quick checks give you clues about what a fabric is made of. They're hints, not proof, so use them
                alongside the care label whenever you have one.
              </p>
              <p className="mt-6 flex gap-3 rounded-2xl border border-[#d2e7f6] bg-[#e6f2fb] p-5 text-sm text-[#0b2a44]">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#1d5c8c]" aria-hidden />
                Many garments are blends, which can give mixed results. For a model-based estimate from a photo, use
                the Analyze tab.
              </p>
            </div>

            <ol className="relative space-y-6 border-l-2 border-[#d2e7f6] pl-8">
              {TESTS.map((t, i) => (
                <li key={t.title} className="relative rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                  <span className="absolute -left-[46px] top-6 flex h-8 w-8 items-center justify-center rounded-full bg-[#1d5c8c] text-xs font-extrabold text-white ring-4 ring-[#f5f8fc]">
                    {i + 1}
                  </span>
                  <h3 className="text-lg font-bold">{t.title}</h3>
                  <p className="mt-2 text-sm text-slate-700">
                    <span className="font-semibold text-[#0b2a44]">How: </span>
                    {t.how}
                  </p>
                  <p className="mt-2 text-sm text-slate-700">
                    <span className="font-semibold text-[#0b2a44]">What it suggests: </span>
                    {t.meaning}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        )}

        {onAnalyze && (
          <div className="relative mt-20 overflow-hidden rounded-3xl bg-gradient-to-br from-[#0b2a44] via-[#1d5c8c] to-[#2f7ab0] px-8 py-14 text-center text-white">
            <div
              className="pointer-events-none absolute inset-0 opacity-[0.07] [background-image:linear-gradient(#fff_1px,transparent_1px),linear-gradient(90deg,#fff_1px,transparent_1px)] [background-size:24px_24px]"
              aria-hidden
            />
            <div className="relative">
              <h2 className="text-3xl font-extrabold tracking-tight md:text-4xl">
                Not sure what your garment is made of?
              </h2>
              <p className="mx-auto mt-3 max-w-md text-sm text-[#d6e4ef]">
                Upload a photo and let the model estimate the fabric and its condition.
              </p>
              <button
                type="button"
                onClick={onAnalyze}
                className="mt-8 inline-flex items-center gap-2 rounded-full bg-white px-7 py-3.5 text-sm font-bold text-[#0b2a44] transition-colors hover:bg-[#e6f2fb]"
              >
                Analyze a garment <ArrowRight className="h-4 w-4" aria-hidden />
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}