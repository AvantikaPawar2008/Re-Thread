"use client";

import React, { useState } from "react";
import {
  Camera,
  Upload,
  X,
  Sparkles,
  AlertCircle,
  FileText,
  Eye,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import { AnalyzeResponse } from "@/types";
import { analyzeGarment } from "@/lib/api";

interface UploadSectionProps {
  onAnalysisComplete: (result: AnalyzeResponse, previewImages: { [key: string]: string }) => void;
}

interface PhotoSlot {
  id: string;
  title: string;
  subtitle: string;
  required: boolean;
  file: File | null;
  previewUrl: string | null;
}

export const UploadSection: React.FC<UploadSectionProps> = ({ onAnalysisComplete }) => {
  const [slots, setSlots] = useState<{ [key: string]: PhotoSlot }>({
    front: {
      id: "front",
      title: "1. Full Garment",
      subtitle: "Full front or back view laid flat or hanging",
      required: true,
      file: null,
      previewUrl: null,
    },
    texture: {
      id: "texture",
      title: "2. Fabric Texture",
      subtitle: "Close-up macro photo of the textile weave",
      required: false,
      file: null,
      previewUrl: null,
    },
    damage: {
      id: "damage",
      title: "3. Damage Close-up",
      subtitle: "Zoomed view of tears, stains, pilling or wear",
      required: false,
      file: null,
      previewUrl: null,
    },
    tag: {
      id: "tag",
      title: "Care Label (Optional)",
      subtitle: "Wash care tag showing brand & composition",
      required: false,
      file: null,
      previewUrl: null,
    },
  });

  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (id: string, file: File | null) => {
    setError(null);
    if (!file) {
      setSlots((prev) => ({
        ...prev,
        [id]: { ...prev[id], file: null, previewUrl: null },
      }));
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    setSlots((prev) => ({
      ...prev,
      [id]: { ...prev[id], file, previewUrl },
    }));
  };

  const handleLoadSample = () => {
    setError(null);
    // Create simulated canvas mock images for quick 1-click testing
    const createSampleFile = (name: string, color: string, label: string): File => {
      const canvas = document.createElement("canvas");
      canvas.width = 400;
      canvas.height = 400;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.fillStyle = color;
        ctx.fillRect(0, 0, 400, 400);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 24px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("RE-THREAD SAMPLE", 200, 180);
        ctx.font = "16px sans-serif";
        ctx.fillText(label, 200, 220);
      }
      const dataUrl = canvas.toDataURL("image/jpeg");
      const blobBin = atob(dataUrl.split(",")[1]);
      const array = [];
      for (let i = 0; i < blobBin.length; i++) {
        array.push(blobBin.charCodeAt(i));
      }
      const blob = new Blob([new Uint8Array(array)], { type: "image/jpeg" });
      return new File([blob], name, { type: "image/jpeg" });
    };

    const frontFile = createSampleFile("sample_front.jpg", "#2b4c7e", "Navy Cotton Chino");
    const textureFile = createSampleFile("sample_texture.jpg", "#386fa4", "Twill Weave 2x1");
    const damageFile = createSampleFile("sample_damage.jpg", "#59a5d8", "Pocket Seam Tear 2cm");
    const tagFile = createSampleFile("sample_tag.jpg", "#133c55", "H&M 60% Cotton 40% Poly");

    setSlots({
      front: { ...slots.front, file: frontFile, previewUrl: URL.createObjectURL(frontFile) },
      texture: { ...slots.texture, file: textureFile, previewUrl: URL.createObjectURL(textureFile) },
      damage: { ...slots.damage, file: damageFile, previewUrl: URL.createObjectURL(damageFile) },
      tag: { ...slots.tag, file: tagFile, previewUrl: URL.createObjectURL(tagFile) },
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!slots.front.file) {
      setError("Please provide at least the primary garment photo (Full Garment).");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      setLoadingStep("Preprocessing garment photographs...");
      const formData = new FormData();

      // Collect garment images
      if (slots.front.file) formData.append("garment_images", slots.front.file);
      if (slots.texture.file) formData.append("garment_images", slots.texture.file);
      if (slots.damage.file) formData.append("garment_images", slots.damage.file);

      // Care tag image if provided
      if (slots.tag.file) {
        formData.append("tag_image", slots.tag.file);
      }

      setLoadingStep("Classifying material, wear condition & defect regions...");
      const result = await analyzeGarment(formData);

      // Collect preview URLs for display on results view
      const previews: { [key: string]: string } = {};
      Object.keys(slots).forEach((key) => {
        if (slots[key].previewUrl) previews[key] = slots[key].previewUrl!;
      });

      setLoadingStep("Analysis complete!");
      onAnalysisComplete(result, previews);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to analyze garment.";
      setError(msg);
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Intro Header */}
      <div className="text-center mb-8">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 mb-3">
          <Camera className="w-3.5 h-3.5" />
          Circular Garment Scanner
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Photograph Your Garment
        </h1>
        <p className="mt-2 text-base text-slate-600 max-w-xl mx-auto">
          Take multi-angle photos to assess material, wear, and defects. Add the care tag for brand rewards and take-back routing.
        </p>

        {/* 1-Click Sample Button for Fast Testing */}
        <div className="mt-4 flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={handleLoadSample}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors border border-slate-200 shadow-2xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            Load Sample Garment (Demo)
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Analysis Error: </span>
            {error}
          </div>
        </div>
      )}

      {/* Photo Slots Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {Object.values(slots).map((slot) => {
            const isTagSlot = slot.id === "tag";
            return (
              <div
                key={slot.id}
                className={`relative rounded-2xl border-2 transition-all p-4 ${
                  slot.file
                    ? "border-emerald-500 bg-emerald-50/20"
                    : isTagSlot
                    ? "border-dashed border-slate-300 bg-slate-50/60 hover:border-slate-400"
                    : slot.required
                    ? "border-dashed border-emerald-300 bg-emerald-50/10 hover:border-emerald-400"
                    : "border-dashed border-slate-300 bg-slate-50/40 hover:border-slate-400"
                }`}
              >
                {/* Header of Slot */}
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-800">
                        {slot.title}
                      </span>
                      {slot.required ? (
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 uppercase">
                          Required
                        </span>
                      ) : (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-200 text-slate-600 uppercase">
                          Optional
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{slot.subtitle}</p>
                  </div>
                  {slot.file && (
                    <button
                      type="button"
                      onClick={() => handleFileChange(slot.id, null)}
                      className="p-1 rounded-full bg-slate-200 hover:bg-rose-100 hover:text-rose-600 text-slate-600 transition-colors"
                      title="Remove photo"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>

                {/* Slot Body: Preview or Upload Control */}
                {slot.previewUrl ? (
                  <div className="relative rounded-xl overflow-hidden aspect-4/3 bg-slate-900 border border-slate-200">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={slot.previewUrl}
                      alt={slot.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-xs text-[11px] text-white font-medium flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      Attached
                    </div>
                  </div>
                ) : (
                  <label className="flex flex-col items-center justify-center aspect-4/3 rounded-xl border border-slate-200/80 bg-white hover:bg-slate-50 cursor-pointer transition-colors p-4 text-center group">
                    <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                      {isTagSlot ? (
                        <FileText className="w-6 h-6" />
                      ) : (
                        <Upload className="w-6 h-6" />
                      )}
                    </div>
                    <span className="text-xs font-semibold text-slate-700">
                      Tap or drag photo here
                    </span>
                    <span className="text-[11px] text-slate-400 mt-1">
                      JPEG, PNG or WebP up to 10MB
                    </span>
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0] || null;
                        handleFileChange(slot.id, file);
                      }}
                    />
                  </label>
                )}
              </div>
            );
          })}
        </div>

        {/* Informative Guidance Banner */}
        <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-xs text-amber-800 flex items-start gap-2.5">
          <Eye className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <p>
            <strong className="font-semibold">Vision First Architecture: </strong>
            Our AI uses the photos as the primary source for fabric material and condition. The care tag acts as a cross-check and unlocks brand take-back vouchers. If the tag is faded or missing, the analysis proceeds seamlessly!
          </p>
        </div>

        {/* Submit Button */}
        <div className="flex flex-col items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={loading || !slots.front.file}
            className={`w-full sm:w-auto min-w-[280px] px-8 py-3.5 rounded-xl font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 ${
              loading || !slots.front.file
                ? "bg-slate-200 text-slate-400 cursor-not-allowed shadow-none"
                : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/30 hover:scale-[1.01]"
            }`}
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>{loadingStep || "Analyzing Garment..."}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Run Garment AI Analysis</span>
              </>
            )}
          </button>
          {!slots.front.file && (
            <span className="text-xs text-slate-400 font-medium">
              Please attach at least the primary garment photo to proceed.
            </span>
          )}
        </div>
      </form>
    </div>
  );
};
