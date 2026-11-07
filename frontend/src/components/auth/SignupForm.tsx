"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertCircle, Loader2, Lock, Mail, MapPin, User as UserIcon } from "lucide-react";
import { registerUser } from "@/lib/auth";
import { useAuth } from "@/lib/useAuth";
import { PasswordField, TextField, primaryBtn } from "./fields";

const STRENGTH_COLOR = ["bg-[#E5E9EE]", "bg-[#E2776B]", "bg-[#E3B341]", "bg-[#4FB0DE]", "bg-[#2B98D0]"];
const STRENGTH_LABELS = ["Very weak", "Weak", "Fair", "Good", "Strong"];

// Local helpers, so this form doesn't depend on exports from auth.ts
function checkEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function scorePassword(password: string): number {
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  return score;
}

export function SignupForm() {
  const router = useRouter();
  const { isLoggedIn } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [city, setCity] = useState("Pune");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<{ name?: string; email?: string; password?: string; confirm?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const score = scorePassword(password);

  useEffect(() => {
    if (isLoggedIn) router.replace("/profile?welcome=1");
  }, [isLoggedIn, router]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const next = {
      name: name.trim().length >= 2 ? undefined : "Please enter your name.",
      email: checkEmail(email) ? undefined : "Enter a valid email address.",
      password: password.length >= 8 ? undefined : "Use at least 8 characters.",
      confirm: confirm === password ? undefined : "Passwords don’t match.",
    };
    setErrors(next);
    setFormError(null);
    if (Object.values(next).some(Boolean)) return;

    setLoading(true);
    try {
      await registerUser({ full_name: name.trim(), email, password, city });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong. Please try again.";
      if (msg.toLowerCase().includes("already")) setErrors({ email: msg });
      else setFormError(msg);
      setLoading(false);
    }
  };

  if (isLoggedIn) {
    return <p className="text-center text-[15px] text-[#5B6B7F]">Account ready. Taking you to your profile…</p>;
  }

  return (
    <div>
      <h1 className="text-[28px] font-extrabold leading-tight tracking-tight text-[#12233B]">Create your account</h1>
      <p className="mt-1.5 text-[15px] leading-relaxed text-[#5B6B7F]">
        Join RE-THREAD and start giving your clothes a second life.
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
          label="Full name"
          autoComplete="name"
          placeholder="Your name"
          icon={<UserIcon className="h-4 w-4" aria-hidden />}
          value={name}
          onChange={setName}
          error={errors.name}
        />
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          inputMode="email"
          placeholder="you@example.com"
          icon={<Mail className="h-4 w-4" aria-hidden />}
          value={email}
          onChange={setEmail}
          error={errors.email}
        />
        <TextField
          label="City"
          autoComplete="address-level2"
          placeholder="e.g. Pune"
          icon={<MapPin className="h-4 w-4" aria-hidden />}
          value={city}
          onChange={setCity}
        />

        <div>
          <PasswordField
            label="Password"
            autoComplete="new-password"
            placeholder="At least 8 characters"
            icon={<Lock className="h-4 w-4" aria-hidden />}
            value={password}
            onChange={setPassword}
            error={errors.password}
          />
          {password && (
            <div className="mt-2" aria-live="polite">
              <div className="flex gap-1.5" aria-hidden>
                {[1, 2, 3, 4].map((n) => (
                  <span
                    key={n}
                    className={`h-1.5 flex-1 rounded-full transition-colors ${
                      score >= n ? STRENGTH_COLOR[score] : "bg-[#E5E9EE]"
                    }`}
                  />
                ))}
              </div>
              <p className="mt-1 text-[13px] text-[#7A8896]">
                Password strength: <span className="font-semibold text-[#12233B]">{STRENGTH_LABELS[score]}</span>
              </p>
            </div>
          )}
        </div>

        <PasswordField
          label="Confirm password"
          autoComplete="new-password"
          placeholder="Repeat your password"
          icon={<Lock className="h-4 w-4" aria-hidden />}
          value={confirm}
          onChange={setConfirm}
          error={errors.confirm}
        />

        <button type="submit" disabled={loading} className={primaryBtn}>
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
              Creating account…
            </>
          ) : (
            "Create account"
          )}
        </button>
      </form>

      <p className="mt-5 text-center text-sm text-[#5B6B7F]">
        Already have an account?{" "}
        <Link href="/login" className="font-semibold text-[#2B7FB8] hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}

export default SignupForm;