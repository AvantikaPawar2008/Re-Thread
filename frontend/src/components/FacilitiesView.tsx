"use client";

import React, { useState } from "react";
import {
  MapPin,
  Phone,
  Globe,
  Scissors,
  Heart,
  Recycle,
  Tag,
  Building,
  CheckCircle2,
} from "lucide-react";

interface FacilityItem {
  name: string;
  type: "repair" | "donation" | "recycling" | "brand_store";
  address: string;
  neighborhood: string;
  phone: string;
  website: string;
  materials: string;
  notes: string;
}

const PUNE_FACILITIES: FacilityItem[] = [
  {
    name: "FC Road Master Tailors & Alterations",
    type: "repair",
    address: "1194/1 Fergusson College Rd, Shivajinagar",
    neighborhood: "Shivajinagar / FC Road",
    phone: "+91-20-2553-1200",
    website: "https://fcroad-tailors.example.com",
    materials: "All fabrics, denim, shirts, trousers",
    notes: "Expert alterations, zipper replacements, patch mending, and resizing.",
  },
  {
    name: "Kothrud Garment Repair & Upcycling Studio",
    type: "repair",
    address: "Shop 4, Mayur Colony, Kothrud",
    neighborhood: "Kothrud",
    phone: "+91-20-2544-3321",
    website: "https://kothrudrepair.example.com",
    materials: "Cotton, wool, silk, denim",
    notes: "Specialises in darning, torn seam restoration, and denim reinforcement.",
  },
  {
    name: "Camp Leather & Heavy Garment Mending",
    type: "repair",
    address: "241 MG Road, Camp",
    neighborhood: "Camp / MG Road",
    phone: "+91-20-2613-8890",
    website: "https://campmending.example.com",
    materials: "Leather, heavy denim, jackets, coats",
    notes: "Heavy fabric and winterwear restoration specialists.",
  },
  {
    name: "Aundh Needlecraft & Restyling Studio",
    type: "repair",
    address: "ITI Road, Near Parihar Chowk, Aundh",
    neighborhood: "Aundh",
    phone: "+91-20-2588-4455",
    website: "https://aundhcraft.example.com",
    materials: "All textiles",
    notes: "Artisanal mending, embroidery patch repair, and garment transformation.",
  },
  {
    name: "Goonj Dropping Centre - Kothrud",
    type: "donation",
    address: "Plot 12, Ideal Colony, Paud Road, Kothrud",
    neighborhood: "Kothrud",
    phone: "+91-98220-11223",
    website: "https://goonj.org",
    materials: "Wearable everyday clothing, sarees, kurtas",
    notes: "Accepts clean wearable clothing for disaster relief and community development.",
  },
  {
    name: "Goodwill India Collection Point - Camp",
    type: "donation",
    address: "45 East Street, Near Camp Post Office",
    neighborhood: "Camp",
    phone: "+91-20-2634-1100",
    website: "https://goodwillindia.org",
    materials: "Adult and children apparel, shoes",
    notes: "Sorting and redistributing clean, wearable apparel to underprivileged families.",
  },
  {
    name: "Maher Ashram Garment Bank",
    type: "donation",
    address: "Wagholi-Pune Road, Bakori Phata",
    neighborhood: "Wagholi",
    phone: "+91-20-2705-0112",
    website: "https://maherashram.org",
    materials: "Everyday clothing, sweaters, cottons",
    notes: "Accepts everyday wear clothing for children, women and elders.",
  },
  {
    name: "Robin Hood Army Clothes Drop - Shivajinagar",
    type: "donation",
    address: "Modern College Rd, Shivajinagar",
    neighborhood: "Shivajinagar",
    phone: "+91-98901-44332",
    website: "https://robinhoodarmy.com",
    materials: "Clean wearable garments",
    notes: "Civic volunteer network redistributing wearable garments across community bastis.",
  },
  {
    name: "Swach Pune Material Recovery Facility",
    type: "recycling",
    address: "Hadapsar Industrial Estate, Hadapsar",
    neighborhood: "Hadapsar",
    phone: "+91-20-2681-7788",
    website: "https://swachcoop-pune.org",
    materials: "Worn, torn, or stained textiles",
    notes: "Waste picker cooperative sorting textiles for industrial fiber downcycling.",
  },
  {
    name: "PCMC Textile Segregation Hub",
    type: "recycling",
    address: "Sector 10, Bhosari, PCMC",
    neighborhood: "Bhosari / PCMC",
    phone: "+91-20-2712-4400",
    website: "https://pcmcindia.gov.in",
    materials: "All unwearable post-consumer textiles",
    notes: "Municipal mechanical sorting and fiber segregation center.",
  },
  {
    name: "Kasba Peth Traditional Textile Recyclers",
    type: "recycling",
    address: "122 Kasba Peth, Near Shaniwar Wada",
    neighborhood: "Kasba Peth / Old Pune",
    phone: "+91-98224-77112",
    website: "https://kasbapethrecyclers.example.com",
    materials: "Natural cottons and handlooms",
    notes: "Traditional chindi recyclers processing cotton rags for handmade paper.",
  },
  {
    name: "H&M In-Store Takeback - Phoenix Marketcity",
    type: "brand_store",
    address: "Ground Floor, Phoenix Marketcity, Viman Nagar",
    neighborhood: "Viman Nagar",
    phone: "+91-20-6689-0100",
    website: "https://www2.hm.com/en_in",
    materials: "Any brand, any condition",
    notes: "In-store garment collection box; gives 15% discount voucher per bag.",
  },
  {
    name: "Decathlon Sports Gear Takeback - Amanora",
    type: "brand_store",
    address: "Amanora Mall, Hadapsar-Kharadi Bypass",
    neighborhood: "Hadapsar / Amanora",
    phone: "+91-20-6726-2200",
    website: "https://decathlon.in",
    materials: "Synthetics, activewear, fleece",
    notes: "Accepts athletic wear, fleece, and synthetic jackets for recycling.",
  },
  {
    name: "Levi's Store & Tailor Hub - The Pavillion",
    type: "brand_store",
    address: "The Pavillion Mall, Senapati Bapat Road",
    neighborhood: "Senapati Bapat Road",
    phone: "+91-20-6642-1500",
    website: "https://levi.in",
    materials: "Denim and cotton apparel",
    notes: "In-store denim customization, repair, and take-back drop box.",
  },
];

export const FacilitiesView: React.FC = () => {
  const [filter, setFilter] = useState<string>("all");

  const filtered =
    filter === "all" ? PUNE_FACILITIES : PUNE_FACILITIES.filter((f) => f.type === filter);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 mb-2">
          <MapPin className="w-3.5 h-3.5 text-emerald-600" />
          Verified Drop-Off Network
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Pune Partner Drop-Off Hubs
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Explore eligible partner facilities in Pune for garment repair, donation, recycling, and brand take-back.
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {[
          { id: "all", label: "All Hubs (15)" },
          { id: "repair", label: "Repair Shops (4)" },
          { id: "donation", label: "Donation Centers (4)" },
          { id: "recycling", label: "Recycling Facilities (3)" },
          { id: "brand_store", label: "Brand Stores (3)" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filter === tab.id
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-slate-100 hover:bg-slate-200 text-slate-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Facilities Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((item, idx) => (
          <div
            key={idx}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <h2 className="font-extrabold text-slate-900 text-sm">
                  {item.name}
                </h2>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0 uppercase tracking-wide ${
                    item.type === "repair"
                      ? "bg-amber-100 text-amber-800"
                      : item.type === "donation"
                      ? "bg-blue-100 text-blue-800"
                      : item.type === "recycling"
                      ? "bg-slate-200 text-slate-800"
                      : "bg-purple-100 text-purple-800"
                  }`}
                >
                  {item.type.replace("_", " ")}
                </span>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-slate-600 mb-2">
                <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span>{item.address}</span>
              </div>

              <p className="text-xs text-slate-500 mb-3 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                {item.notes}
              </p>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span className="font-medium text-slate-700">Area: {item.neighborhood}</span>
              <span className="flex items-center gap-1 text-emerald-700 font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Active Intake
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
