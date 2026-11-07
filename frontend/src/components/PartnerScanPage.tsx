"use client";

import { useState } from "react";
import "./partner-scan.css";

export type PartnerResult = {
  code: string;
  name: string;
  type: string;
  area: string;
  verified: boolean;
  accepts: string[];
  pickup: boolean;
  benefit?: string;
};

export type PartnerScanPageProps = {
  onLookup?: (code: string) => Promise<PartnerResult | null>;
};

// Sample data only. Replace by passing `onLookup` that calls your backend.
const SAMPLE_PARTNERS: PartnerResult[] = [
  {
    code: "RT-DEMO-01",
    name: "Sample Partner Store",
    type: "Retail drop-off",
    area: "Pune",
    verified: true,
    accepts: ["Clothing", "Shoes", "Bags"],
    pickup: false,
    benefit: "Sample store credit on eligible garments",
  },
  {
    code: "RT-DEMO-02",
    name: "Sample Community Partner",
    type: "NGO collection",
    area: "Pune",
    verified: false,
    accepts: ["Wearable clothing", "Blankets"],
    pickup: true,
  },
];

const STEPS = ["Enter code", "Verify partner", "Review benefits"];

type Status = "idle" | "loading" | "found" | "missing" | "error";

export function PartnerScanPage({ onLookup }: PartnerScanPageProps) {
  const [code, setCode] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<PartnerResult | null>(null);

  const activeStep = status === "idle" ? 0 : status === "loading" ? 1 : 2;

  const runLookup = async (value: string) => {
    const clean = value.trim().toUpperCase();
    if (!clean) return;
    setCode(clean);
    setStatus("loading");
    setResult(null);
    try {
      const found = onLookup
        ? await onLookup(clean)
        : SAMPLE_PARTNERS.find((p) => p.code === clean) ?? null;
      if (found) {
        setResult(found);
        setStatus("found");
      } else {
        setStatus("missing");
      }
    } catch {
      setStatus("error");
    }
  };

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    runLookup(code);
  };

  const reset = () => {
    setCode("");
    setResult(null);
    setStatus("idle");
  };

  return (
    <section className="ps" aria-labelledby="ps-title">
      <header className="ps-header">
        <p className="ps-eyebrow">
          <span className="ps-eyebrowRule" aria-hidden="true" />
          Partner scan
        </p>
        <h2 id="ps-title" className="ps-title">
          Verify a <em>drop-off partner</em>
        </h2>
        <p className="ps-lead">
          Enter the code printed at a partner location to confirm it is verified and see what it accepts before
          you go.
        </p>
      </header>

      <ol className="ps-steps" aria-label="Progress">
        {STEPS.map((label, i) => {
          const state = i < activeStep ? "done" : i === activeStep ? "current" : "todo";
          return (
            <li key={label} className={`ps-step ps-step--${state}`} aria-current={state === "current" ? "step" : undefined}>
              <span className="ps-stepNum">{i < activeStep ? "✓" : i + 1}</span>
              <span className="ps-stepLabel">{label}</span>
            </li>
          );
        })}
      </ol>

      <div className="ps-layout">
        <form className="ps-card ps-form" onSubmit={onSubmit}>
          <label htmlFor="ps-code" className="ps-fieldLabel">
            Partner code
          </label>
          <div className="ps-inputRow">
            <input
              id="ps-code"
              className="ps-input"
              type="text"
              autoComplete="off"
              autoCapitalize="characters"
              placeholder="e.g. RT-DEMO-01"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            <button type="submit" className="ps-btnPrimary" disabled={!code.trim() || status === "loading"}>
              {status === "loading" ? "Checking…" : "Verify"}
            </button>
          </div>
          <p className="ps-hint">
            Found on the sticker at the partner location.{" "}
            <button type="button" className="ps-linkBtn" onClick={() => runLookup(SAMPLE_PARTNERS[0].code)}>
              Try a sample code
            </button>
          </p>
        </form>

        <div className="ps-result" aria-live="polite">
          {status === "idle" && (
            <div className="ps-placeholder">
              <p className="ps-placeholderTitle">Waiting for a code</p>
              <p className="ps-placeholderText">Results will appear here once a partner is verified.</p>
            </div>
          )}

          {status === "loading" && (
            <div className="ps-placeholder">
              <span className="ps-spinner" aria-hidden="true" />
              <p className="ps-placeholderText">Checking partner records…</p>
            </div>
          )}

          {status === "missing" && (
            <div className="ps-alert ps-alert--warn">
              <p className="ps-alertTitle">We couldn't find that code</p>
              <p className="ps-alertText">Check the sticker for typos, or ask the partner to confirm their code.</p>
              <button type="button" className="ps-btnGhost" onClick={reset}>
                Try another code
              </button>
            </div>
          )}

          {status === "error" && (
            <div className="ps-alert ps-alert--bad">
              <p className="ps-alertTitle">Something went wrong</p>
              <p className="ps-alertText">We couldn't reach the partner service. Please try again in a moment.</p>
              <button type="button" className="ps-btnGhost" onClick={() => runLookup(code)}>
                Retry
              </button>
            </div>
          )}

          {status === "found" && result && (
            <article className="ps-card ps-partner">
              <div className="ps-partnerTop">
                <span className={`ps-badge ${result.verified ? "ps-badge--ok" : "ps-badge--muted"}`}>
                  {result.verified ? "✓ Verified partner" : "Not verified"}
                </span>
                <span className="ps-code">{result.code}</span>
              </div>

              <h3 className="ps-partnerName">{result.name}</h3>
              <p className="ps-partnerMeta">
                {result.type} · {result.area}
              </p>

              <p className="ps-sectionLabel">Accepts</p>
              <ul className="ps-chips" role="list">
                {result.accepts.map((a) => (
                  <li key={a} className="ps-chip">
                    {a}
                  </li>
                ))}
              </ul>

              <div className="ps-facts">
                <div>
                  <span className="ps-factLabel">Pickup</span>
                  <span className="ps-factValue">{result.pickup ? "Available" : "Drop-off only"}</span>
                </div>
                <div>
                  <span className="ps-factLabel">Benefit</span>
                  <span className="ps-factValue">{result.benefit ?? "None listed"}</span>
                </div>
              </div>

              <div className="ps-actions">
                <button type="button" className="ps-btnGhost" onClick={reset}>
                  Scan another
                </button>
              </div>
            </article>
          )}
        </div>
      </div>
    </section>
  );
}

export default PartnerScanPage;