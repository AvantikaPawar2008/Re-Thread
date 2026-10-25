import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RE-THREAD · AI-Powered Circular Fashion Decision Platform",
  description:
    "Photograph unwanted clothing to assess material, wear, and defects with computer vision. Get explained circular recommendations for reuse, repair, donation, recycling, and brand take-back.",
  keywords: [
    "circular fashion",
    "textile recycling",
    "garment repair",
    "sustainable fashion",
    "AI clothing analysis",
    "Pune textile drop-off",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
