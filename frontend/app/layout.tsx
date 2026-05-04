import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";

import { Navbar } from "@/components/Navbar";
import { SmartGuide } from "@/components/AI/SmartGuide";
import { ThemeProvider } from "@/components/ThemeProvider";

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
  title: "RealEstateAI - Property intelligence",
  description:
    "A premium AI marketplace for property search, investment signals, and verified real estate intelligence."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${outfit.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-screen font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div
            aria-hidden="true"
            className="mesh-gradient pointer-events-none fixed inset-0 z-0"
          >
            <div className="pointer-events-none absolute inset-0 bg-grid" />
          </div>
          <Navbar />
          <main className="relative z-10 mx-auto min-h-[calc(100vh-5rem)] w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
            {children}
          </main>
          <SmartGuide />
        </ThemeProvider>
      </body>
    </html>
  );
}
