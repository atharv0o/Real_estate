"use client";

import { motion } from "framer-motion";
import type { Variants } from "framer-motion";
import {
  BadgeCheck,
  Bot,
  CheckCircle2,
  Gem,
  MapPin,
  MessageCircle,
  Send,
  ShieldCheck,
  Wallet
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useWallet } from "@/store/useWallet";

const property = {
  id: "p-01",
  title: "Skyline Residences",
  location: "Worli, Mumbai",
  price: 720000,
  trustScore: 94,
  monthlyYield: 4850,
  image:
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1800&q=85"
};

const projectedValue = [
  { year: "2026", value: 720 },
  { year: "2027", value: 782 },
  { year: "2028", value: 846 },
  { year: "2029", value: 928 },
  { year: "2030", value: 1014 },
  { year: "2031", value: 1128 }
];

const legalChecks = [
  "Ownership Hash Verified",
  "Tax Docs Verified",
  "Zoning Clear"
];

const quickPrompts = [
  "Analyze ROI",
  "Is this price fair?",
  "Suggest a lower offer"
];

const bentoMotion: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: (index: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: index * 0.08,
      duration: 0.35,
      ease: [0.16, 1, 0.3, 1] as const
    }
  })
};

function TrustGauge({ score }: { score: number }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative grid place-items-center">
      <svg className="h-40 w-40 -rotate-90" viewBox="0 0 140 140">
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="10"
          className="text-slate-800/80"
        />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeLinecap="round"
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="text-emerald-500"
        />
      </svg>
      <div className="absolute text-center">
        <p className="text-4xl font-semibold text-white">{score}</p>
        <p className="text-xs text-slate-400">AI score</p>
      </div>
    </div>
  );
}

function BentoCard({
  className,
  index,
  children
}: {
  className?: string;
  index: number;
  children: React.ReactNode;
}) {
  return (
    <motion.div variants={bentoMotion} initial="hidden" animate="show" custom={index}>
      <Card
        className={cn(
          "h-full border-white/10 bg-slate-950/70 text-white shadow-none backdrop-blur-xl",
          className
        )}
      >
        <CardContent className="h-full p-6">{children}</CardContent>
      </Card>
    </motion.div>
  );
}

export default function MarketplacePropertyDetailPage() {
  const { isConnected } = useWallet();

  return (
    <div className="pb-24 text-slate-100">
      <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-950/70 shadow-glass">
        <div className="relative min-h-[460px]">
          <div
            aria-label={property.title}
            className="absolute inset-0 bg-cover bg-center"
            role="img"
            style={{ backgroundImage: `url(${property.image})` }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/35 to-slate-900/20" />
          <div className="relative flex min-h-[460px] flex-col justify-between p-6 sm:p-8 lg:p-10">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur-xl">
                <Gem className="h-3.5 w-3.5 text-emerald-400" />
                Minted as NFT
                <span className="ml-1 inline-grid h-5 w-5 place-items-center rounded-full bg-white text-[10px] font-bold text-slate-950">
                  A
                </span>
              </div>
              <div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-300">
                Algorand verified asset
              </div>
            </div>

            <div className="max-w-3xl">
              <h1 className="font-display text-4xl font-semibold tracking-normal text-white md:text-6xl">
                {property.title}
              </h1>
              <div className="mt-4 flex items-center gap-2 text-sm text-slate-200">
                <MapPin className="h-4 w-4 text-emerald-400" />
                <span>{property.location}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_340px]">
        <section className="grid auto-rows-[minmax(220px,auto)] gap-5 md:grid-cols-4">
          <BentoCard index={0} className="md:col-span-2">
            <div className="mb-5 flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">Growth</p>
                <h2 className="mt-1 text-xl font-semibold">Projected Value</h2>
              </div>
              <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
                2026-2031
              </span>
            </div>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={projectedValue} margin={{ left: -18, right: 8 }}>
                  <CartesianGrid stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="year" stroke="#94a3b8" tickLine={false} axisLine={false} />
                  <YAxis
                    stroke="#94a3b8"
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => `$${value}k`}
                  />
                  <Tooltip
                    cursor={{ stroke: "#10b981", strokeWidth: 1 }}
                    contentStyle={{
                      background: "#020617",
                      border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: 12,
                      color: "#f8fafc"
                    }}
                    formatter={(value) => [`$${value}k`, "Projected value"]}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#10b981"
                    strokeWidth={3}
                    dot={{ r: 4, fill: "#10b981", strokeWidth: 0 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </BentoCard>

          <BentoCard index={1}>
            <div className="mb-4">
              <p className="text-sm text-slate-400">Trust Score</p>
              <h2 className="mt-1 text-xl font-semibold">AI Fraud Detection</h2>
            </div>
            <TrustGauge score={property.trustScore} />
          </BentoCard>

          <BentoCard index={2}>
            <p className="text-sm text-slate-400">Rental Yield</p>
            <div className="mt-8">
              <p className="text-4xl font-semibold text-white">
                ${property.monthlyYield.toLocaleString()}
              </p>
              <p className="mt-2 text-sm text-slate-400">estimated monthly yield</p>
            </div>
            <div className="mt-8 rounded-lg border border-emerald-500/15 bg-emerald-500/10 p-3 text-sm text-emerald-200">
              Net yield model includes vacancy and maintenance assumptions.
            </div>
          </BentoCard>

          <BentoCard index={3} className="md:col-span-4">
            <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
              <div>
                <p className="text-sm text-slate-400">Legal</p>
                <h2 className="mt-1 text-xl font-semibold">Verification Checklist</h2>
              </div>
              <div className="grid flex-1 gap-3 md:grid-cols-3">
                {legalChecks.map((check) => (
                  <div
                    key={check}
                    className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-4"
                  >
                    <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                    <span className="text-sm">{check}</span>
                  </div>
                ))}
              </div>
            </div>
          </BentoCard>
        </section>

        <aside className="lg:sticky lg:top-24 lg:self-start">
          <Card className="border-white/10 bg-slate-950/80 text-white shadow-none backdrop-blur-xl">
            <CardContent className="p-5">
              <div className="flex items-center gap-3 border-b border-white/10 pb-5">
                <div className="grid h-11 w-11 place-items-center rounded-full bg-emerald-500/10 text-emerald-300">
                  <Bot className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="font-semibold">AI Advisor</h2>
                  <p className="text-xs text-slate-400">Negotiation intelligence</p>
                </div>
              </div>

              <div className="space-y-3 py-5">
                <div className="rounded-lg bg-white/[0.04] p-4 text-sm leading-6 text-slate-200">
                  This listing is priced within the upper fair-value band. Current trust and legal signals support a confident offer strategy.
                </div>
                <div className="rounded-lg border border-emerald-500/15 bg-emerald-500/10 p-4 text-sm leading-6 text-emerald-100">
                  Suggested opening offer: 4.5% below ask with a 72-hour wallet close.
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                  Quick Prompts
                </p>
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    className="flex w-full items-center justify-between rounded-full border border-white/10 px-4 py-2 text-left text-sm text-slate-200 transition-colors hover:border-emerald-500/30 hover:bg-emerald-500/10"
                  >
                    {prompt}
                    <Send className="h-3.5 w-3.5 text-emerald-400" />
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </aside>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-white/10 bg-slate-950/90 px-4 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-white">{property.title}</p>
            <p className="text-xs text-slate-400">NFT deed ready for wallet settlement</p>
          </div>
          <div className="flex gap-3">
            <Button
              className="flex-1 bg-emerald-500 text-slate-950 hover:bg-emerald-400 sm:flex-none"
              disabled={!isConnected}
              title={!isConnected ? "Please Connect Wallet" : "Buy NFT asset"}
            >
              <Wallet className="h-4 w-4" />
              {isConnected ? "Buy NFT Asset" : "Please Connect Wallet"}
            </Button>
            <Button variant="outline" className="flex-1 border-white/15 bg-white/5 text-white hover:bg-white/10 sm:flex-none">
              <MessageCircle className="h-4 w-4" />
              Contact Seller
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
