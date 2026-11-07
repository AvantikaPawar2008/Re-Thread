const LEFT = [
  { label: "Make an Impact", top: "17%" },
  { label: "Sustainable Choice", top: "62%" },
  { label: "Carbon Tokens", top: "84%" },
];

const RIGHT = [
  { label: "Eco Impact", top: "17%" },
  { label: "Waste Reduced", top: "52%" },
  { label: "CO₂ Saved", top: "84%" },
];

function Chip({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-white/85 px-3 py-1 text-[11px] font-medium text-charcoal shadow-sm ring-1 ring-line backdrop-blur">
      <span className="h-1.5 w-1.5 rounded-full bg-forest" aria-hidden />
      {label}
    </span>
  );
}

/** Decorative only. Shown only on very wide screens (1700px+), where the side
 *  gutters are wide enough that the chips never overlap the content. */
export function FloatingLabels() {
  return (
    <div className="pointer-events-none fixed inset-0 z-10 hidden min-[1700px]:block" aria-hidden>
      {LEFT.map((c) => (
        <div key={c.label} className="absolute left-5" style={{ top: c.top }}>
          <Chip label={c.label} />
        </div>
      ))}
      {RIGHT.map((c) => (
        <div key={c.label} className="absolute right-5" style={{ top: c.top }}>
          <Chip label={c.label} />
        </div>
      ))}
    </div>
  );
}