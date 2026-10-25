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
  HelpCircle,
  RefreshCw,
  Eye,
  EyeOff,
} from "lucide-react";
import { AnalyzeResponse, RecommendResponse } from "@/types";
import { getRecommendations } from "@/lib/api";

interface AnalysisResultsSectionProps {
  analysis: AnalyzeResponse;
  previewImages?: { [key: string]: string };
  onRecommendationsReady: (recs: RecommendResponse, userLocation: { lat: number; lon: number }) => void;
  onReset: () => void;
}

export const AnalysisResultsSection: React.FC<AnalysisResultsSectionProps> = ({
  analysis,
  previewImages,
  onRecommendationsReady,
  onReset,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMaterialCam, setShowMaterialCam] = useState<boolean>(false);
  const [showConditionCam, setShowConditionCam] = useState<boolean>(false);

  // Default coordinates to Central Pune (FC Road)
  const [latitude, setLatitude] = useState<number>(18.5204);
  const [longitude, setLongitude] = useState<number>(73.8567);
  const [locationName, setLocationName] = useState<string>("Pune (Shivajinagar / FC Rd)");
  const [weightKg, setWeightKg] = useState<number>(0.5);

  const isCompositionUncertain =
    analysis.composition_status === "uncertain" || analysis.material.label === "uncertain";

  const handleUseBrowserLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(Number(pos.coords.latitude.toFixed(4)));
        setLongitude(Number(pos.coords.longitude.toFixed(4)));
        setLocationName(`Current GPS (${pos.coords.latitude.toFixed(2)}, ${pos.coords.longitude.toFixed(2)})`);
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
      const msg = err instanceof Error ? err.message : "Failed to generate recommendations.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const formatConfidence = (val: number) => Math.round(val * 100);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 mb-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            AI Garment Diagnosis Complete
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Garment Visual & Material Analysis
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Review computer vision findings below before calculating eligible pathways.
          </p>
        </div>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors w-fit"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Scan Another
        </button>
      </div>

      {/* "Uncertain" State Banner if Applicable */}
      {isCompositionUncertain && (
        <div className="mb-6 p-4 rounded-2xl bg-amber-50 border-2 border-amber-300 text-amber-900">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h2 className="font-bold text-sm text-amber-950">
                Composition Uncertainty Flagged [Honest AI Transparency]
              </h2>
              <p className="text-xs text-amber-800 leading-relaxed">
                RGB optical cameras cannot reliably resolve fine blend ratios (e.g. 60/40 vs 80/20) without spectral NIR/HSI hardware, or the care tag had partial/conflicting data.
                Our decision engine gracefully routes this garment without blocking you, providing both recycling and drop-off alternatives!
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main 4 Analysis Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        {/* 1. Material Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-emerald-600" />
                Material Classification
              </span>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded-full capitalize ${
                  analysis.material.label === "natural"
                    ? "bg-emerald-100 text-emerald-800"
                    : analysis.material.label === "synthetic"
                    ? "bg-sky-100 text-sky-800"
                    : analysis.material.label === "blend"
                    ? "bg-purple-100 text-purple-800"
                    : "bg-amber-100 text-amber-800"
                }`}
              >
                {analysis.material.label}
              </span>
            </div>

            <div className="text-2xl font-extrabold text-slate-900 capitalize mb-1">
              {analysis.material.label === "uncertain" ? "Composition Uncertain" : `${analysis.material.label} Fiber`}
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Coarse optical prediction via fine-tuned ResNet-18 (natural, synthetic, blend, or uncertain).
            </p>
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
              <span>Confidence Score</span>
              <span>{formatConfidence(analysis.material.confidence)}%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                style={{ width: `${formatConfidence(analysis.material.confidence)}%` }}
              />
            </div>

            {analysis.material.heatmap_base64 && (
              <div className="mt-3 pt-2.5 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowMaterialCam(!showMaterialCam)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 hover:text-emerald-800 transition-colors"
                >
                  {showMaterialCam ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  {showMaterialCam ? "Hide Grad-CAM Attention" : "Explain Visual AI (Grad-CAM)"}
                </button>
                {showMaterialCam && (
                  <div className="mt-2 p-2 bg-slate-900 rounded-xl overflow-hidden shadow-inner text-white">
                    <img
                      src={analysis.material.heatmap_base64}
                      alt="Material Grad-CAM Heatmap"
                      className="w-full h-36 object-cover rounded-lg"
                    />
                    <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-300 px-0.5">
                      <span>Layer: ResNet18.layer4[-1]</span>
                      <span className="text-emerald-400 font-semibold">🔴 Fabric Texture Attention</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 2. Condition Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-teal-600" />
                Condition & Wear
              </span>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 capitalize">
                {analysis.condition.label.replace("_", " ")}
              </span>
            </div>

            <div className="text-2xl font-extrabold text-slate-900 capitalize mb-1">
              {analysis.condition.label.replace("_", " ")}
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Wear assessment (fading, pilling, structural retention) predicted via visual texture model.
            </p>
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
              <span>Confidence Score</span>
              <span>{formatConfidence(analysis.condition.confidence)}%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
              <div
                className="h-full rounded-full bg-teal-500 transition-all duration-500"
                style={{ width: `${formatConfidence(analysis.condition.confidence)}%` }}
              />
            </div>

            {analysis.condition.heatmap_base64 && (
              <div className="mt-3 pt-2.5 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowConditionCam(!showConditionCam)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-800 transition-colors"
                >
                  {showConditionCam ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  {showConditionCam ? "Hide Grad-CAM Attention" : "Explain Visual AI (Grad-CAM)"}
                </button>
                {showConditionCam && (
                  <div className="mt-2 p-2 bg-slate-900 rounded-xl overflow-hidden shadow-inner text-white">
                    <img
                      src={analysis.condition.heatmap_base64}
                      alt="Condition Grad-CAM Heatmap"
                      className="w-full h-36 object-cover rounded-lg"
                    />
                    <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-300 px-0.5">
                      <span>Layer: ResNet18.layer4[-1]</span>
                      <span className="text-teal-300 font-semibold">🔴 Wear & Surface Analysis</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 3. Damage Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Scissors className="w-4 h-4 text-rose-500" />
                Defects & Damage
              </span>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  analysis.damage.detected
                    ? "bg-rose-100 text-rose-800"
                    : "bg-emerald-100 text-emerald-800"
                }`}
              >
                {analysis.damage.detected ? "Damage Detected" : "Intact / No Defects"}
              </span>
            </div>

            <div className="text-2xl font-extrabold text-slate-900 mb-1">
              {analysis.damage.area_percent}% Garment Area
            </div>
            <p className="text-xs text-slate-500 mb-4">
              YOLOv8 defect bounding evaluation. Items with &lt;25% damage remain eligible for repair restoration.
            </p>
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
              <span>Damaged Surface Proportion</span>
              <span>{analysis.damage.area_percent}%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  analysis.damage.area_percent > 20
                    ? "bg-rose-500"
                    : analysis.damage.area_percent > 5
                    ? "bg-amber-500"
                    : "bg-emerald-500"
                }`}
                style={{ width: `${Math.min(100, analysis.damage.area_percent * 2)}%` }}
              />
            </div>
          </div>
        </div>

        {/* 4. Care Label / Brand Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Tag className="w-4 h-4 text-indigo-600" />
                Care Label & Brand
              </span>
              {analysis.tag.brand ? (
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800">
                  {analysis.tag.brand}
                </span>
              ) : (
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                  Tag Absent
                </span>
              )}
            </div>

            <div className="text-lg font-bold text-slate-900 mb-2">
              {analysis.tag.brand ? (
                <span>Recognized: <strong className="text-indigo-600">{analysis.tag.brand}</strong></span>
              ) : (
                <span className="text-slate-500 text-base font-normal">No brand detected on label</span>
              )}
            </div>

            {/* Fiber composition chips */}
            {Object.keys(analysis.tag.composition).length > 0 ? (
              <div className="flex flex-wrap gap-1.5 mb-3">
                {Object.entries(analysis.tag.composition).map(([fiber, pct]) => (
                  <span
                    key={fiber}
                    className="text-xs font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 capitalize"
                  >
                    {pct}% {fiber}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic mb-3">
                No fiber composition parsed from image.
              </p>
            )}
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
            <span>OCR Confidence: {formatConfidence(analysis.tag.ocr_confidence)}%</span>
            {analysis.tag.agrees_with_vision ? (
              <span className="text-emerald-700 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Agrees with Vision
              </span>
            ) : (
              <span className="text-amber-700 font-semibold flex items-center gap-1">
                <HelpCircle className="w-3.5 h-3.5" />
                Discrepancy Noted
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Drop-Off Geography & Location Settings Bar */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-50/50 via-teal-50/40 to-slate-50 border border-emerald-200/80 mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <MapPin className="w-4 h-4 text-emerald-700" />
              <span className="font-bold text-sm text-slate-800">
                User Drop-off Location (Pune)
              </span>
            </div>
            <p className="text-xs text-slate-600">
              Active: <strong>{locationName}</strong> · GPS ({latitude}, {longitude})
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleUseBrowserLocation}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 transition-colors shadow-2xs"
            >
              Use My Current GPS
            </button>
            <div className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
              <span>Weight:</span>
              <select
                value={weightKg}
                onChange={(e) => setWeightKg(parseFloat(e.target.value))}
                className="bg-white border border-slate-300 rounded px-2 py-1 text-xs"
              >
                <option value={0.25}>0.25 kg (T-Shirt)</option>
                <option value={0.50}>0.50 kg (Shirt / Pants)</option>
                <option value={0.80}>0.80 kg (Denim Jeans)</option>
                <option value={1.20}>1.20 kg (Jacket / Coat)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {/* Recommendation Action Button */}
      <div className="flex flex-col items-center">
        <button
          onClick={handleFetchRecommendations}
          disabled={loading}
          className="w-full sm:w-auto min-w-[320px] px-8 py-4 rounded-xl font-bold text-sm text-white bg-emerald-600 hover:bg-emerald-700 shadow-md shadow-emerald-600/30 transition-all hover:scale-[1.01] flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Running Hybrid Decision Engine...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Recommend Best Circular Pathways</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
        <span className="text-xs text-slate-400 mt-2">
          Evaluates PostgreSQL rules, XGBoost ranking formula, nearest facilities & cited LCA impact.
        </span>
      </div>
    </div>
  );
};
