"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertCircle, Loader2, Lock, Mail } from "lucide-react";
import { loginUser, validateEmail } from "@/lib/auth";
import { useAuth } from "@/lib/useAuth";
import { PasswordField, TextField, primaryBtn } from "./fields";

/** Where to go after logging in: ?next=/somewhere (same-site paths only) */
function destination(): string {
  const next = new URLSearchParams(window.location.search).get("next");
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/";
}

export function LoginForm() {
  const router = useRouter();
  const { ready, signedIn } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [emailError, setEmailError] = useState<string>();
  const [passwordError, setPasswordError] = useState<string>();
  const [formError, setFormError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (ready && signedIn) router.replace(destination());
  }, [ready, signedIn, router]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const eErr = validateEmail(email) ? undefined : "Enter a valid email address.";
    const pErr = password ? undefined : "Enter your password.";
    setEmailError(eErr);
    setPasswordError(pErr);
    setFormError(null);
    if (eErr || pErr) return;

    setLoading(true);
    try {
      await loginUser(email, password, remember);
      // The effect above redirects once the session is saved
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      setLoading(false);
    }
  };

  if (ready && signedIn) {
    return <p className="text-center text-[15px] text-[#5B6B7F]">You’re logged in. Taking you back…</p>;
  }

  return (
    <div>
      <h1 className="text-[28px] font-extrabold leading-tight tracking-tight text-[#12233B]">Welcome back</h1>
      <p className="mt-1.5 text-[15px] leading-relaxed text-[#5B6B7F]">
        Log in to keep identifying fabrics and finding ideas for what you own.
      </p>

      <form onSubmit={onSubmit} noValidate className="mt-7 space-y-4">
        {formError && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-xl border border-[#F2C9C4] bg-[#FDECEA] p-3 text-sm text-[#A93D32]"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            {formError}
          </div>
        )}

        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          inputMode="email"
          placeholder="you@example.com"
          icon={<Mail className="h-4 w-4" aria-hidden />}
          value={email}
          onChange={setEmail}
          error={emailError}
        />

        <PasswordField
          label="Password"
          autoComplete="current-password"
          placeholder="Your password"
          icon={<Lock className="h-4 w-4" aria-hidden />}
          value={password}
          onChange={setPassword}
          error={passwordError}
        />

        <label className="flex min-h-10 cursor-pointer items-center gap-2.5 text-sm text-[#5B6B7F]">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            className="h-4 w-4 rounded border-[#CFE3F1] accent-[#2B98D0]"
          />
          Keep me logged in on this device
        </label>

        <button type="submit" disabled={loading} className={primaryBtn}>
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
              Logging in…
            </>
          ) : (
            "Log in"
          )}
        </button>
      </form>

      <p className="mt-5 text-center text-sm text-[#5B6B7F]">
        New to RE-THREAD?{" "}
        <Link href="/signup" className="font-semibold text-[#2B7FB8] hover:underline">
          Create an account
        </Link>
      </p>

      <p className="mt-5 rounded-xl bg-[#EAF4FB] p-3 text-[13px] leading-relaxed text-[#4F6B80]">
        <span className="font-semibold text-[#2B7FB8]">Demo mode. </span>
        Accounts are stored in this browser only, not on a server. Please don’t reuse a real password.
      </p>
    </div>
  );
}