"use client";

import React, { useState } from "react";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { Check, Eye, EyeOff, Leaf } from "lucide-react";

const POINTS = [
  "Identify fabrics from a single photo",
  "Get reuse and upcycling ideas that fit",
  "Find reuse and recycling hubs in Pune",
];

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen bg-ivory lg:grid-cols-2">
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-evergreen via-[#17508A] to-[#2B8AD0] p-12 text-white lg:flex">
        <div
          className="pointer-events-none absolute -right-24 top-1/4 h-96 w-96 rounded-full bg-white/10 blur-3xl"
          aria-hidden
        />

        <Link href="/" className="relative flex w-fit items-center gap-2.5 text-sm font-semibold tracking-[0.2em]">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/15">
            <Leaf className="h-4 w-4" aria-hidden />
          </span>
          RE-THREAD
        </Link>

        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-white/70">
            Circular fashion · Pune
          </p>
          <h2 className="mt-5 text-5xl font-bold leading-[1.05]">
            Your clothes. Your stories. Their next chapter.
          </h2>
          <p className="mt-5 max-w-md text-base leading-relaxed text-white/80">
            Find out what your fabric is made of, see how worn it is, and discover thoughtful ways to
            keep it in use and out of landfill.
          </p>

          <ul className="mt-8 space-y-3">
            {POINTS.map((p) => (
              <li key={p} className="flex items-center gap-3 text-sm text-white/90">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/20">
                  <Check className="h-3 w-3" aria-hidden />
                </span>
                {p}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative">
          <div className="max-w-xs rounded-xl bg-white/10 p-4 backdrop-blur">
            <div className="flex justify-between text-[11px] uppercase tracking-wider text-white/70">
              <span>Example result</span>
              <span>Model confidence</span>
            </div>
            <p className="mt-2 text-lg font-semibold">Denim</p>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/20" aria-hidden>
              <div className="h-full w-4/5 rounded-full bg-white" />
            </div>
          </div>
          <p className="mt-6 text-xs text-white/60">
            A college project exploring AI for the circular economy.
          </p>
        </div>
      </aside>

      <main className="flex flex-col items-center justify-center p-5 sm:p-10">
        <Link href="/" className="mb-8 flex items-center gap-2 text-sm font-semibold lg:hidden">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest text-white">
            <Leaf className="h-4 w-4" aria-hidden />
          </span>
          Re-Thread
        </Link>
        {children}
      </main>
    </div>
  );
}

type FieldProps = {
  id: string;
  label: string;
  Icon: LucideIcon;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  autoComplete?: string;
  password?: boolean;
  error?: string;
};

export function AuthField({
  id,
  label,
  Icon,
  value,
  onChange,
  placeholder,
  type = "text",
  autoComplete,
  password = false,
  error,
}: FieldProps) {
  const [show, setShow] = useState(false);

  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-charcoal">
        {label}
      </label>
      <div className="relative">
        <Icon
          className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
          aria-hidden
        />
        <input
          id={id}
          type={password ? (show ? "text" : "password") : type}
          autoComplete={autoComplete}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
          className={`block min-h-12 w-full rounded-lg border bg-mist/50 pl-10 text-base text-charcoal placeholder:text-muted/70 focus:border-forest focus:bg-white focus:outline-none focus:ring-2 focus:ring-forest/20 ${
            password ? "pr-12" : "pr-4"
          } ${error ? "border-terracotta" : "border-line"}`}
        />
        {password && (
          <button
            type="button"
            onClick={() => setShow((s) => !s)}
            aria-label={show ? "Hide password" : "Show password"}
            aria-pressed={show}
            className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-muted hover:text-forest"
          >
            {show ? <EyeOff className="h-4 w-4" aria-hidden /> : <Eye className="h-4 w-4" aria-hidden />}
          </button>
        )}
      </div>
      {error && (
        <p id={`${id}-error`} className="mt-1.5 text-sm text-[#7A3A22]">
          {error}
        </p>
      )}
    </div>
  );
}