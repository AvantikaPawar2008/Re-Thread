"use client";

import React, { useState } from "react";
import { Sparkles, Upload, RefreshCw } from "lucide-react";
import { analyzeGarment, identifyFabric } from "@/lib/api";
import type { AnalyzeResponse } from "@/types";

type FabricGuess = { label: string; confidence: number }; // confidence in 0-100
type FabricResult = {
  label: string;
  confidence: number;
  top: FabricGuess[];
  error?: string;
};

/** Accepts several likely response shapes from /fabric/identify. */
function normalizeFabric(raw: any): FabricResult {
  if (!raw) {
    return { label: "", confidence: 0, top: [], error: "Empty response from server." };
  }

  const msg = raw.error || raw.detail || raw.message;
  if (msg && !(raw.fabric || raw.label || raw.prediction)) {
    return { label: "", confidence: 0, top: [], error: String(msg) };
  }

  const toPct = (n: number) => (n <= 1 ? n * 100 : n);
  const label = String(raw.fabric ?? raw.label ?? raw.prediction ?? raw.class ?? "");
  const confidence = toPct(Number(raw.confidence ?? raw.score ?? raw.probability ?? 0));

  const list = raw.top3 ?? raw.top_k ?? raw.predictions ?? raw.top ?? [];
  const top: FabricGuess[] = (Array.isArray(list) ? list : []).slice(0, 3).map((g: any) =>
    Array.isArray(g)
      ? { label: String(g[0]), confidence: toPct(Number(g[1])) }
      : {
          label: String(g.fabric ?? g.label ?? g.name ?? g.class ?? ""),
          confidence: toPct(Number(g.confidence ?? g.score ?? g.probability ?? 0)),
        }
  );

  return { label, confidence, top };
}

export const FabricIdentifier: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [fabric, setFabric] = useState<FabricResult | null>(null);

  const onPick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;

    if (preview) URL.revokeObjectURL(preview);
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setFabric(null);
    setError(null);
  };

  const analyze = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setFabric(null);

    try {
      const formData = new FormData();
      formData.append("garment_images", file);

      // Run both requests together. One failing must not hide the other.
      const [analysisRes, fabricRes] = await Promise.allSettled([
        analyzeGarment(formData), // condition, damage, tag, broad material
        identifyFabric(file),     // ResNet50: Cotton, Denim, Silk...
      ]);

      if (analysisRes.status === "fulfilled") {
        setResult(analysisRes.value);
      }

      if (fabricRes.status === "fulfilled") {
        setFabric(normalizeFabric(fabricRes.value));
      } else {
        const reason: any = fabricRes.reason;
        setFabric({
          label: "",
          confidence: 0,
          top: [],
          error: reason?.message || "Fabric identification failed.",
        });
      }

      if (analysisRes.status === "rejected" && fabricRes.status === "rejected") {
        const reason: any = analysisRes.reason;
        setError(reason?.message || "Something went wrong. Please try again.");
      }
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setFile(null);
    setPreview(null);
    setResult(null);
    setFabric(null);
    setError(null);
  };

  const weightsMissing = !!fabric?.error && /weights|not found|trained/i.test(fabric.error);

  return (
    <section
      id="fabric"
      className="max-w-6xl mx-auto px-4 sm:px-6 mt-10 scroll-mt-24"
    >
      <div className="rounded-2xl border border-emerald-100 bg-white p-5 sm:p-7 shadow-sm">
        {/* Heading */}
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-5 h-5 text-emerald-600" />
          <h2 className="text-xl font-extrabold text-slate-900">
            Fabric Type Identifier
          </h2>
        </div>

        <p className="text-sm text-slate-500 mb-5">
          Upload a photo of your garment to analyze its material,
          condition and environmental impact.
        </p>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Image Upload */}
          <div>
            <label className="flex flex-col items-center justify-center h-56 rounded-xl border-2 border-dashed border-emerald-200 bg-emerald-50/40 cursor-pointer hover:bg-emerald-50 overflow-hidden">
              {preview ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={preview}
                  alt="Selected garment"
                  className="h-full w-full object-cover"
                />
              ) : (
                <span className="flex flex-col items-center text-slate-500 text-sm gap-2">
                  <Upload className="w-6 h-6" />
                  Click to choose a JPG, PNG or WebP image
                </span>
              )}

              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={onPick}
              />
            </label>

            {/* Buttons */}
            <div className="flex gap-2 mt-3">
              <button
                onClick={analyze}
                disabled={!file || loading}
                className="flex-1 px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-semibold disabled:opacity-50"
              >
                {loading ? "Analyzing..." : "Identify Fabric"}
              </button>

              <button
                onClick={reset}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm font-semibold text-slate-600 flex items-center gap-1"
              >
                <RefreshCw className="w-4 h-4" />
                Reset
              </button>
            </div>
          </div>

          {/* Results */}
          <div aria-live="polite">
            {error && (
              <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 text-sm text-rose-700">
                {error}
              </div>
            )}

            {(result || fabric) && (
              <div className="space-y-4">
                {/* Identified fabric (ResNet50) */}
                {fabric && !fabric.error && (
                  <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4">
                    <p className="text-xs font-bold uppercase tracking-wider text-emerald-700">
                      Identified Fabric
                    </p>

                    <p className="text-3xl font-extrabold text-slate-900 capitalize">
                      {fabric.label}
                    </p>

                    <p className="text-sm text-slate-600 mt-1">
                      Model confidence: {fabric.confidence.toFixed(0)}%
                    </p>

                    {result && (
                      <p className="text-xs text-slate-500 mt-1 capitalize">
                        Material category: {result.material.label}
                      </p>
                    )}

                    {fabric.top.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs font-semibold text-slate-600">
                          Top guesses
                        </p>
                        {fabric.top.map((g) => (
                          <div key={g.label}>
                            <div className="flex justify-between text-xs text-slate-700">
                              <span className="capitalize">{g.label}</span>
                              <span>{g.confidence.toFixed(0)}%</span>
                            </div>
                            <div className="h-1.5 rounded-full bg-emerald-100 mt-1">
                              <div
                                className="h-full rounded-full bg-emerald-600"
                                style={{ width: `${Math.min(100, g.confidence)}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Fabric model unavailable: fall back to broad category */}
                {fabric?.error && (
                  <>
                    {result && (
                      <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4">
                        <p className="text-xs font-bold uppercase tracking-wider text-emerald-700">
                          Predicted Material
                        </p>
                        <p className="text-3xl font-extrabold text-slate-900 capitalize">
                          {result.material.label}
                        </p>
                        <p className="text-sm text-slate-600 mt-1">
                          Model confidence:{" "}
                          {(result.material.confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                    )}

                    <div className="rounded-xl bg-amber-50 border border-amber-200 p-4">
                      <p className="text-sm text-amber-900">
                        {weightsMissing
                          ? "The specific fabric model isn't trained yet (fabric_resnet50.pt not found), so only the broad material category is shown. Add the weights file and restart the backend to see names like Cotton or Denim."
                          : `Specific fabric name unavailable: ${fabric.error}`}
                      </p>
                    </div>
                  </>
                )}

                {result && (
                  <>
                    {/* Condition */}
                    <div className="rounded-xl bg-slate-50 border border-slate-200 p-4">
                      <h3 className="font-bold text-slate-900">Garment Condition</h3>

                      <p className="text-lg capitalize text-slate-700 mt-1">
                        {result.condition.label.replace(/_/g, " ")}
                      </p>

                      <p className="text-sm text-slate-500">
                        Confidence: {(result.condition.confidence * 100).toFixed(0)}%
                      </p>
                    </div>

                    {/* Damage */}
                    <div className="rounded-xl bg-slate-50 border border-slate-200 p-4">
                      <h3 className="font-bold text-slate-900">Damage Analysis</h3>

                      <p className="text-sm text-slate-700 mt-2">
                        Damage detected: {result.damage.detected ? "Yes" : "No"}
                      </p>

                      <p className="text-sm text-slate-700">
                        Damaged area: {result.damage.area_percent}%
                      </p>

                      <p className="text-sm text-slate-700">
                        Detected regions: {result.damage.boxes.length}
                      </p>
                    </div>

                    {/* Composition */}
                    <div className="rounded-xl bg-slate-50 border border-slate-200 p-4">
                      <h3 className="font-bold text-slate-900">Fabric Composition</h3>

                      <p className="text-sm text-slate-600 mt-1">
                        Status: {result.composition_status}
                      </p>

                      {Object.keys(result.tag.composition).length > 0 ? (
                        <ul className="mt-2 space-y-1 text-sm text-slate-700">
                          {Object.entries(result.tag.composition).map(
                            ([name, value]) => (
                              <li key={name}>
                                <b>{name}:</b> {value}
                              </li>
                            )
                          )}
                        </ul>
                      ) : (
                        <p className="text-sm text-slate-500 mt-2">
                          No composition information available.
                        </p>
                      )}
                    </div>

                    {/* Clothing Tag */}
                    <div className="rounded-xl bg-slate-50 border border-slate-200 p-4">
                      <h3 className="font-bold text-slate-900">
                        Clothing Tag Information
                      </h3>

                      <p className="text-sm text-slate-700 mt-2">
                        Brand: {result.tag.brand || "Not detected"}
                      </p>

                      <p className="text-sm text-slate-700">
                        Tag confidence: {(result.tag.ocr_confidence * 100).toFixed(0)}%
                      </p>

                      <p className="text-sm text-slate-700">
                        Vision agreement: {result.tag.agrees_with_vision ? "Yes" : "No"}
                      </p>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};