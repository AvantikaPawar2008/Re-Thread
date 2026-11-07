"use client";

import React, { useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import {
  Sparkles,
  MapPin,
  Droplets,
  Leaf,
  CheckCircle2,
  QrCode,
  RotateCcw,
  ChevronRight,
  ShieldCheck,
  Building,
  Award,
  RefreshCw,
} from "lucide-react";
import { RecommendResponse, RankedPathway } from "@/types";
import { confirmOutcome } from "@/lib/api";

interface RecommendationsSectionProps {
  recommendations: RecommendResponse;
  userLocation: { lat: number; lon: number };
  onReset: () => void;
}

const PATHWAY_NAMES: Record<string, { title: string; badge: string }> = {
  repair: { title: "Garment Repair & Restoration", badge: "Repair" },
  reuse_resell: { title: "Resale & Direct Reuse", badge: "Reuse / Resell" },
  donate: { title: "Community Clothing Donation", badge: "Donate" },
  brand_takeback: { title: "Brand In-Store Takeback", badge: "Brand Takeback" },
  recycle: { title: "Textile Shredding & Fibre Recycling", badge: "Recycle" },
};

export const RecommendationsSection: React.FC<RecommendationsSectionProps> = ({
  recommendations,
  onReset,
}) => {
  const qrCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedPathway, setSelectedPathway] = useState<RankedPathway>(
    recommendations.ranked_pathways[0]
  );
  const [scanConfirmed, setScanConfirmed] = useState<boolean>(false);
  const [confirming, setConfirming] = useState<boolean>(false);
  const [confirmMessage, setConfirmMessage] = useState<string>("");

  useEffect(() => {
    if (qrCanvasRef.current && recommendations.qr_id) {
      QRCode.toCanvas(
        qrCanvasRef.current,
        `rethread://outcome/${recommendations.qr_id}`,
        {
          width: 200,
          margin: 1.5,
          color: { dark: "#0b2a44", light: "#ffffff" },
        },
        (error) => {
          if (error) console.error("QR Code generation error:", error);
        }
      );
    }
  }, [recommendations.qr_id]);

  const handleSimulateDropoffScan = async () => {
    setConfirming(true);
    try {
      const res = await confirmOutcome(
        recommendations.qr_id,
        1, // Default facility ID
        selectedPathway.pathway,
        "Confirmed via partner test scanner interface"
      );
      setScanConfirmed(true);
      setConfirmMessage(res.message);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Outcome confirmation failed.";
      alert(msg);
    } finally {
      setConfirming(false);
    }
  };

  const topPathway = recommendations.ranked_pathways[0];
  const topMeta = PATHWAY_NAMES[topPathway.pathway];
  const maxShap = Math.max(...Object.values(recommendations.shap).map((w) => Math.abs(w)), 0.01);

  return (
    <div className="mx-auto max-w-5xl px-5 py-10 text-slate-900">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-[#e6eef5] px-3 py-1 text-xs font-semibold text-[#0b2a44]">
            <Sparkles className="h-3.5 w-3.5 text-[#1d5c8c]" aria-hidden />
            Your recommendation
          </p>
          <h1 className="text-3xl font-extrabold tracking-tight md:text-4xl">Your best next step</h1>
          <p className="mt-2 text-sm text-slate-600">
            Based on the garment's condition, damage, and nearby options.
          </p>
        </div>
        <button
          onClick={onReset}
          className="inline-flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:border-[#1d5c8c] hover:text-[#1d5c8c]"
        >
          <RotateCcw className="h-4 w-4" aria-hidden />
          Scan another item
        </button>
      </div>

      {/* Primary recommendation */}
      <section className="relative mb-8 overflow-hidden rounded-3xl bg-gradient-to-br from-[#e6f2fb] via-[#d2e7f6] to-[#b9d9ef] p-7 shadow-lg sm:p-9">
        <div className="pointer-events-none absolute -right-16 -top-16 h-72 w-72 rounded-full bg-white/50 blur-3xl" />

        <div className="relative">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[#0b2a44] px-3.5 py-1.5 text-xs font-bold uppercase tracking-wider text-white">
              <Award className="h-4 w-4" aria-hidden />
              Best match
            </span>
            <span className="text-xs font-semibold text-[#174e7c]">
              Match confidence: {Math.round(topPathway.score * 100)}%
            </span>
          </div>

          <h2 className="text-2xl font-black tracking-tight text-[#0b2a44] sm:text-3xl">
            {topMeta?.title || topPathway.pathway.replace(/_/g, " ")}
          </h2>

          <div className="mt-5 rounded-2xl border border-white/70 bg-white/70 p-5 text-sm leading-relaxed text-[#1f3a52] backdrop-blur">
            <p className="font-medium">&ldquo;{recommendations.explanation}&rdquo;</p>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
            <div className="rounded-2xl bg-white/80 p-4">
              <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-[#1d5c8c]">
                <Droplets className="h-4 w-4" aria-hidden />
                Water saved
              </div>
              <div className="text-xl font-extrabold text-[#0b2a44]">
                {topPathway.impact.water_litres_saved.toLocaleString()} L
              </div>
              <p className="mt-0.5 text-[11px] text-slate-600">Avoids virgin production</p>
            </div>

            <div className="rounded-2xl bg-white/80 p-4">
              <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-[#1d5c8c]">
                <Leaf className="h-4 w-4" aria-hidden />
                CO₂ avoided
              </div>
              <div className="text-xl font-extrabold text-[#0b2a44]">{topPathway.impact.co2_kg_saved} kg</div>
              <p className="mt-0.5 text-[11px] text-slate-600">Published LCA factor</p>
            </div>

            <div className="col-span-2 rounded-2xl bg-white/80 p-4 sm:col-span-1">
              <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-[#1d5c8c]">
                <MapPin className="h-4 w-4" aria-hidden />
                Nearest partner
              </div>
              <div className="truncate text-sm font-bold text-[#0b2a44]">
                {topPathway.nearest_partner?.name || "Local partner"}
              </div>
              <p className="mt-0.5 text-[11px] text-slate-600">
                {topPathway.nearest_partner?.distance_km} km from you
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Pathways */}
        <div className="space-y-4 lg:col-span-7">
          <div className="flex items-baseline justify-between">
            <h2 className="text-lg font-bold">All {recommendations.ranked_pathways.length} options</h2>
            <span className="text-xs text-slate-500">Ranked by fit and distance</span>
          </div>

          <div className="space-y-2.5">
            {recommendations.ranked_pathways.map((item, idx) => {
              const isSelected = selectedPathway.pathway === item.pathway;
              const meta = PATHWAY_NAMES[item.pathway] || { title: item.pathway, badge: item.pathway };

              return (
                <button
                  key={item.pathway}
                  type="button"
                  onClick={() => setSelectedPathway(item)}
                  aria-pressed={isSelected}
                  className={`w-full rounded-2xl border p-4 text-left transition-all ${
                    isSelected
                      ? "border-[#1d5c8c] bg-[#f0f7fc] ring-2 ring-[#1d5c8c]/15"
                      : "border-slate-200 bg-white hover:border-[#9fc6e4] hover:bg-slate-50"
                  }`}
                >
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-2.5">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-700">
                        {idx + 1}
                      </span>
                      <span className="truncate text-sm font-bold">{meta.title}</span>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      {item.eligible ? (
                        <span className="rounded-full bg-[#e6f2fb] px-2 py-0.5 text-[10px] font-bold text-[#174e7c]">
                          Eligible
                        </span>
                      ) : (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">
                          Not suitable
                        </span>
                      )}
                      <span className="text-xs font-black text-slate-700">{Math.round(item.score * 100)}%</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pl-8 text-xs text-slate-500">
                    <span>
                      {item.nearest_partner ? `${item.nearest_partner.distance_km} km away` : "Drop-off partner available"}
                    </span>
                    <span className="font-medium text-[#1d5c8c]">
                      +{item.impact.water_litres_saved.toLocaleString()} L water saved
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Explainability */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <h3 className="mb-1.5 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
              <ShieldCheck className="h-4 w-4 text-[#1d5c8c]" aria-hidden />
              Why this was ranked this way
            </h3>
            <p className="mb-4 text-xs text-slate-500">How each factor influenced this recommendation.</p>
            <div className="space-y-3">
              {Object.entries(recommendations.shap).map(([feat, weight]) => (
                <div key={feat} className="flex items-center justify-between gap-3 text-xs">
                  <span className="font-medium capitalize text-slate-700">{feat.replace(/_/g, " ")}</span>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-32 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className={`h-full rounded-full ${weight >= 0 ? "bg-[#1d5c8c]" : "bg-rose-400"}`}
                        style={{ width: `${Math.min(100, (Math.abs(weight) / maxShap) * 100)}%` }}
                      />
                    </div>
                    <span className="w-12 text-right font-mono text-[11px] text-slate-600">
                      {weight > 0 ? `+${weight.toFixed(2)}` : weight.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* QR and partner */}
        <div className="lg:col-span-5">
          <div className="flex flex-col items-center rounded-3xl border border-slate-200 bg-white p-6 text-center shadow-sm">
            <div className="mb-2 flex items-center gap-2">
              <QrCode className="h-5 w-5 text-[#1d5c8c]" aria-hidden />
              <h2 className="text-base font-extrabold">Drop-off QR code</h2>
            </div>
            <p className="mb-5 max-w-xs text-xs leading-relaxed text-slate-500">
              Show this at the drop-off point. The staff scan confirms what happened to your garment.
            </p>

            <div className="mb-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-inner">
              <canvas ref={qrCanvasRef} className="rounded-lg" />
            </div>

            <div className="mb-5 rounded-md bg-[#f0f7fc] px-3 py-1 font-mono text-xs font-bold text-[#174e7c]">
              ID: {recommendations.qr_id}
            </div>

            {selectedPathway.nearest_partner && (
              <div className="mb-5 w-full rounded-2xl border border-[#d2e7f6] bg-[#f5faff] p-4 text-left text-xs">
                <div className="mb-1 flex items-center gap-1.5 font-bold text-slate-800">
                  <Building className="h-4 w-4 shrink-0 text-[#1d5c8c]" aria-hidden />
                  <span>{selectedPathway.nearest_partner.name}</span>
                </div>
                {selectedPathway.nearest_partner.address && (
                  <p className="mb-1 pl-5 text-slate-600">{selectedPathway.nearest_partner.address}</p>
                )}
                {selectedPathway.nearest_partner.contact_phone && (
                  <p className="pl-5 text-slate-500">Phone: {selectedPathway.nearest_partner.contact_phone}</p>
                )}
              </div>
            )}

            <div className="w-full border-t border-slate-100 pt-5">
              {scanConfirmed ? (
                <div className="flex items-center justify-center gap-2 rounded-xl border border-[#b9d9ef] bg-[#e6f2fb] p-3 text-xs font-semibold text-[#0b2a44]">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-[#1d5c8c]" aria-hidden />
                  <span>{confirmMessage || "Intake confirmed. Thank you."}</span>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleSimulateDropoffScan}
                  disabled={confirming}
                  className="flex w-full items-center justify-center gap-2 rounded-full bg-[#0b2a44] px-4 py-3 text-xs font-bold text-white transition-colors hover:bg-[#1d5c8c] disabled:opacity-60"
                >
                  {confirming ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden />
                      <span>Recording scan…</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="h-4 w-4" aria-hidden />
                      <span>Simulate partner intake scan</span>
                      <ChevronRight className="h-3.5 w-3.5" aria-hidden />
                    </>
                  )}
                </button>
              )}
              <p className="mt-3 text-[10px] text-slate-400">
                Only confirmed partner scans count as real training data.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecommendationsSection;