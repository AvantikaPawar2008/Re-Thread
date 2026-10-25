"use client";

import React, { useEffect, useState } from "react";
import { Sparkles, Recycle, BarChart3, MapPin, Activity, QrCode } from "lucide-react";
import { checkBackendHealth } from "@/lib/api";

interface NavbarProps {
  activeTab: "scan" | "dashboard" | "facilities" | "partner";
  onTabChange: (tab: "scan" | "dashboard" | "facilities" | "partner") => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange }) => {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const ping = async () => {
      try {
        const res = await checkBackendHealth();
        setBackendOnline(res.status === "ok");
      } catch {
        setBackendOnline(false);
      }
    };
    ping();
    const interval = setInterval(ping, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-white/85 border-b border-emerald-100 shadow-xs">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-18 flex items-center justify-between">
        {/* Logo & Tagline */}
        <div
          onClick={() => onTabChange("scan")}
          className="cursor-pointer flex items-center gap-3 group"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-500/20 group-hover:scale-105 transition-transform">
            <Recycle className="w-5 h-5 animate-spin-slow" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-emerald-800 to-teal-700 bg-clip-text text-transparent">
                RE-THREAD
              </span>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 uppercase tracking-wider">
                Circular AI
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block font-medium">
              Your Clothes. Your Stories. Their Next Chapter.
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => onTabChange("scan")}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === "scan"
                ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/30"
                : "text-slate-600 hover:text-emerald-700 hover:bg-emerald-50"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Garment AI</span>
          </button>

          <button
            onClick={() => onTabChange("dashboard")}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === "dashboard"
                ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/30"
                : "text-slate-600 hover:text-emerald-700 hover:bg-emerald-50"
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Impact</span>
          </button>

          <button
            onClick={() => onTabChange("facilities")}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === "facilities"
                ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/30"
                : "text-slate-600 hover:text-emerald-700 hover:bg-emerald-50"
            }`}
          >
            <MapPin className="w-4 h-4" />
            <span>Pune Hubs</span>
          </button>

          <button
            onClick={() => onTabChange("partner")}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === "partner"
                ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/30"
                : "text-slate-600 hover:text-emerald-700 hover:bg-emerald-50"
            }`}
          >
            <QrCode className="w-4 h-4" />
            <span>Partner Scan</span>
          </button>
        </nav>

        {/* Backend Connectivity Status Indicator */}
        <div className="hidden md:flex items-center gap-2 text-xs font-medium px-2.5 py-1 rounded-full bg-slate-50 border border-slate-200">
          <Activity className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-500">API:</span>
          {backendOnline === null ? (
            <span className="text-amber-500 flex items-center gap-1">Checking...</span>
          ) : backendOnline ? (
            <span className="text-emerald-600 font-semibold flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Connected
            </span>
          ) : (
            <span className="text-rose-600 font-semibold flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              Offline
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
