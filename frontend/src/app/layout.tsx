import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RainWise — Regime-Aware Monsoon Forecast | PS 26080",
  description:
    "AI-powered regime-aware post-processing of monsoon rainfall forecasts for India. Built for NCMRWF / Ministry of Earth Sciences.",
  keywords: ["monsoon forecast", "AI", "NCMRWF", "rainfall", "India weather"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-slate-900 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
