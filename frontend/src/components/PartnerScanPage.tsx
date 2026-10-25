"use client";

import React, { useState } from "react";
import {
  QrCode,
  CheckCircle2,
  Building2,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  AlertCircle,
  FileText,
  Sparkles,
} from "lucide-react";
import { confirmOutcome } from "@/lib/api";

const PUNE_FACILITIES = [
  { id: 1, name: "EcoReclaim Pune - FC Road", neighborhood: "FC Road, Shivajinagar" },
  { id: 2, name: "Rethread Hub Kothrud", neighborhood: "Kothrud Depot" },
  { id: 3, name: "SwapStyle Pune Camp", neighborhood: "MG Road, Camp" },
  { id: 4, name: "Deccan Fabric Upcyclers", neighborhood: "Deccan Gymkhana" },
  { id: 5, name: "Viman Nagar Textile Bank", neighborhood: "Viman Nagar" },
  { id: 6, name: "Hadapsar Circular Mending", neighborhood: "Hadapsar" },
  { id: 7, name: "PCMC Green Threads Pimpri", neighborhood: "Pimpri Chinchwad" },
  { id: 8, name: "Aundh Eco-Stitch Collective", neighborhood: "Aundh" },
  { id: 9, name: "Baner Zero-Waste Closet", neighborhood: "Baner" },
  { id: 10, name: "Swargate Community Closet", neighborhood: "Swargate" },
  { id: 11, name: "Koregaon Park Vintage Exchange", neighborhood: "Koregaon Park" },
  { id: 12, name: "Katraj Fiber Recovery Hub", neighborhood: "Katraj" },
  { id: 13, name: "Hinjawadi IT Eco-Drop", neighborhood: "Hinjawadi Phase 1" },
  { id: 14, name: "Magarpatta Circular Station", neighborhood: "Magarpatta City" },
  { id: 15, name: "Pune Station Care & Repair", neighborhood: "Pune Railway Station" },
];

const PATHWAYS = [
  { id: "reuse_resell", label: "Reuse / Resell", color: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  { id: "repair", label: "Repair & Mending", color: "bg-teal-100 text-teal-800 border-teal-300" },
  { id: "donate", label: "Community Donation", color: "bg-blue-100 text-blue-800 border-blue-300" },
  { id: "recycle", label: "Fiber Recycling", color: "bg-purple-100 text-purple-800 border-purple-300" },
  { id: "brand_takeback", label: "Brand Take-Back", color: "bg-amber-100 text-amber-800 border-amber-300" },
];

export const PartnerScanPage: React.FC = () => {
  const [qrId, setQrId] = useState("");
  const [facilityId, setFacilityId] = useState(1);
  const [pathway, setPathway] = useState("reuse_resell");
  const [notes, setNotes] = useState("Intake inspection verified at drop-off hub.");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmedResult, setConfirmedResult] = useState<{
    status: string;
    qr_id: string;
    message: string;
    timestamp: string;
  } | null>(null);

  const handleScanSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!qrId.trim()) {
      setError("Please provide a valid QR ID.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const res = await confirmOutcome(qrId.trim(), facilityId, pathway, notes);
      setConfirmedResult({
        ...res,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Confirmation failed.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setQrId("");
    setConfirmedResult(null);
    setError(null);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Title */}
      <div className="text-center mb-8">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 mb-2">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          Partner Intake Portal
        </span>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Drop-Off Partner QR Scanner
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-xl mx-auto">
          Rule #7 Enforced: Recommendations are intentions; only partner-scanned drop-offs count as verified circular outcomes.
        </p>
      </div>

      {!confirmedResult ? (
        <form
          onSubmit={handleScanSubmit}
          className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6"
        >
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          {/* QR Code Input */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Garment QR Identifier
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <QrCode className="w-5 h-5" />
              </div>
              <input
                type="text"
                value={qrId}
                onChange={(e) => setQrId(e.target.value)}
                placeholder="Scan or paste QR ID (e.g. qr_4b7f92e10c)"
                className="w-full pl-10 pr-24 py-3 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                required
              />
              <button
                type="button"
                onClick={() => setQrId(`qr_${Math.random().toString(36).substring(2, 10)}`)}
                className="absolute inset-y-1.5 right-1.5 px-3 rounded-lg text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 transition-colors"
              >
                Simulate Scan
              </button>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Printed on the circular passport tag generated by RE-THREAD.
            </p>
          </div>

          {/* Partner Facility Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Drop-off Facility (Pune Network)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Building2 className="w-5 h-5" />
              </div>
              <select
                value={facilityId}
                onChange={(e) => setFacilityId(Number(e.target.value))}
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              >
                {PUNE_FACILITIES.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name} ({f.neighborhood})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Confirmed Pathway Selection */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Physical Outcome Verified
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {PATHWAYS.map((p) => {
                const isSelected = pathway === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setPathway(p.id)}
                    className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                      isSelected
                        ? `${p.color} ring-2 ring-emerald-500 shadow-xs font-bold`
                        : "border-slate-200 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Intake Notes */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Facility Intake Notes (Optional)
            </label>
            <div className="relative">
              <div className="absolute top-3 left-3 pointer-events-none text-slate-400">
                <FileText className="w-4 h-4" />
              </div>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="Condition checked, garment accepted for sorting..."
                className="w-full pl-10 pr-3 py-2.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 shadow-md shadow-emerald-600/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {loading ? (
              <span>Confirming Outcome in DB...</span>
            ) : (
              <>
                <span>Record Real Circular Outcome</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      ) : (
        /* Confirmed Outcome Certificate Card */
        <div className="rounded-2xl border-2 border-emerald-400 bg-white p-6 shadow-md text-center space-y-5 animate-in fade-in zoom-in-95 duration-300">
          <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto shadow-inner">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          <div>
            <span className="text-[10px] font-extrabold uppercase tracking-widest px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              Verified Circular Transaction
            </span>
            <h2 className="text-2xl font-black text-slate-900 mt-2">
              Lifecycle Drop-off Confirmed!
            </h2>
            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
              This garment has physically arrived at an authorized circular hub. Impact savings are now certified in the Pune circular registry.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-left text-xs space-y-2 max-w-md mx-auto font-mono">
            <div className="flex justify-between">
              <span className="text-slate-400">QR ID:</span>
              <span className="font-bold text-slate-800">{confirmedResult.qr_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Outcome:</span>
              <span className="font-bold text-emerald-700 uppercase">{pathway.replace("_", " ")}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Hub:</span>
              <span className="font-medium text-slate-700 truncate max-w-[200px]">
                {PUNE_FACILITIES.find((f) => f.id === facilityId)?.name}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Time:</span>
              <span className="text-slate-600">{confirmedResult.timestamp}</span>
            </div>
          </div>

          <button
            type="button"
            onClick={handleReset}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Scan Next Garment</span>
          </button>
        </div>
      )}
    </div>
  );
};
