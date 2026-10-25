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
  ExternalLink,
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

const PATHWAY_NAMES: Record<string, { title: string; badge: string; color: string }> = {
  repair: {
    title: "Garment Repair & Restoration",
    badge: "Repair",
    color: "from-amber-500 to-orange-500",
  },
  reuse_resell: {
    title: "Resale & Direct Reuse",
    badge: "Reuse / Resell",
    color: "from-emerald-500 to-teal-500",
  },
  donate: {
    title: "Community Clothing Donation",
    badge: "Donate",
    color: "from-blue-500 to-cyan-500",
  },
  brand_takeback: {
    title: "Brand In-Store Takeback",
    badge: "Brand Takeback",
    color: "from-purple-500 to-indigo-500",
  },
  recycle: {
    title: "Textile Shredding & Fiber Recycling",
    badge: "Recycle",
    color: "from-slate-600 to-slate-800",
  },
};

export const RecommendationsSection: React.FC<RecommendationsSectionProps> = ({
  recommendations,
  userLocation,
  onReset,
}) => {
  const qrCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedPathway, setSelectedPathway] = useState<RankedPathway>(
    recommendations.ranked_pathways[0]
  );

  // Partner scan simulation state
  const [scanConfirmed, setScanConfirmed] = useState<boolean>(false);
  const [confirming, setConfirming] = useState<boolean>(false);
  const [confirmMessage, setConfirmMessage] = useState<string>("");

  // Generate QR code on canvas whenever qr_id changes
  useEffect(() => {
    if (qrCanvasRef.current && recommendations.qr_id) {
      QRCode.toCanvas(
        qrCanvasRef.current,
        `rethread://outcome/${recommendations.qr_id}`,
        {
          width: 200,
          margin: 1.5,
          color: {
            dark: "#064e3b",
            light: "#ffffff",
          },
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
        1, // Default facility ID (FC Road Master Tailors / Kothrud)
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

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Top Banner Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            Decision Engine Output
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Recommended Circular Next Life
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Hybrid rule & ranking optimization considering condition, defect %, distance, and climate impact.
          </p>
        </div>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors w-fit"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Scan Another Item
        </button>
      </div>

      {/* Primary Recommendation Feature Card */}
      <div className="rounded-3xl bg-gradient-to-br from-emerald-800 via-teal-900 to-slate-900 text-white p-6 sm:p-8 shadow-xl mb-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-400 text-emerald-950 uppercase tracking-wider flex items-center gap-1.5 shadow-sm">
              <Award className="w-4 h-4" />
              Primary Recommendation
            </span>
            <span className="text-xs font-semibold text-emerald-200 flex items-center gap-1">
              Match Confidence: {Math.round(topPathway.score * 100)}%
            </span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-black tracking-tight mb-3">
            {PATHWAY_NAMES[topPathway.pathway]?.title || topPathway.pathway.replace("_", " ")}
          </h2>

          {/* Plain-Language Explanation Trace */}
          <div className="p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/15 text-sm text-emerald-50 leading-relaxed mb-6">
            <p className="font-medium">
              &ldquo;{recommendations.explanation}&rdquo;
            </p>
          </div>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="p-3 rounded-xl bg-white/10 border border-white/10">
              <div className="flex items-center gap-1.5 text-xs text-emerald-300 font-semibold mb-1">
                <Droplets className="w-4 h-4 text-cyan-300" />
                Water Saved
              </div>
              <div className="text-lg font-extrabold text-white">
                {topPathway.impact.water_litres_saved.toLocaleString()} L
              </div>
              <span className="text-[10px] text-emerald-200">Avoids virgin production</span>
            </div>

            <div className="p-3 rounded-xl bg-white/10 border border-white/10">
              <div className="flex items-center gap-1.5 text-xs text-emerald-300 font-semibold mb-1">
                <Leaf className="w-4 h-4 text-emerald-300" />
                CO₂ Avoided
              </div>
              <div className="text-lg font-extrabold text-white">
                {topPathway.impact.co2_kg_saved} kg
              </div>
              <span className="text-[10px] text-emerald-200">Published LCA factor</span>
            </div>

            <div className="p-3 rounded-xl bg-white/10 border border-white/10 col-span-2 sm:col-span-1">
              <div className="flex items-center gap-1.5 text-xs text-emerald-300 font-semibold mb-1">
                <MapPin className="w-4 h-4 text-amber-300" />
                Nearest Partner
              </div>
              <div className="text-sm font-bold text-white truncate">
                {topPathway.nearest_partner?.name || "Local Partner"}
              </div>
              <span className="text-[10px] text-emerald-200">
                {topPathway.nearest_partner?.distance_km} km from user
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Pathways List on Left, QR & Partner Details on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">
        {/* Left: 5 Ranked Pathways Selection */}
        <div className="lg:col-span-7 space-y-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center justify-between">
            <span>All 5 Evaluated Pathways</span>
            <span className="text-xs font-normal text-slate-500">Ranked by desirability & distance</span>
          </h2>

          <div className="space-y-2.5">
            {recommendations.ranked_pathways.map((item, idx) => {
              const isSelected = selectedPathway.pathway === item.pathway;
              const meta = PATHWAY_NAMES[item.pathway] || {
                title: item.pathway,
                badge: item.pathway,
                color: "from-slate-500 to-slate-700",
              };

              return (
                <div
                  key={item.pathway}
                  onClick={() => setSelectedPathway(item)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                    isSelected
                      ? "border-emerald-500 bg-emerald-50/40 shadow-xs ring-1 ring-emerald-500/20"
                      : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/70"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold flex items-center justify-center">
                        #{idx + 1}
                      </span>
                      <span className="font-bold text-sm text-slate-900">
                        {meta.title}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {item.eligible ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                          Eligible
                        </span>
                      ) : (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
                          Restricted by Rules
                        </span>
                      )}
                      <span className="text-xs font-black text-slate-700 ml-1">
                        {Math.round(item.score * 100)}%
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-500 pl-8">
                    <span>
                      {item.nearest_partner ? `${item.nearest_partner.distance_km} km away` : "Drop-off partner available"}
                    </span>
                    <span className="text-emerald-700 font-medium">
                      +{item.impact.water_litres_saved.toLocaleString()} L water saved
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Explainability (SHAP) Insights Drawer */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Decision Explainability (SHAP Feature Attribution)
            </h3>
            <p className="text-xs text-slate-500 mb-3">
              How individual attributes influenced the ranking model for this recommendation:
            </p>
            <div className="space-y-2">
              {Object.entries(recommendations.shap).map(([feat, weight]) => (
                <div key={feat} className="flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-700 capitalize">
                    {feat.replace("_", " ")}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 h-1.5 rounded-full bg-slate-200 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          weight >= 0 ? "bg-emerald-500" : "bg-rose-400"
                        }`}
                        style={{ width: `${Math.min(100, Math.abs(weight) * 200)}%` }}
                      />
                    </div>
                    <span className="font-mono text-[11px] text-slate-600 w-10 text-right">
                      {weight > 0 ? `+${weight.toFixed(2)}` : weight.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Drop-off QR Code & Partner Action Card */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xs flex flex-col items-center text-center">
            <div className="flex items-center gap-2 mb-3">
              <QrCode className="w-5 h-5 text-emerald-600" />
              <h2 className="font-extrabold text-base text-slate-900">
                Drop-Off Intake QR Code
              </h2>
            </div>
            <p className="text-xs text-slate-500 mb-4 max-w-xs">
              Show this QR code to the staff at the drop-off location. A scan confirms the true outcome to train the circular flywheel!
            </p>

            {/* QR Canvas */}
            <div className="p-3 bg-white rounded-2xl shadow-inner border border-slate-200 mb-3">
              <canvas ref={qrCanvasRef} className="rounded-lg" />
            </div>

            <div className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-3 py-1 rounded-md mb-4">
              ID: {recommendations.qr_id}
            </div>

            {/* Partner Details */}
            {selectedPathway.nearest_partner && (
              <div className="w-full text-left p-3.5 rounded-2xl bg-emerald-50/50 border border-emerald-100 mb-4 text-xs">
                <div className="flex items-center gap-1.5 font-bold text-slate-800 mb-1">
                  <Building className="w-4 h-4 text-emerald-700 shrink-0" />
                  <span>{selectedPathway.nearest_partner.name}</span>
                </div>
                {selectedPathway.nearest_partner.address && (
                  <p className="text-slate-600 mb-1 pl-5">
                    {selectedPathway.nearest_partner.address}
                  </p>
                )}
                {selectedPathway.nearest_partner.contact_phone && (
                  <p className="text-slate-500 pl-5">
                    Phone: {selectedPathway.nearest_partner.contact_phone}
                  </p>
                )}
              </div>
            )}

            {/* Flywheel Confirmation Simulation Button (Rule #7) */}
            <div className="w-full pt-2 border-t border-slate-100">
              {scanConfirmed ? (
                <div className="p-3 rounded-xl bg-emerald-100 border border-emerald-300 text-emerald-900 text-xs font-semibold flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>{confirmMessage || "Intake Confirmed! Ground truth saved."}</span>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleSimulateDropoffScan}
                  disabled={confirming}
                  className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white transition-all shadow-xs flex items-center justify-center gap-2"
                >
                  {confirming ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Recording Scan...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span>Simulate Partner Intake Scan (Flywheel Test)</span>
                    </>
                  )}
                </button>
              )}
              <p className="text-[10px] text-slate-400 mt-2">
                *Only confirmed partner scans count as real model training data (Rule #7).
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
