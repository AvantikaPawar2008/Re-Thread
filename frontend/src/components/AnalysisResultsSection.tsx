"use client";

import React, { useState } from "react";
import {
  Sparkles,
  ArrowRight,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Tag,
  Scissors,
  Layers,
  MapPin,
  RefreshCw,
  Eye,
  EyeOff,
  ChevronDown,
} from "lucide-react";
import { AnalyzeResponse, RecommendResponse } from "@/types";
import { getRecommendations } from "@/lib/api";

interface AnalysisResultsSectionProps {
  analysis: AnalyzeResponse;
  previewImages?: { [key: string]: string };
  onRecommendationsReady: (recs: RecommendResponse, userLocation: { lat: number; lon: number }) => void;
  onReset: () => void;
}

const WEIGHT_OPTIONS = [
  { value: 0.25, label: "T-shirt (0.25 kg)" },
  { value: 0.5, label: "Shirt or trousers (0.5 kg)" },
  { value: 0.8, label: "Denim jeans (0.8 kg)" },
  { value: 1.2, label: "Jacket or coat (1.2 kg)" },
];

const MATERIAL_TEXT: Record<string, string> = {
  natural: "Natural fibre",
  synthetic: "Synthetic fibre",
  blend: "Fibre blend",
  uncertain: "Unclear fibre",
};

function confidenceNote(pct: number): string {
  if (pct >= 80) return "The model is fairly sure. Trust this unless the photo looks unusual.";
  if (pct >= 60) return "The model is somewhat sure. A clearer photo would help.";
  return "The model is unsure. Treat this as a rough guess.";
}

export const AnalysisResultsSection: React.FC<AnalysisResultsSectionProps> = ({
  analysis,
  onRecommendationsReady,
  onReset,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMaterialCam, setShowMaterialCam] = useState(false);
  const [showConditionCam, setShowConditionCam] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  // Default coordinates: Central Pune (FC Road)
  const [latitude, setLatitude] = useState<number>(18.5204);
  const [longitude, setLongitude] = useState<number>(73.8567);
  const [locationName, setLocationName] = useState<string>("Pune (Shivajinagar / FC Rd)");
  const [weightKg, setWeightKg] = useState<number>(0.5);

  const isCompositionUncertain =
    analysis.composition_status === "uncertain" || analysis.material.label === "uncertain";

  const isVLM = analysis.source === "vlm";
  const isStub = !analysis.source || analysis.source === "stub";
  const reasoning = analysis.reasoning;

  const materialPct = Math.round(analysis.material.confidence * 100);
  const conditionPct = Math.round(analysis.condition.confidence * 100);
  const damagePct = analysis.damage.area_percent;
  const conditionText = analysis.condition.label.replace(/_/g, " ");
  const hasComposition = Object.keys(analysis.tag.composition).length > 0;

  const damageLevel = damagePct > 20 ? "high" : damagePct > 5 ? "moderate" : "low";
  const summaryTitle = analysis.damage.detected
    ? damagePct < 25
      ? "Repairable with some wear"
      : "Heavily damaged"
    : "Looks intact";
  const summaryText = analysis.damage.detected
    ? `About ${damagePct}% of the garment shows damage (${damageLevel}). Garments with less than 25% damage are usually eligible for repair.`
    : "No significant damage was detected. This garment is a good candidate for resale, donation or reuse.";

  const handleUseBrowserLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(Number(pos.coords.latitude.toFixed(4)));
        setLongitude(Number(pos.coords.longitude.toFixed(4)));
        setLocationName(`Current location (${pos.coords.latitude.toFixed(2)}, ${pos.coords.longitude.toFixed(2)})`);
      },
      (err) => {
        alert(`Location permission denied or unavailable: ${err.message}`);
      }
    );
  };

  const handleFetchRecommendations = async () => {
    setError(null);
    setLoading(true);
    try {
      const recs = await getRecommendations(analysis, latitude, longitude, weightKg);
      onRecommendationsReady(recs, { lat: latitude, lon: longitude });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Could not generate recommendations. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-5 py-10 text-slate-900">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <p className="inline-flex items-center gap-1.5 rounded-full bg-[#e6eef5] px-3 py-1 text-xs font-semibold text-[#0b2a44]">
              <CheckCircle2 className="h-3.5 w-3.5 text-[#1d5c8c]" aria-hidden />
              Analysis complete
            </p>
            {isVLM && (
              <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                <Sparkles className="h-3.5 w-3.5 text-blue-600" aria-hidden />
                AI vision analysis (estimate)
              </span>
            )}
            {isStub && (
              <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                Demo mode
              </span>
            )}
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight md:text-4xl">Your garment, assessed</h1>
          <p className="mt-2 text-sm text-slate-600">Here is what we found. Review it, then see your best options.</p>
        </div>
        <button
          onClick={onReset}
          className="inline-flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:border-[#1d5c8c] hover:text-[#1d5c8c]"
        >
          <RotateCcw className="h-4 w-4" aria-hidden />
          Scan another
        </button>
      </div>

      {/* Summary */}
      <section className="mb-6 overflow-hidden rounded-3xl bg-gradient-to-br from-[#0b2a44] via-[#1d5c8c] to-[#2f7ab0] p-7 text-white shadow-xl">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#bdd9ee]">Overall</p>
        <h2 className="mt-2 text-2xl font-extrabold tracking-tight md:text-3xl">{summaryTitle}</h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#d6e4ef]">{summaryText}</p>
        <div className="mt-5 flex flex-wrap gap-2 text-xs font-semibold">
          <span className="rounded-full bg-white/15 px-3 py-1.5">
            {MATERIAL_TEXT[analysis.material.label] ?? analysis.material.label}
          </span>
          <span className="rounded-full bg-white/15 px-3 py-1.5 capitalize">{conditionText}</span>
          <span className="rounded-full bg-white/15 px-3 py-1.5">
            {analysis.damage.detected ? "Damage found" : "No damage found"}
          </span>
        </div>
      </section>

      {isCompositionUncertain && (
        <div className="mb-6 flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-amber-900">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" aria-hidden />
          <div>
            <h2 className="text-sm font-bold">We couldn't confirm the fibre content</h2>
            <p className="mt-1 text-sm leading-relaxed text-amber-800">
              A photo can't reliably tell blends apart, and the care label may be missing or unclear. We'll still
              suggest both recycling and drop-off options.
            </p>
          </div>
        </div>
      )}

      {/* Findings */}
      <div className="grid gap-5 md:grid-cols-2">
        {/* Material */}
        <article className="flex flex-col rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
            <Layers className="h-4 w-4 text-[#1d5c8c]" aria-hidden />
            Material
          </span>
          <h3 className="mt-4 text-2xl font-extrabold tracking-tight">
            {MATERIAL_TEXT[analysis.material.label] ?? analysis.material.label}
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{confidenceNote(materialPct)}</p>

          <div className="mt-5">
            <div className="mb-1.5 flex justify-between text-xs font-semibold text-slate-600">
              <span>Confidence</span>
              <span>{materialPct}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-[#1d5c8c] transition-all duration-700" style={{ width: `${materialPct}%` }} />
            </div>
          </div>

          {reasoning?.material && (
            <p className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs leading-relaxed text-slate-600 italic">
              “{reasoning.material}”
            </p>
          )}

          {analysis.material.heatmap_base64 && (
            <div className="mt-auto pt-5">
              <button
                type="button"
                onClick={() => setShowMaterialCam(!showMaterialCam)}
                aria-expanded={showMaterialCam}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#1d5c8c] hover:underline"
              >
                {showMaterialCam ? <EyeOff className="h-3.5 w-3.5" aria-hidden /> : <Eye className="h-3.5 w-3.5" aria-hidden />}
                {showMaterialCam ? "Hide where the model looked" : "See where the model looked"}
              </button>
              {showMaterialCam && (
                <img
                  src={analysis.material.heatmap_base64}
                  alt="Heatmap of the areas the material model focused on"
                  className="mt-3 h-40 w-full rounded-2xl object-cover"
                />
              )}
            </div>
          )}
        </article>

        {/* Condition */}
        <article className="flex flex-col rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
            <Sparkles className="h-4 w-4 text-[#1d5c8c]" aria-hidden />
            Condition
          </span>
          <h3 className="mt-4 text-2xl font-extrabold capitalize tracking-tight">{conditionText}</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Based on fading, pilling and how well the fabric holds its shape.
          </p>

          <div className="mt-5">
            <div className="mb-1.5 flex justify-between text-xs font-semibold text-slate-600">
              <span>Confidence</span>
              <span>{conditionPct}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-[#1d5c8c] transition-all duration-700" style={{ width: `${conditionPct}%` }} />
            </div>
          </div>

          {reasoning?.condition && (
            <p className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs leading-relaxed text-slate-600 italic">
              “{reasoning.condition}”
            </p>
          )}

          {analysis.condition.heatmap_base64 && (
            <div className="mt-auto pt-5">
              <button
                type="button"
                onClick={() => setShowConditionCam(!showConditionCam)}
                aria-expanded={showConditionCam}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#1d5c8c] hover:underline"
              >
                {showConditionCam ? <EyeOff className="h-3.5 w-3.5" aria-hidden /> : <Eye className="h-3.5 w-3.5" aria-hidden />}
                {showConditionCam ? "Hide where the model looked" : "See where the model looked"}
              </button>
              {showConditionCam && (
                <img
                  src={analysis.condition.heatmap_base64}
                  alt="Heatmap of the areas the condition model focused on"
                  className="mt-3 h-40 w-full rounded-2xl object-cover"
                />
              )}
            </div>
          )}
        </article>

        {/* Damage */}
        <article className="flex flex-col rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
            <Scissors className="h-4 w-4 text-rose-500" aria-hidden />
            Damage
          </span>
          <h3 className="mt-4 text-2xl font-extrabold tracking-tight">
            {analysis.damage.detected ? `${damagePct}% of the garment` : "No damage found"}
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            {analysis.damage.detected
              ? "Garments with less than 25% damage can usually be repaired."
              : "Nothing visible needs repair."}
          </p>

          <div className="mt-5">
            <div className="mb-1.5 flex justify-between text-xs font-semibold text-slate-600">
              <span>Share of damaged area (estimated)</span>
              <span>{damagePct}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  damagePct > 20 ? "bg-rose-500" : damagePct > 5 ? "bg-amber-500" : "bg-emerald-500"
                }`}
                style={{ width: `${Math.min(100, damagePct * 2)}%` }}
              />
            </div>
          </div>

          {reasoning?.damage && (
            <p className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs leading-relaxed text-slate-600 italic">
              “{reasoning.damage}”
            </p>
          )}
        </article>

        {/* Care label */}
        <article className="flex flex-col rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
            <Tag className="h-4 w-4 text-indigo-600" aria-hidden />
            Care label
          </span>
          <h3 className="mt-4 text-2xl font-extrabold tracking-tight">{analysis.tag.brand || "No label found"}</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            {hasComposition
              ? "We read the fibre content from the label."
              : "We couldn't read a fibre content from a label in this photo."}
          </p>

          {hasComposition && (
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(analysis.tag.composition).map(([fiber, pct]) => (
                <span key={fiber} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold capitalize text-slate-700">
                  {pct}% {fiber}
                </span>
              ))}
            </div>
          )}

          {reasoning?.tag && (
            <p className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs leading-relaxed text-slate-600 italic">
              “{reasoning.tag}”
            </p>
          )}

          <div className="mt-auto flex items-center justify-between border-t border-slate-100 pt-5 text-xs text-slate-500">
            <span>Label reading: {Math.round(analysis.tag.ocr_confidence * 100)}% sure</span>
            {analysis.tag.agrees_with_vision ? (
              <span className="flex items-center gap-1 font-semibold text-emerald-700">
                <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
                Matches the photo
              </span>
            ) : (
              <span className="flex items-center gap-1 font-semibold text-amber-700">
                <AlertTriangle className="h-3.5 w-3.5" aria-hidden />
                Doesn't fully match
              </span>
            )}
          </div>
        </article>
      </div>

      {/* Technical details */}
      <div className="mt-6 rounded-2xl border border-slate-200 bg-white">
        <button
          type="button"
          onClick={() => setShowDetails(!showDetails)}
          aria-expanded={showDetails}
          className="flex w-full items-center justify-between px-5 py-4 text-left text-sm font-semibold text-slate-700"
        >
          How this was measured
          <ChevronDown className={`h-4 w-4 transition-transform ${showDetails ? "rotate-180" : ""}`} aria-hidden />
        </button>
        {showDetails && (
          <ul className="space-y-2 border-t border-slate-100 px-5 py-4 text-sm text-slate-600">
            <li>Material: image classifier (ResNet-18), trained to tell natural, synthetic and blended fabrics apart.</li>
            <li>Condition: visual texture model estimating fading, pilling and structure.</li>
            <li>Damage: object detection (YOLOv8) measuring the share of the garment that is damaged.</li>
            <li>Label: text reading (OCR), cross-checked against what the camera sees.</li>
          </ul>
        )}
      </div>

      {/* Location and weight */}
      <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="flex items-center gap-2 text-sm font-bold">
              <MapPin className="h-4 w-4 text-[#1d5c8c]" aria-hidden />
              Where are you dropping off?
            </p>
            <p className="mt-1 text-sm text-slate-600">
              Using <span className="font-semibold text-slate-800">{locationName}</span>
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleUseBrowserLocation}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition-colors hover:border-[#1d5c8c] hover:text-[#1d5c8c]"
            >
              Use my location
            </button>
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-600">
              <span className="sr-only">Garment weight</span>
              <select
                value={weightKg}
                onChange={(e) => setWeightKg(parseFloat(e.target.value))}
                className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1d5c8c] focus:outline-none"
              >
                {WEIGHT_OPTIONS.map((w) => (
                  <option key={w.value} value={w.value}>
                    {w.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </div>

      {error && (
        <div role="alert" className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          {error}
        </div>
      )}

      {/* Primary action */}
      <div className="mt-8 flex flex-col items-center gap-3">
        <button
          onClick={handleFetchRecommendations}
          disabled={loading}
          className="inline-flex w-full min-w-[280px] items-center justify-center gap-2 rounded-full bg-[#0b2a44] px-8 py-4 text-sm font-bold text-white shadow-lg shadow-[#0b2a44]/25 transition-all hover:bg-[#1d5c8c] disabled:opacity-60 sm:w-auto"
        >
          {loading ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" aria-hidden />
              <span>Finding your best options…</span>
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" aria-hidden />
              <span>See what to do with this garment</span>
              <ArrowRight className="h-4 w-4" aria-hidden />
            </>
          )}
        </button>
        <p className="text-xs text-slate-500">
          Based on nearby drop-off points, repair options and estimated environmental impact.
        </p>
      </div>
    </div>
  );
};

export default AnalysisResultsSection;