"use client";

import React, { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { UploadSection } from "@/components/UploadSection";
import { AnalysisResultsSection } from "@/components/AnalysisResultsSection";
import { RecommendationsSection } from "@/components/RecommendationsSection";
import { ImpactDashboard } from "@/components/ImpactDashboard";
import { FacilitiesView } from "@/components/FacilitiesView";
import { PartnerScanPage } from "@/components/PartnerScanPage";
import { AnalyzeResponse, RecommendResponse } from "@/types";
import { Recycle, Sparkles } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"scan" | "dashboard" | "facilities" | "partner">("scan");
  const [scanStep, setScanStep] = useState<"upload" | "analysis" | "recommendations">("upload");

  const [analysisResult, setAnalysisResult] = useState<AnalyzeResponse | null>(null);
  const [previewImages, setPreviewImages] = useState<{ [key: string]: string }>({});
  const [recommendations, setRecommendations] = useState<RecommendResponse | null>(null);
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number }>({
    lat: 18.5204,
    lon: 73.8567,
  });

  const handleAnalysisComplete = (
    result: AnalyzeResponse,
    previews: { [key: string]: string }
  ) => {
    setAnalysisResult(result);
    setPreviewImages(previews);
    setScanStep("analysis");
  };

  const handleRecommendationsReady = (
    recs: RecommendResponse,
    loc: { lat: number; lon: number }
  ) => {
    setRecommendations(recs);
    setUserLocation(loc);
    setScanStep("recommendations");
  };

  const handleResetScan = () => {
    setAnalysisResult(null);
    setPreviewImages({});
    setRecommendations(null);
    setScanStep("upload");
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50/70 text-slate-900 font-sans selection:bg-emerald-100 selection:text-emerald-900">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
        }}
      />

      {/* Main Content Area */}
      <main className="flex-1 pb-16">
        {activeTab === "scan" && (
          <>
            {scanStep === "upload" && (
              <UploadSection onAnalysisComplete={handleAnalysisComplete} />
            )}

            {scanStep === "analysis" && analysisResult && (
              <AnalysisResultsSection
                analysis={analysisResult}
                previewImages={previewImages}
                onRecommendationsReady={handleRecommendationsReady}
                onReset={handleResetScan}
              />
            )}

            {scanStep === "recommendations" && recommendations && (
              <RecommendationsSection
                recommendations={recommendations}
                userLocation={userLocation}
                onReset={handleResetScan}
              />
            )}
          </>
        )}

        {activeTab === "dashboard" && <ImpactDashboard />}

        {activeTab === "facilities" && <FacilitiesView />}

        {activeTab === "partner" && <PartnerScanPage />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-8 px-4 text-xs text-slate-500">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-slate-800">RE-THREAD</span>
            <span>·</span>
            <span className="italic">
              &ldquo;Your Clothes. Your Stories. Their Next Chapter.&rdquo;
            </span>
          </div>

          <div className="flex items-center gap-4 text-slate-400">
            <span>AI for Circular Economy</span>
            <span>·</span>
            <span>Sustainable Fashion Intelligence</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
