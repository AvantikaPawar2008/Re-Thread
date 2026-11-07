"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Leaf, Menu, X } from "lucide-react";
import { useAuth } from "@/lib/useAuth";

export type Tab = "scan" | "dashboard" | "facilities" | "partner" | "guide";

interface NavbarProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

const TABS: { key: Tab; label: string }[] = [
  { key: "scan", label: "Analyze" },
  { key: "dashboard", label: "Impact" },
  { key: "facilities", label: "Drop-off Hubs" },
  { key: "partner", label: "Partner Scan" },
  { key: "guide", label: "Fabric Guide" },
];

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange }) => {
  const [open, setOpen] = useState(false);
  const { user, isLoggedIn } = useAuth();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const go = (tab: Tab) => {
    setOpen(false);
    onTabChange(tab);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const analyze = () => {
    setOpen(false);
    onTabChange("scan");
    window.setTimeout(
      () => document.getElementById("analyze")?.scrollIntoView({ behavior: "smooth" }),
      60
    );
  };

  const fullName = user?.full_name?.trim() ?? "";
  const initial = (fullName.charAt(0) || user?.email?.charAt(0) || "?").toUpperCase();
  const firstName = fullName.split(/\s+/)[0] ?? "";

  const accountArea =
    isLoggedIn && user ? (
      <Link
        href="/profile"
        aria-label="Open your profile"
        className="flex items-center gap-2 rounded-full py-1 pl-1 pr-3 text-sm font-medium text-charcoal transition-colors hover:bg-mist/70"
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-forest text-sm font-semibold text-white">
          {initial}
        </span>
        <span className="max-w-[90px] truncate">{firstName}</span>
      </Link>
    ) : (
      <>
        <Link href="/login" className="px-3 text-sm font-medium text-charcoal hover:text-forest">
          Log in
        </Link>
        <Link
          href="/signup"
          className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-forest shadow-sm ring-1 ring-line transition-colors hover:bg-mist/60"
        >
          Sign up
        </Link>
      </>
    );

  return (
    <header className="fixed inset-x-0 top-3 z-50 px-3 sm:px-5">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between gap-3 rounded-full bg-white/90 py-2 pl-3 pr-2 shadow-lg ring-1 ring-line backdrop-blur">
        <button
          type="button"
          onClick={() => go("scan")}
          className="flex shrink-0 items-center gap-2"
          aria-label="RE-THREAD home"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-forest text-white">
            <Leaf className="h-4 w-4" aria-hidden />
          </span>
          <span className="text-sm font-bold text-charcoal">Re-Thread</span>
        </button>

        <nav className="hidden items-center gap-1 rounded-full bg-mist/60 p-1 lg:flex" aria-label="Main">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => go(t.key)}
              aria-current={activeTab === t.key ? "page" : undefined}
              className={`whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                activeTab === t.key ? "bg-white text-charcoal shadow-sm" : "text-muted hover:text-charcoal"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className="hidden items-center gap-1 lg:flex">
          {accountArea}
          <button
            type="button"
            onClick={analyze}
            className="ml-1 inline-flex items-center gap-2 rounded-full bg-forest px-5 py-2.5 text-sm font-semibold text-white shadow-md transition-colors hover:bg-evergreen"
          >
            Analyze a Garment
            <ArrowRight className="h-4 w-4" aria-hidden />
          </button>
        </div>

        <button
          type="button"
          className="rounded-full p-2.5 text-charcoal hover:bg-mist/70 lg:hidden"
          onClick={() => setOpen(!open)}
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="mobile-menu"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <div
          id="mobile-menu"
          className="mx-auto mt-2 flex max-w-[1200px] flex-col rounded-3xl bg-white p-3 shadow-lg ring-1 ring-line lg:hidden"
        >
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => go(t.key)}
              aria-current={activeTab === t.key ? "page" : undefined}
              className={`rounded-xl px-4 py-3 text-left text-base ${
                activeTab === t.key ? "bg-mist/70 font-semibold text-forest" : "text-charcoal"
              }`}
            >
              {t.label}
            </button>
          ))}

          <div className="mt-2 flex flex-wrap items-center gap-2 border-t border-line pt-3">
            {accountArea}
            <button
              type="button"
              onClick={analyze}
              className="ml-auto inline-flex items-center gap-2 rounded-full bg-forest px-5 py-2.5 text-sm font-semibold text-white"
            >
              Analyze a Garment
              <ArrowRight className="h-4 w-4" aria-hidden />
            </button>
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;