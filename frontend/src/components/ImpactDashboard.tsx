"use client";

import React from "react";
import {
  Droplets,
  Leaf,
  Recycle,
  Sparkles,
  Award,
  ArrowUpRight,
  ShieldCheck,
  CheckCircle2,
  Gift,
  Building,
} from "lucide-react";

export const ImpactDashboard: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Title & Tagline */}
      <div className="mb-8">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 mb-2">
          <Recycle className="w-3.5 h-3.5 text-emerald-600" />
          Circular Impact Dashboard
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Your Circular Fashion Journey
        </h1>
        <p className="text-sm text-slate-500 mt-1 font-medium">
          &ldquo;Your Clothes. Your Stories. Their Next Chapter.&rdquo;
        </p>
      </div>

      {/* Top 4 KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Garments Diverted</span>
            <span className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <Recycle className="w-4 h-4" />
            </span>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">42</div>
          <div className="flex items-center gap-1 text-xs text-emerald-700 font-semibold mt-1">
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>+12 this month</span>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Water Conserved</span>
            <span className="p-2 rounded-xl bg-cyan-50 text-cyan-600">
              <Droplets className="w-4 h-4" />
            </span>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">114,200 L</div>
          <div className="text-xs text-slate-500 mt-1">
            Equal to ~1,420 household showers
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Carbon Avoided</span>
            <span className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <Leaf className="w-4 h-4" />
            </span>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">890 kg CO₂</div>
          <div className="text-xs text-slate-500 mt-1">
            Equal to driving ~3,600 km in a car
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Confirmed Intake</span>
            <span className="p-2 rounded-xl bg-purple-50 text-purple-600">
              <ShieldCheck className="w-4 h-4" />
            </span>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">90.5%</div>
          <div className="text-xs text-purple-700 font-semibold mt-1">
            38/42 QR-confirmed outcomes
          </div>
        </div>
      </div>

      {/* Pathways Distribution & Active Brand Rewards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">
        {/* Pathway Breakdown */}
        <div className="lg:col-span-7 rounded-3xl border border-slate-200 bg-white p-6 shadow-xs">
          <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-600" />
            Lifetime Pathway Breakdown
          </h2>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-bold text-slate-700 mb-1">
                <span>Repaired & Restored</span>
                <span>16 items (38%)</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full rounded-full bg-amber-500" style={{ width: "38%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-bold text-slate-700 mb-1">
                <span>Donated to Community (Goonj & Goodwill)</span>
                <span>12 items (29%)</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full rounded-full bg-blue-500" style={{ width: "29%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-bold text-slate-700 mb-1">
                <span>Brand Take-Back (Vouchers Earned)</span>
                <span>8 items (19%)</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full rounded-full bg-purple-500" style={{ width: "19%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-bold text-slate-700 mb-1">
                <span>Industrial Fiber Recycled (Swach Pune)</span>
                <span>6 items (14%)</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full rounded-full bg-emerald-600" style={{ width: "14%" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Brand Rewards Wallet */}
        <div className="lg:col-span-5 rounded-3xl border border-slate-200 bg-white p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Gift className="w-4 h-4 text-purple-600" />
                Brand Rewards Wallet
              </h2>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-800">
                2 Active
              </span>
            </div>

            <div className="space-y-3">
              <div className="p-3.5 rounded-2xl bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200">
                <div className="flex items-center justify-between font-bold text-xs text-purple-900 mb-1">
                  <span>H&M Phoenix Marketcity</span>
                  <span className="text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">15% OFF</span>
                </div>
                <p className="text-[11px] text-purple-700">
                  Earned via QR intake scan on unwanted denim jacket. Valid until Dec 2026.
                </p>
                <div className="mt-2 font-mono text-[10px] text-purple-900 bg-white/70 px-2 py-1 rounded w-fit">
                  CODE: HM-RETHREAD-928A
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200">
                <div className="flex items-center justify-between font-bold text-xs text-blue-900 mb-1">
                  <span>Levi&apos;s Pavillion Store</span>
                  <span className="text-blue-700 bg-blue-100 px-2 py-0.5 rounded">Free Repair</span>
                </div>
                <p className="text-[11px] text-blue-700">
                  Customization or hem repair credit at The Pavillion Tailor Shop.
                </p>
              </div>
            </div>
          </div>

          <p className="text-[11px] text-slate-400 mt-4">
            Coupons are generated exclusively through verified drop-off QR scans.
          </p>
        </div>
      </div>

      {/* Pune City Circular Network Activity & Ward Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xs">
          <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Building className="w-4 h-4 text-emerald-600" />
            Pune Municipal Ward Progress (PMC & PCMC)
          </h2>
          <div className="space-y-3">
            {[
              { ward: "FC Road / Shivajinagar", collected: "4,120 kg", rate: "92% diverted" },
              { ward: "Kothrud & Karve Nagar", collected: "3,890 kg", rate: "88% diverted" },
              { ward: "Camp & MG Road", collected: "2,940 kg", rate: "85% diverted" },
              { ward: "Viman Nagar & Kalyani Nagar", collected: "3,150 kg", rate: "91% diverted" },
              { ward: "Hadapsar & Magarpatta", collected: "2,420 kg", rate: "84% diverted" },
              { ward: "Pimpri-Chinchwad (PCMC)", collected: "4,680 kg", rate: "89% diverted" },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-50">
                <span className="font-semibold text-slate-700">{item.ward}</span>
                <div className="flex items-center gap-3">
                  <span className="text-slate-500 font-mono">{item.collected}</span>
                  <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded-full text-[11px]">
                    {item.rate}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Municipal Zero-Waste Mission Target */}
        <div className="rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-900 to-teal-950 text-white p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-2">
              <Award className="w-4 h-4" />
              <span>Municipal Circular Mission</span>
            </div>
            <h3 className="text-xl font-black text-white mb-2">
              Zero-Textile-Waste Initiative
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Targeting 15,000 metric tons of unwanted post-consumer garments diverted from Urali Devachi landfills by combining edge computer vision diagnostics, automated fiber OCR, and localized Pune municipal repair cooperatives.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800">
            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1.5">
              <span>City Milestone Progress</span>
              <span className="text-emerald-400 font-bold">68.4% Achieved</span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
              <div className="h-full rounded-full bg-emerald-400" style={{ width: "68.4%" }} />
            </div>
          </div>
        </div>
      </div>

      {/* Recent QR Confirmed Activity Feed */}
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xs">
        <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          Recent Verified Drop-Offs (Pune Network)
        </h2>

        <div className="divide-y divide-slate-100">
          <div className="py-3 flex items-center justify-between text-xs">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
                RP
              </div>
              <div>
                <p className="font-bold text-slate-800">Navy Cotton Chino Trousers</p>
                <p className="text-slate-500">FC Road Master Tailors & Alterations · Confirmed Repair</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-emerald-700 font-semibold">+3,100 L water</span>
              <p className="text-slate-400 text-[10px]">Today, 4:15 PM</p>
            </div>
          </div>

          <div className="py-3 flex items-center justify-between text-xs">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
                DN
              </div>
              <div>
                <p className="font-bold text-slate-800">Embroidered Cotton Kurta</p>
                <p className="text-slate-500">Goonj Dropping Centre (Kothrud) · Confirmed Donation</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-emerald-700 font-semibold">+3,900 L water</span>
              <p className="text-slate-400 text-[10px]">Yesterday</p>
            </div>
          </div>

          <div className="py-3 flex items-center justify-between text-xs">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center font-bold">
                TB
              </div>
              <div>
                <p className="font-bold text-slate-800">Fleece Sportswear Jacket</p>
                <p className="text-slate-500">Decathlon Sports Gear Takeback (Amanora) · Brand Store</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-emerald-700 font-semibold">+875 L water</span>
              <p className="text-slate-400 text-[10px]">3 days ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
