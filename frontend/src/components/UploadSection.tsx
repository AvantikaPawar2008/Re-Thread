"use client";

import React, { useRef, useState } from "react";
import {
  Camera,
  Upload,
  X,
  Sparkles,
  AlertCircle,
  RefreshCw,
  RotateCcw,
} from "lucide-react";
import { AnalyzeResponse } from "@/types";
import { analyzeGarment } from "@/lib/api";

interface UploadSectionProps {
  onAnalysisComplete: (result: AnalyzeResponse, previewImages: { [key: string]: string }) => void;
}

const MAX_MB = 10;
const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];

export const UploadSection: React.FC<UploadSectionProps> = ({ onAnalysisComplete }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [error, setError] = useState<string | null>(null);

  const pickFile = (f: File | null) => {
    setError(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);

    if (!f) {
      setFile(null);
      setPreviewUrl(null);
      return;
    }
    if (!ACCEPTED.includes(f.type)) {
      setError("Please upload a JPG, PNG or WebP image.");
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`This image is larger than ${MAX_MB} MB. Please choose a smaller one.`);
      return;
    }
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    pickFile(e.dataTransfer.files?.[0] ?? null);
  };

  const handleLoadSample = () => {
    const canvas = document.createElement("canvas");
    canvas.width = 600;
    canvas.height = 600;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.fillStyle = "#2b4c7e";
      ctx.fillRect(0, 0, 600, 600);
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 30px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("RE-THREAD SAMPLE", 300, 280);
      ctx.font = "20px sans-serif";
      ctx.fillText("Navy Cotton Chino", 300, 325);
    }
    canvas.toBlob(
      (blob) => {
        if (blob) pickFile(new File([blob], "sample_garment.jpg", { type: "image/jpeg" }));
      },
      "image/jpeg",
      0.92
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please add a photo of your garment first.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      setLoadingStep("Preprocessing your photo...");
      const formData = new FormData();
      formData.append("garment_images", file);

      setLoadingStep("Classifying material, wear condition & defects...");
      const result = await analyzeGarment(formData);

      setLoadingStep("Analysis complete!");
      onAnalysisComplete(result, previewUrl ? { front: previewUrl } : {});
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to analyze garment.");
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      {/* Header */}
      <div className="mb-8">
        <span className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-line bg-white px-3 py-1 text-xs font-semibold text-muted">
          <Camera className="h-3.5 w-3.5" />
          Circular Garment Scanner
        </span>
        <h1 className="text-3xl font-extrabold tracking-tight text-charcoal sm:text-4xl">
          Let&apos;s get to know your garment.
        </h1>
        <p className="mt-2 max-w-xl text-base text-muted">
          Upload a photo to explore its fabric, condition, and possible next steps.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-5 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" />
          <div>{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="rounded-3xl border border-line bg-white p-4 shadow-soft sm:p-6">
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              pickFile(e.target.files?.[0] ?? null);
              e.target.value = "";
            }}
          />

          {previewUrl ? (
            /* Preview state */
            <div className="relative overflow-hidden rounded-2xl border border-line bg-mist">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewUrl}
                alt="Your garment"
                className="mx-auto max-h-[460px] w-full object-contain"
              />
              <div className="absolute right-3 top-3 flex gap-2">
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="inline-flex items-center gap-1.5 rounded-full bg-white/90 px-3 py-1.5 text-xs font-semibold text-charcoal shadow-sm backdrop-blur hover:bg-white"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  Change
                </button>
                <button
                  type="button"
                  onClick={() => pickFile(null)}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white/90 text-charcoal shadow-sm backdrop-blur hover:bg-white hover:text-rose-600"
                  title="Remove photo"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          ) : (
            /* Empty drop zone */
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              className={`flex min-h-[360px] flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
                dragging ? "border-forest bg-brand-50" : "border-line bg-white"
              }`}
            >
              <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-mist text-forest">
                <Upload className="h-6 w-6" />
              </div>
              <h2 className="text-2xl font-medium text-charcoal">Drop your garment photo here</h2>
              <p className="mt-1 text-sm text-muted">or browse files from your device.</p>

              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                className="mt-6 inline-flex items-center gap-2 rounded-full bg-forest px-7 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-evergreen"
              >
                <Camera className="h-4 w-4" />
                Choose Photo
              </button>

              <p className="mt-5 text-xs text-muted">JPG, PNG or WebP · up to {MAX_MB} MB</p>
              <p className="mt-1 max-w-sm text-xs text-muted">
                For the best result, use a clear, well-lit photo of the whole garment laid flat.
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="mt-5 flex flex-col items-center gap-3">
            <button
              type="submit"
              disabled={loading || !file}
              className={`flex min-w-[260px] items-center justify-center gap-2 rounded-full px-8 py-3.5 text-sm font-bold transition-all ${
                loading || !file
                  ? "cursor-not-allowed bg-mist text-ghost"
                  : "bg-forest text-white shadow-md hover:bg-evergreen"
              }`}
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>{loadingStep || "Analyzing garment..."}</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Analyze Garment</span>
                </>
              )}
            </button>

            {!file && !loading && (
              <button
                type="button"
                onClick={handleLoadSample}
                className="text-xs font-medium text-muted underline-offset-4 hover:text-charcoal hover:underline"
              >
                No photo handy? Try a sample garment (demo)
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
};