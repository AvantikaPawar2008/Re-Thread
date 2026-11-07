"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check, Leaf, Loader2, LogOut, MapPin } from "lucide-react";
import { INTERESTS, logoutUser, updateProfile, type User } from "@/lib/auth";
import { useAuth } from "@/lib/useAuth";
import { TextField, primaryBtn, secondaryBtn } from "./fields";

const CARD = "rounded-3xl border border-[#EFEDE6] bg-white shadow-[0_20px_50px_-30px_rgba(31,95,139,0.35)]";

const initials = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("") || "?";

export function ProfileView() {
  const router = useRouter();
  const { user, isLoggedIn } = useAuth();

  useEffect(() => {
    if (!isLoggedIn) router.replace("/login?next=/profile");
  }, [isLoggedIn, router]);

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F9F8F4]">
        <Loader2 className="h-6 w-6 animate-spin text-[#2B98D0]" aria-label="Loading your profile" />
      </div>
    );
  }

  return <ProfileForm key={user.id} user={user} onLogout={() => { logoutUser(); router.push("/"); }} />;
}

function ProfileForm({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [fullName, setFullName] = useState(user.full_name);
  const [city, setCity] = useState(user.city);
  const [bio, setBio] = useState(user.bio);
  const [interests, setInterests] = useState<string[]>(
    user.interests ? user.interests.split(",").map((s) => s.trim()).filter(Boolean) : []
  );
  const [nameError, setNameError] = useState<string>();
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const dirty =
    fullName.trim() !== user.full_name ||
    city.trim() !== user.city ||
    bio !== user.bio ||
    interests.join(",") !== user.interests;

  const toggle = (i: string) =>
    setInterests((cur) => (cur.includes(i) ? cur.filter((x) => x !== i) : [...cur, i]));

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (fullName.trim().length < 2) {
      setNameError("Please enter your name.");
      return;
    }
    setNameError(undefined);
    setFormError(null);
    setSaving(true);
    setSaved(false);
    try {
      await updateProfile({
        full_name: fullName.trim(),
        city: city.trim(),
        bio,
        interests: interests.join(","),
      });
      setSaved(true);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not save your changes.");
    } finally {
      setSaving(false);
    }
  };

  const since = user.created_at
    ? new Date(user.created_at).toLocaleDateString(undefined, { month: "short", year: "numeric" })
    : null;

  return (
    <div className="min-h-screen bg-[#F9F8F4] pb-16 text-[#12233B]">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-5 py-5 sm:px-8">
        <Link href="/" className="inline-flex items-center gap-2.5" aria-label="RE-THREAD home">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#2B98D0] text-white">
            <Leaf className="h-[18px] w-[18px]" aria-hidden />
          </span>
          <span className="text-[15px] font-bold">Re-Thread</span>
        </Link>
        <div className="flex items-center gap-2">
          <Link
            href="/"
            className="inline-flex min-h-11 items-center gap-1.5 rounded-full px-3 text-sm font-medium text-[#5B6B7F] hover:text-[#2B7FB8]"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden />
            Back to app
          </Link>
          <button type="button" onClick={onLogout} className={secondaryBtn}>
            <LogOut className="h-4 w-4" aria-hidden />
            Log out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-5 sm:px-8">
        <section className="rounded-[28px] bg-gradient-to-br from-[#2e4863] via-[#2b76a0] to-[#3ba6da] p-7 text-white sm:p-9">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
            <span
              className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-white text-2xl font-extrabold text-[#2B7FB8] shadow-lg"
              aria-hidden
            >
              {initials(user.full_name)}
            </span>
            <div className="min-w-0">
              <h1 className="truncate text-3xl font-extrabold tracking-tight">{user.full_name}</h1>
              <p className="mt-0.5 truncate text-white/85">{user.email}</p>
              <div className="mt-3 flex flex-wrap gap-2 text-[13px] font-medium">
                {since && <span className="rounded-full bg-white/20 px-3 py-1">Member since {since}</span>}
                {user.city && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-white/20 px-3 py-1">
                    <MapPin className="h-3.5 w-3.5" aria-hidden /> {user.city}
                  </span>
                )}
              </div>
            </div>
          </div>
        </section>

        <form onSubmit={save} noValidate className={`${CARD} space-y-5 p-6 sm:p-8`}>
          <div>
            <h2 className="text-xl font-extrabold tracking-tight">Your details</h2>
            <p className="mt-1 text-sm text-[#5B6B7F]">This is how RE-THREAD knows you.</p>
          </div>

          {formError && (
            <div role="alert" className="rounded-xl border border-[#F2C9C4] bg-[#FDECEA] p-3 text-sm text-[#A93D32]">
              {formError}
            </div>
          )}

          <TextField label="Full name" autoComplete="name" value={fullName} onChange={setFullName} error={nameError} />
          <TextField
            label="Email"
            type="email"
            value={user.email}
            onChange={() => {}}
            readOnly
            hint="Your email is your login, so it can't be changed here."
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
            <label htmlFor="bio" className="mb-1.5 flex justify-between text-[13px] font-semibold text-[#2B7FB8]">
              <span>About you</span>
              <span className="font-normal text-[#7A8896]">{bio.length}/500</span>
            </label>
            <textarea
              id="bio"
              value={bio}
              maxLength={500}
              rows={3}
              onChange={(e) => setBio(e.target.value)}
              placeholder="A line about your style or what you want to do with old clothes"
              className="w-full resize-none rounded-xl border border-[#E9E6DE] bg-[#FBFAF8] px-3.5 py-3 text-[15px] text-[#12233B] placeholder:text-[#9AA6B2] hover:border-[#C9DCEA] focus:border-[#2B98D0] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#2B98D0]/15"
            />
          </div>

          <fieldset>
            <legend className="mb-2 text-[13px] font-semibold text-[#2B7FB8]">What would you like to do more of?</legend>
            <div className="flex flex-wrap gap-2">
              {INTERESTS.map((i) => {
                const on = interests.includes(i);
                return (
                  <button
                    key={i}
                    type="button"
                    onClick={() => toggle(i)}
                    aria-pressed={on}
                    className={`inline-flex min-h-10 items-center gap-1.5 rounded-full border px-4 text-sm font-medium transition-colors ${
                      on
                        ? "border-[#2B98D0] bg-[#EAF4FB] text-[#1F5F8B]"
                        : "border-[#E9E6DE] bg-white text-[#12233B] hover:border-[#C9DCEA]"
                    }`}
                  >
                    {on && <Check className="h-4 w-4" aria-hidden />}
                    {i}
                  </button>
                );
              })}
            </div>
          </fieldset>

          <div className="flex items-center gap-4 pt-1">
            <button type="submit" disabled={!dirty || saving} className={`${primaryBtn} sm:w-auto sm:min-w-44`}>
              {saving ? "Saving…" : "Save changes"}
            </button>
            <p className="text-sm font-medium text-[#2B7FB8]" aria-live="polite">
              {saved && (
                <span className="inline-flex items-center gap-1.5">
                  <Check className="h-4 w-4" aria-hidden /> Saved
                </span>
              )}
            </p>
          </div>
        </form>
      </main>
    </div>
  );
}

export default ProfileView;