"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { LogOut, User as UserIcon } from "lucide-react";
import { useAuth } from "@/lib/useAuth";
import { logoutUser } from "@/lib/auth";

const initials = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("") || "?";

/**
 * Drop-in for the navbar's "Log in / Sign up" area.
 * Signed out: "Log in" link + "Sign up" pill. Signed in: avatar with a small menu.
 */
export default function AuthMenu({ variant = "desktop" }: { variant?: "desktop" | "mobile" }) {
  const { user, ready } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointer = (e: PointerEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!ready) return null;

  if (!user) {
    return variant === "mobile" ? (
      <div className="flex gap-3">
        <Link href="/login" className="flex-1 rounded-full border border-[#CFE3F1] py-2.5 text-center text-sm font-semibold text-[#12233B]">
          Log in
        </Link>
        <Link href="/signup" className="flex-1 rounded-full bg-[#2F7BB5] py-2.5 text-center text-sm font-semibold text-white">
          Sign up
        </Link>
      </div>
    ) : (
      <div className="flex items-center gap-3">
        <Link href="/login" className="text-sm font-semibold text-[#12233B] hover:text-[#2F7BB5]">
          Log in
        </Link>
        <Link
          href="/signup"
          className="inline-flex h-9 items-center rounded-full border border-[#2F7BB5] px-4 text-sm font-semibold text-[#2F7BB5] transition-colors hover:bg-[#2F7BB5] hover:text-white"
        >
          Sign up
        </Link>
      </div>
    );
  }

  if (variant === "mobile") {
    return (
      <div className="flex gap-3">
        <Link href="/profile" className="flex-1 rounded-full border border-[#CFE3F1] py-2.5 text-center text-sm font-semibold text-[#12233B]">
          Profile
        </Link>
        <button
          type="button"
          onClick={logoutUser}
          className="flex-1 rounded-full bg-[#2F7BB5] py-2.5 text-center text-sm font-semibold text-white"
        >
          Log out
        </button>
      </div>
    );
  }

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Account menu for ${user.name || user.full_name}`}
        className="flex h-9 w-9 items-center justify-center rounded-full bg-[linear-gradient(135deg,#2B98D0,#2F7BB5)] text-sm font-bold text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#2B98D0]"
      >
        {initials(user.name || user.full_name)}
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-2 w-60 rounded-2xl border border-[#E9EEF3] bg-white p-2 shadow-[0_20px_40px_-20px_rgba(31,95,139,0.4)]"
        >
          <div className="px-3 py-2">
            <p className="truncate text-sm font-semibold text-[#12233B]">{user.name || user.full_name}</p>
            <p className="truncate text-xs text-[#7A8896]">{user.email}</p>
          </div>
          <Link
            role="menuitem"
            href="/profile"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm text-[#12233B] hover:bg-[#EAF4FB]"
          >
            <UserIcon className="h-4 w-4 text-[#2B7FB8]" aria-hidden /> Your profile
          </Link>
          <button
            role="menuitem"
            type="button"
            onClick={() => {
              setOpen(false);
              logoutUser();
            }}
            className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-sm text-[#12233B] hover:bg-[#EAF4FB]"
          >
            <LogOut className="h-4 w-4 text-[#2B7FB8]" aria-hidden /> Log out
          </button>
        </div>
      )}
    </div>
  );
}