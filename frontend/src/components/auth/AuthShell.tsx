import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowLeft, Check, Leaf } from "lucide-react";

const GRADIENT = "linear-gradient(135deg,#2e4863 0%,#2b76a0 38%,#3ba6da 100%)";
const GRID = {
  backgroundImage:
    "linear-gradient(rgba(255,255,255,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.07) 1px,transparent 1px)",
  backgroundSize: "28px 28px",
  WebkitMaskImage: "linear-gradient(180deg,#000,transparent 85%)",
  maskImage: "linear-gradient(180deg,#000,transparent 85%)",
} as const;

const POINTS = [
  "Identify fabrics from a single photo",
  "Get reuse and upcycling ideas that fit",
  "Find reuse and recycling hubs in Pune",
];

function Logo() {
  return (
    <Link href="/" aria-label="RE-THREAD home" className="inline-flex items-center gap-3">
      <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/25 bg-white/15 text-white backdrop-blur">
        <Leaf className="h-[18px] w-[18px]" aria-hidden />
      </span>
      <span className="text-[13px] font-extrabold uppercase tracking-[0.18em] text-white">Re-Thread</span>
    </Link>
  );
}

export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#F9F8F4] text-[#12233B] lg:grid lg:grid-cols-2">
      {/* Brand panel */}
      <aside
        className="relative overflow-hidden px-6 py-6 text-white lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col lg:justify-between lg:p-12 xl:p-14"
        style={{ background: GRADIENT }}
      >
        <div className="pointer-events-none absolute inset-0" style={GRID} aria-hidden />
        <div
          className="pointer-events-none absolute -right-24 -top-24 h-[26rem] w-[26rem] rounded-full bg-white/20 blur-3xl"
          aria-hidden
        />

        <div className="relative flex items-center justify-between">
          <Logo />
          <Link
            href="/"
            className="inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-white/85 hover:text-white lg:hidden"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden />
            Back
          </Link>
        </div>

        <div className="relative hidden max-w-lg lg:block">
          <p className="text-[12px] font-medium uppercase tracking-[0.2em] text-white/85">Circular fashion · Pune</p>
          <h2 className="mt-4 text-5xl font-extrabold leading-[1.05] tracking-tight xl:text-[3.4rem]">
            Your clothes. Your stories. Their next chapter.
          </h2>
          <p className="mt-5 max-w-md text-base leading-relaxed text-white/90">
            Find out what your fabric is made of, see how worn it is, and discover thoughtful ways to keep it in use
            and out of landfill.
          </p>

          <ul className="mt-6 space-y-3">
            {POINTS.map((p) => (
              <li key={p} className="flex items-center gap-3 text-[15px] text-white/95">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/20">
                  <Check className="h-3.5 w-3.5" aria-hidden />
                </span>
                {p}
              </li>
            ))}
          </ul>

          {/* Decorative example, not real data */}
          <div
            className="mt-10 max-w-xs rounded-2xl border border-white/25 bg-white/10 p-4 backdrop-blur"
            aria-hidden
          >
            <div className="flex justify-between text-xs text-white/75">
              <span>Example result</span>
              <span>Model confidence</span>
            </div>
            <p className="mt-2 text-lg font-bold">Denim</p>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/25">
              <div className="h-full w-[94%] rounded-full bg-white" />
            </div>
          </div>
        </div>

        <p className="relative hidden text-[13px] text-white/80 lg:block">
          A college project exploring AI for the circular fashion economy.
        </p>
      </aside>

      {/* Form area */}
      <main className="flex min-h-[calc(100vh-4.5rem)] flex-col px-5 py-8 sm:px-10 lg:min-h-screen lg:py-10">
        <div className="hidden justify-end lg:flex">
          <Link
            href="/"
            className="inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-[#5B6B7F] hover:text-[#2B7FB8]"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden />
            Back to RE-THREAD
          </Link>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-[420px] rounded-[28px] border border-[#EFEDE6] bg-white p-7 shadow-[0_24px_60px_-28px_rgba(31,95,139,0.35)] sm:p-9">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}