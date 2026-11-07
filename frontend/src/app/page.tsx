"use client";

import React, { useState } from "react";
import { Navbar, type Tab } from "@/components/Navbar";
import { FloatingLabels } from "@/components/FloatingLabels";
import { UploadSection } from "@/components/UploadSection";
import { AnalysisResultsSection } from "@/components/AnalysisResultsSection";
import { RecommendationsSection } from "@/components/RecommendationsSection";
import { ImpactDashboard } from "@/components/ImpactDashboard";
import { FacilitiesView } from "@/components/FacilitiesView";
import { PartnerScanPage } from "@/components/PartnerScanPage";
import FabricGuide from "@/components/FabricGuide";
import { FabricIdentifier } from "@/components/FabricIdentifier";
import { Landing } from "@/components/Landing";
import { AnalyzeResponse, RecommendResponse } from "@/types";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("scan");
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

  const footerLinks: { label: string; tab: Tab }[] = [
    { label: "Analyze Garment", tab: "scan" },
    { label: "Fabric Guide", tab: "guide" },
    { label: "Sustainability Impact", tab: "dashboard" },
    { label: "Pune Drop-off Hubs", tab: "facilities" },
    { label: "Partner Scan", tab: "partner" },
  ];

  const goToTab = (tab: Tab) => {
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleResetScan = () => {
    setAnalysisResult(null);
    setPreviewImages({});
    setRecommendations(null);
    setScanStep("upload");
  };

  return (
    <div className="min-h-screen flex flex-col bg-ivory text-charcoal">
      <FloatingLabels />

      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content Area (top padding leaves room for the floating navbar) */}
      <main className="relative z-20 flex-1 pb-16 pt-20">
        {activeTab === "scan" && (
          <>
            {scanStep === "upload" && (
              <>
                <Landing />
                <UploadSection onAnalysisComplete={handleAnalysisComplete} />
                <FabricIdentifier />
              </>
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

        {activeTab === "dashboard" && (
          <ImpactDashboard
            summary="Keeping clothes in use for longer avoids most of their environmental footprint."
            metrics={[
              {
                id: "water",
                label: "Water",
                value: 2700,
                unit: "L",
                equivalent: "≈ 13 showers",
                share: 0.55,
                confidence: "medium",
              },
              {
                id: "carbon",
                label: "Carbon",
                value: 6.5,
                unit: "kg CO₂e",
                equivalent: "≈ 40 km by petrol car",
                share: 0.3,
                confidence: "medium",
              },
              {
                id: "waste",
                label: "Textile waste avoided",
                value: 0.25,
                unit: "kg",
                equivalent: "≈ 1 shirt kept out of landfill",
                share: 0.15,
                confidence: "high",
              },
            ]}
            methodologyNote="Figures are model estimates based on average garment data, not measurements of your specific item."
            onNextAction={() => goToTab("scan")}
          />
        )}
        {activeTab === "facilities" && <FacilitiesView />}
        {activeTab === "partner" && <PartnerScanPage />}
        {activeTab === "guide" && <FabricGuide />}
      </main>

      {/* Footer */}
      <footer
        className="relative z-20 mx-3 mb-3 rounded-3xl bg-forest text-white sm:mx-5"
        aria-label="Site footer"
      >
        <div className="mx-auto grid max-w-[1200px] gap-8 px-6 py-10 text-sm md:grid-cols-12">
          <div className="md:col-span-5">
            <p className="text-3xl font-bold tracking-tight">Re-Thread.</p>
            <p className="mt-2 italic text-white/80">
              &ldquo;Your Clothes. Your Stories. Their Next Chapter.&rdquo;
            </p>
            <p className="mt-4 max-w-sm leading-relaxed text-white/75">
              An AI-powered circular fashion platform that helps you decide whether a garment should be
              resold, repaired, donated, recycled or returned to its brand.
            </p>
          </div>

          <nav className="flex flex-col gap-3 md:col-span-3" aria-label="Footer">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60">Platform</p>
            {footerLinks.map((link) => (
              <button
                key={link.tab}
                type="button"
                className="text-left text-white/85 transition-colors hover:text-white"
                onClick={() => goToTab(link.tab)}
              >
                {link.label}
              </button>
            ))}
          </nav>

          <div className="md:col-span-4">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60">Our approach</p>
            <p className="mt-3 leading-relaxed text-white/80">
              Keeping textiles out of landfill starts with an honest answer. Every recommendation is
              explained, and uncertain results are labelled as uncertain.
            </p>
            <p className="mt-3 leading-relaxed text-white/80">
              Predictions and impact figures are model estimates, not guarantees.
            </p>
            <a
              href="https://github.com/AvantikaPawar2008/Re-Thread"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-block rounded-md bg-black px-4 py-2 text-xs font-semibold uppercase tracking-wider text-white hover:bg-charcoal"
            >
              Project on GitHub
            </a>
          </div>
        </div>

        <div className="border-t border-white/15">
          <p className="mx-auto max-w-[1200px] px-6 py-4 text-xs text-white/60">
            Rethink. Reuse. Re-Thread. · Built with Next.js, FastAPI and PyTorch.
          </p>
        </div>
      </footer>
    </div>
  );
}