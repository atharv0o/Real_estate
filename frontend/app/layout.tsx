import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-geist-sans",
  display: "swap"
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap"
});

export const metadata: Metadata = {
  title: "RealestateRag — Area intelligence",
  description:
    "Search localities, explore maps, and fetch property intelligence powered by RAG."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable}`}>
      <body className="min-h-screen font-sans antialiased">
        <header className="sticky top-0 z-50 border-b border-white/5 bg-slate-950/80 backdrop-blur-md">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
            <a href="/" className="font-display text-lg font-bold tracking-tight text-white">
              Realestate<span className="text-sky-400">Rag</span>
            </a>
            <nav className="flex gap-6 text-sm text-slate-400">
              <a href="/" className="hover:text-white">
                Home
              </a>
              <a href="/search" className="hover:text-white">
                Search
              </a>
            </nav>
          </div>
        </header>
        <main className="relative min-h-[calc(100vh-4rem)]">{children}</main>
        <footer className="border-t border-white/5 py-8 text-center text-xs text-slate-600">
          RealestateRag · Frontend demo · No backend included
        </footer>
      </body>
    </html>
  );
}
