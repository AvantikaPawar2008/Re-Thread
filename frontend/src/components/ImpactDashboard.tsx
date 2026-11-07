"use client";

import React from "react";
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  Clock,
  Droplets,
  Info,
  Leaf,
  Recycle,
  Repeat,
  Sparkles,
} from "lucide-react";

export type ImpactMetric = {
  id: string;
  label: string;
  value: number;
  unit: string;
  equivalent?: string;
  share?: number; // 0–1, portion of total impact
  confidence?: "high" | "medium" | "low";
};

export type ComparisonRow = {
  label: string;
  value: number; // kg CO₂e per garment
  highlight?: boolean;
};

export type LifeStage = {
  year: string;
  title: string;
  detail: string;
};

export type ImpactDashboardProps = {
  summary: string;
  metrics: ImpactMetric[];
  methodologyNote?: string;
  nextActionLabel?: string;
  onNextAction?: () => void;
  comparison?: ComparisonRow[];
  timeline?: LifeStage[];
  assumptions?: { label: string; value: string }[];
  actions?: { title: string; detail: string }[];
};

const nf = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 1 });

const CONFIDENCE: Record<NonNullable<ImpactMetric["confidence"]>, { text: string; className: string }> = {
  high: { text: "High confidence", className: "bg-emerald-50 text-emerald-800 ring-emerald-200" },
  medium: { text: "Estimate", className: "bg-[#e6f2fb] text-[#174e7c] ring-[#b9d9ef]" },
  low: { text: "Rough estimate", className: "bg-amber-50 text-amber-800 ring-amber-200" },
};

const ICONS: Record<string, React.ComponentType<{ className?: string; "aria-hidden"?: boolean }>> = {
  water: Droplets,
  carbon: Leaf,
  waste: Recycle,
};

const SEGMENT_COLOURS = ["bg-[#7fb8e0]", "bg-[#1d5c8c]", "bg-[#0b2a44]", "bg-[#c9e2f3]"];

const DEFAULT_COMPARISON: ComparisonRow[] = [
  { label: "Buying a new cotton tee", value: 6.5 },
  { label: "Keeping it one extra year", value: 1.8, highlight: true },
  { label: "Recycling into fibre", value: 2.4 },
];

const DEFAULT_TIMELINE: LifeStage[] = [
  { year: "Now", title: "Still wearable", detail: "The fabric is intact. A repaired seam or button can extend its life." },
  { year: "Year 1", title: "Keep it in use", detail: "Each extra year of wear spreads its production impact across more uses." },
  { year: "Year 2+", title: "Pass it on", detail: "Resell, swap or donate once it no longer fits your routine." },
];

const DEFAULT_ASSUMPTIONS = [
  { label: "Average garment mass", value: "180 g cotton" },
  { label: "Water per cotton tee", value: "About 2,700 L" },
  { label: "Data source", value: "Average industry figures" },
];

const DEFAULT_ACTIONS = [
  { title: "Repair first", detail: "Fix a loose seam or missing button before deciding to discard." },
  { title: "Resell or swap", detail: "Check local resale or swap groups for items you no longer wear." },
  { title: "Donate responsibly", detail: "Choose a partner that accepts wearable garments." },
];

export function ImpactDashboard({
  summary,
  metrics,
  methodologyNote,
  nextActionLabel = "See what to do with this garment",
  onNextAction,
  comparison = DEFAULT_COMPARISON,
  timeline = DEFAULT_TIMELINE,
  assumptions = DEFAULT_ASSUMPTIONS,
  actions = DEFAULT_ACTIONS,
}: ImpactDashboardProps) {
  const shared = metrics.filter((m) => typeof m.share === "number");
  const maxCompare = Math.max(...comparison.map((c) => c.value), 1);
  const headline = splitHeadline(summary);
  const heroStats = metrics.slice(0, 3);

  return (
    <div className="mx-auto max-w-6xl space-y-10 px-5 py-10 text-slate-900">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-[32px] bg-gradient-to-br from-[#0b2a44] via-[#1d5c8c] to-[#2f7ab0] p-8 text-white shadow-xl md:p-12">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.07] [background-image:linear-gradient(#fff_1px,transparent_1px),linear-gradient(90deg,#fff_1px,transparent_1px)] [background-size:28px_28px]"
          aria-hidden
        />
        <div className="relative grid gap-10 lg:grid-cols-[1.25fr_1fr] lg:items-end">
          <div>
            <p className="flex items-center gap-3 text-xs font-bold uppercase tracking-[0.22em] text-[#bdd9ee]">
              <span className="h-px w-10 bg-[#bdd9ee]" aria-hidden />
              Your impact
            </p>
            <h1 className="mt-5 text-4xl font-extrabold leading-[1.05] tracking-tight md:text-5xl">
              {headline.lead} <em className="not-italic text-[#b6d9f0]">{headline.accent}</em>
            </h1>
            {onNextAction && (
              <button
                type="button"
                onClick={onNextAction}
                className="mt-8 inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-bold text-[#0b2a44] transition-colors hover:bg-[#e6f2fb] focus-visible:outline focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                {nextActionLabel}
                <ArrowRight className="h-4 w-4" aria-hidden />
              </button>
            )}
          </div>

          <ul className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            {heroStats.map((m) => {
              const Icon = ICONS[m.id] ?? Info;
              return (
                <li
                  key={m.id}
                  className="flex items-center gap-4 rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-md"
                >
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/15">
                    <Icon className="h-5 w-5" aria-hidden />
                  </span>
                  <div className="min-w-0">
                    <p className="text-2xl font-extrabold tracking-tight">
                      {nf.format(m.value)}
                      <span className="ml-1 text-sm font-semibold text-[#cfe0ee]">{m.unit}</span>
                    </p>
                    <p className="truncate text-xs text-[#cfe0ee]">{m.label}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      </section>

      {/* Metric cards */}
      <section aria-labelledby="impact-metrics" className="space-y-4">
        <h2 id="impact-metrics" className="sr-only">
          Impact figures
        </h2>
        <ul className="grid gap-5 md:grid-cols-3">
          {metrics.map((m) => {
            const Icon = ICONS[m.id] ?? Info;
            const conf = m.confidence ? CONFIDENCE[m.confidence] : null;
            return (
              <li
                key={m.id}
                className="flex flex-col rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#e6f2fb] text-[#1d5c8c]">
                    <Icon className="h-5 w-5" aria-hidden />
                  </span>
                  {conf && (
                    <span className={`rounded-full px-3 py-1 text-[11px] font-bold ring-1 ring-inset ${conf.className}`}>
                      {conf.text}
                    </span>
                  )}
                </div>
                <p className="mt-6 text-sm font-semibold text-slate-500">{m.label}</p>
                <p className="mt-1 text-4xl font-extrabold tracking-tight">
                  {nf.format(m.value)}
                  <span className="ml-1.5 text-base font-semibold text-slate-500">{m.unit}</span>
                </p>
                {m.equivalent && (
                  <p className="mt-4 border-t border-slate-100 pt-4 text-sm text-slate-600">{m.equivalent}</p>
                )}
              </li>
            );
          })}
        </ul>
      </section>

      {/* Breakdown and comparison */}
      <section className="grid gap-6 lg:grid-cols-2">
        {shared.length > 0 && (
          <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
            <h2 className="text-xl font-extrabold tracking-tight">Where the impact comes from</h2>
            <p className="mt-1 text-sm text-slate-500">Share of this garment's total estimated impact.</p>

            <div
              className="mt-6 flex h-4 gap-1 overflow-hidden rounded-full"
              role="img"
              aria-label={shared.map((m) => `${m.label} ${Math.round((m.share ?? 0) * 100)}%`).join(", ")}
            >
              {shared.map((m, i) => (
                <span
                  key={m.id}
                  className={`${SEGMENT_COLOURS[i % SEGMENT_COLOURS.length]} rounded-full`}
                  style={{ flexGrow: m.share, flexBasis: 0 }}
                />
              ))}
            </div>

            <ul className="mt-6 space-y-3">
              {shared.map((m, i) => (
                <li key={m.id} className="flex items-center justify-between gap-4 text-sm">
                  <span className="flex items-center gap-2.5 text-slate-700">
                    <span className={`h-3 w-3 rounded-full ${SEGMENT_COLOURS[i % SEGMENT_COLOURS.length]}`} aria-hidden />
                    {m.label}
                  </span>
                  <span className="font-bold">{Math.round((m.share ?? 0) * 100)}%</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
          <h2 className="text-xl font-extrabold tracking-tight">Compared to other choices</h2>
          <p className="mt-1 text-sm text-slate-500">Estimated carbon per garment, in kg CO₂e.</p>

          <ul className="mt-6 space-y-5">
            {comparison.map((row) => (
              <li key={row.label}>
                <div className="mb-2 flex items-center justify-between gap-3 text-sm">
                  <span className={row.highlight ? "font-bold text-[#0b2a44]" : "text-slate-700"}>{row.label}</span>
                  <span className="font-bold">{nf.format(row.value)} kg</span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      row.highlight ? "bg-[#1d5c8c]" : "bg-slate-300"
                    }`}
                    style={{ width: `${(row.value / maxCompare) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Timeline */}
      <section className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm md:p-9">
        <h2 className="flex items-center gap-2 text-xl font-extrabold tracking-tight">
          <Clock className="h-5 w-5 text-[#1d5c8c]" aria-hidden />
          What happens next
        </h2>
        <ol className="mt-8 grid gap-8 md:grid-cols-3">
          {timeline.map((s, i) => (
            <li key={s.year + s.title} className="relative">
              {i < timeline.length - 1 && (
                <span
                  className="absolute left-5 top-5 hidden h-px w-[calc(100%-2.5rem)] bg-[#b9d9ef] md:block"
                  aria-hidden
                />
              )}
              <span className="relative flex h-10 w-10 items-center justify-center rounded-full bg-[#0b2a44] text-sm font-extrabold text-white">
                {i + 1}
              </span>
              <p className="mt-4 text-xs font-bold uppercase tracking-wider text-[#1d5c8c]">{s.year}</p>
              <p className="mt-1 text-lg font-bold">{s.title}</p>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{s.detail}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Actions */}
      <section aria-labelledby="impact-actions" className="space-y-4">
        <h2 id="impact-actions" className="text-xl font-extrabold tracking-tight">
          Ways to keep it in use
        </h2>
        <ul className="grid gap-4 md:grid-cols-3">
          {actions.map((a) => (
            <li
              key={a.title}
              className="group rounded-3xl border border-slate-200 bg-white p-6 transition-all hover:-translate-y-0.5 hover:border-[#9fc6e4] hover:shadow-md"
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#e6f2fb] text-[#1d5c8c]">
                <CheckCircle2 className="h-4.5 w-4.5" aria-hidden />
              </span>
              <p className="mt-4 font-bold">{a.title}</p>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{a.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Methodology */}
      <section className="rounded-3xl border border-slate-200 bg-white">
        <details className="group">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4 rounded-3xl px-7 py-5 font-bold marker:hidden">
            <span className="flex items-center gap-3">
              <Repeat className="h-4 w-4 text-[#1d5c8c]" aria-hidden />
              How these numbers were calculated
            </span>
            <ChevronDown className="h-4 w-4 text-slate-500 transition-transform group-open:rotate-180" aria-hidden />
          </summary>
          <div className="space-y-5 border-t border-slate-100 px-7 pb-7 pt-5">
            <dl className="grid gap-3 sm:grid-cols-3">
              {assumptions.map((a) => (
                <div key={a.label} className="rounded-2xl bg-[#f5f8fb] p-4">
                  <dt className="text-xs font-semibold text-slate-500">{a.label}</dt>
                  <dd className="mt-1 text-sm font-bold">{a.value}</dd>
                </div>
              ))}
            </dl>
            {methodologyNote && (
              <p className="flex gap-3 text-sm leading-relaxed text-slate-600">
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-[#1d5c8c]" aria-hidden />
                {methodologyNote}
              </p>
            )}
          </div>
        </details>
      </section>
    </div>
  );
}

function splitHeadline(text: string) {
  const words = text.trim().split(/\s+/);
  const accentCount = Math.min(3, Math.max(1, words.length - 1));
  return {
    lead: words.slice(0, words.length - accentCount).join(" "),
    accent: words.slice(words.length - accentCount).join(" "),
  };
}

export default ImpactDashboard;