"use client";

import { useId, useState } from "react";
import type { InputHTMLAttributes, ReactNode } from "react";
import { Eye, EyeOff } from "lucide-react";

export const primaryBtn =
  "inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-[linear-gradient(90deg,#2B98D0,#3CA7DB)] px-6 text-[15px] font-semibold text-white shadow-[0_12px_24px_-12px_rgba(43,152,208,0.9)] transition hover:brightness-95 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#2B98D0] disabled:cursor-not-allowed disabled:opacity-60";

export const secondaryBtn =
  "inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-[#CFE3F1] bg-white px-5 text-[15px] font-semibold text-[#2B7FB8] transition hover:bg-[#EAF4FB] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#2B98D0] disabled:opacity-60";

type FieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value" | "className"> & {
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  hint?: string;
  icon?: ReactNode;
  optional?: boolean;
  trailing?: ReactNode;
};

export function TextField({
  label,
  value,
  onChange,
  error,
  hint,
  icon,
  optional,
  trailing,
  ...rest
}: FieldProps) {
  const id = useId();
  const msgId = `${id}-msg`;
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 flex items-baseline justify-between text-[13px] font-semibold text-[#2B7FB8]">
        <span>{label}</span>
        {optional && <span className="text-xs font-normal text-[#7A8896]">Optional</span>}
      </label>
      <div className="relative">
        {icon && (
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8795A3]">{icon}</span>
        )}
        <input
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-invalid={error ? true : undefined}
          aria-describedby={error || hint ? msgId : undefined}
          className={`h-11 w-full rounded-xl border bg-[#FBFAF8] text-[15px] text-[#12233B] placeholder:text-[#9AA6B2] transition focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#2B98D0]/15 ${
            icon ? "pl-10" : "pl-3.5"
          } ${trailing ? "pr-11" : "pr-3.5"} ${
            error
              ? "border-[#D9594C] focus:border-[#D9594C]"
              : "border-[#E9E6DE] hover:border-[#C9DCEA] focus:border-[#2B98D0]"
          }`}
          {...rest}
        />
        {trailing && <span className="absolute right-1 top-1/2 -translate-y-1/2">{trailing}</span>}
      </div>
      {(error || hint) && (
        <p
          id={msgId}
          role={error ? "alert" : undefined}
          className={`mt-1.5 text-[13px] ${error ? "text-[#C0463A]" : "text-[#7A8896]"}`}
        >
          {error ?? hint}
        </p>
      )}
    </div>
  );
}

export function PasswordField(props: Omit<FieldProps, "type" | "trailing">) {
  const [show, setShow] = useState(false);
  const Icon = show ? EyeOff : Eye;
  return (
    <TextField
      {...props}
      type={show ? "text" : "password"}
      trailing={
        <button
          type="button"
          onClick={() => setShow((v) => !v)}
          aria-label={show ? "Hide password" : "Show password"}
          aria-pressed={show}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-[#8795A3] hover:bg-[#EAF4FB] hover:text-[#2B7FB8] focus-visible:outline-2 focus-visible:outline-[#2B98D0]"
        >
          <Icon className="h-[18px] w-[18px]" aria-hidden />
        </button>
      }
    />
  );
}