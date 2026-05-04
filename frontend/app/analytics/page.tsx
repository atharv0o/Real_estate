"use client";

import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  BadgeCheck,
  Database,
  Gauge,
  Map,
  Radar,
  ShieldAlert,
  Sparkles,
  Terminal,
  TrendingUp,
  Wallet
} from "lucide-react";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const hotspots = [
  {
    name: "Kharadi",
    x: "31%",
    y: "48%",
    signal: "High Demand",
    tone: "emerald"
  },
  {
    name: "Baner",
    x: "45%",
    y: "36%",
    signal: "Infrastructure Surge",
    tone: "blue"
  },
  {
    name: "Balewadi",
    x: "52%",
    y: "46%",
    signal: "Underpriced",
    tone: "rose"
  },
  {
    name: "Powai",
    x: "72%",
    y: "32%",
    signal: "High Demand",
    tone: "emerald"
  },
  {
    name: "Worli",
    x: "81%",
    y: "55%",
    signal: "Infrastructure Surge",
    tone: "blue"
  }
];

const alphaData = [
  { month: "Jan", value: 64 },
  { month: "Feb", value: 67 },
  { month: "Mar", value: 71 },
  { month: "Apr", value: 76 },
  { month: "May", value: 81 },
  { month: "Jun", value: 86 }
];

const scans = [
  {
    property: "Property ID #102",
    detail: "Duplicate Image Match found in external DB",
    status: "Flagged",
    tone: "rose",
    icon: ShieldAlert
  },
  {
    property: "Property ID #105",
    detail: "Price 40% below market average",
    status: "Pending Review",
    tone: "amber",
    icon: AlertTriangle
  },
  {
    property: "Property ID #109",
    detail: "Ownership Hash Verified on Algorand",
    status: "Safe",
    tone: "emerald",
    icon: BadgeCheck
  }
];

const legend = [
  { label: "High Demand", className: "bg-emerald-500" },
  { label: "Infrastructure Surge", className: "bg-blue-400" },
  { label: "Underpriced", className: "bg-rose-500" }
];

const briefing =
  "AI Analysis: Metro Line 3 completion in 2026 will likely drive a 15% appreciation in surrounding residential assets. Recommendation: Target 2BHK units in Sector 4.";

function toneClasses(tone: string) {
  if (tone === "rose") {
    return {
      dot: "bg-rose-500 shadow-[0_0_30px_rgba(244,63,94,0.85)]",
      pulse: "border-rose-400/30 bg-rose-500/10",
      text: "text-rose-300",
      badge: "border-rose-400/30 bg-rose-500/10 text-rose-300"
    };
  }

  if (tone === "amber") {
    return {
      dot: "bg-amber-300 shadow-[0_0_30px_rgba(252,211,77,0.8)]",
      pulse: "border-amber-300/30 bg-amber-300/10",
      text: "text-amber-200",
      badge: "border-amber-300/30 bg-amber-400/10 text-amber-200"
    };
  }

  if (tone === "blue") {
    return {
      dot: "bg-blue-400 shadow-[0_0_30px_rgba(96,165,250,0.8)]",
      pulse: "border-blue-400/30 bg-blue-400/10",
      text: "text-blue-200",
      badge: "border-blue-400/30 bg-blue-400/10 text-blue-200"
    };
  }

  return {
    dot: "bg-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.9)]",
    pulse: "border-emerald-400/30 bg-emerald-500/10",
    text: "text-emerald-300",
    badge: "border-emerald-400/30 bg-emerald-500/10 text-emerald-300"
  };
}

function HotspotDot({
  hotspot,
  index
}: {
  hotspot: (typeof hotspots)[number];
  index: number;
}) {
  const classes = toneClasses(hotspot.tone);

  return (
    <motion.div
      className="absolute"
      style={{ left: hotspot.x, top: hotspot.y }}
      initial={{ opacity: 0, scale: 0.72 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.12, duration: 0.35 }}
    >
      <motion.span
        className={cn(
          "absolute -left-7 -top-7 h-14 w-14 rounded-full border",
          classes.pulse
        )}
        animate={{ scale: [0.65, 1.75], opacity: [0.72, 0] }}
        transition={{ duration: 2.4, repeat: Infinity, delay: index * 0.28 }}
      />
      <span className={cn("relative block h-4 w-4 rounded-full", classes.dot)} />
      <div className="absolute left-5 top-1/2 min-w-36 -translate-y-1/2 rounded-lg border border-white/10 bg-slate-950/85 px-3 py-2 text-xs shadow-glass backdrop-blur-xl">
        <p className="font-medium text-white">{hotspot.name}</p>
        <p className={cn("mt-0.5", classes.text)}>{hotspot.signal}</p>
      </div>
    </motion.div>
  );
}

function StatusBadge({ tone, label }: { tone: string; label: string }) {
  return (
    <span
      className={cn(
        "rounded-full border px-2.5 py-1 text-xs font-medium",
        toneClasses(tone).badge
      )}
    >
      {label}
    </span>
  );
}

function BentoCard({
  title,
  value,
  icon: Icon,
  children
}: {
  title: string;
  value: string;
  icon: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <Card className="border-white/10 bg-slate-950/75 text-white shadow-none backdrop-blur-xl">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm text-slate-400">{title}</p>
            <p className="mt-2 text-2xl font-semibold">{value}</p>
          </div>
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-emerald-400/20 bg-emerald-500/10 text-emerald-300">
            <Icon className="h-5 w-5" />
          </span>
        </div>
        <div className="mt-5">{children}</div>
      </CardContent>
    </Card>
  );
}

function SaturationGauge({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-5">
      <div
        className="relative h-28 w-28 rounded-full"
        style={{
          background: `conic-gradient(#10b981 ${value * 3.6}deg, #1e293b 0deg)`
        }}
      >
        <div className="absolute inset-3 grid place-items-center rounded-full bg-slate-950">
          <div className="text-center">
            <p className="text-2xl font-semibold text-white">{value}</p>
            <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">
              score
            </p>
          </div>
        </div>
      </div>
      <div className="text-sm leading-6 text-slate-400">
        Buyer saturation is elevated, but verified supply remains constrained in core Pune corridors.
      </div>
    </div>
  );
}

function TerminalBriefing() {
  return (
    <motion.p
      className="text-sm leading-7 text-emerald-300"
      initial="hidden"
      animate="show"
      variants={{ show: { transition: { staggerChildren: 0.018 } } }}
    >
      {briefing.split("").map((character, index) => (
        <motion.span
          key={`${character}-${index}`}
          variants={{
            hidden: { opacity: 0 },
            show: { opacity: 1 }
          }}
        >
          {character}
        </motion.span>
      ))}
      <motion.span
        className="ml-1 inline-block h-4 w-2 translate-y-0.5 bg-emerald-400"
        animate={{ opacity: [1, 0, 1] }}
        transition={{ duration: 0.9, repeat: Infinity }}
      />
    </motion.p>
  );
}

export default function AnalyticsPage() {
  return (
    <div className="space-y-6 pb-8 text-slate-100">
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
            <Radar className="h-3.5 w-3.5" />
            Intelligence Dashboard
          </div>
          <h1 className="mt-4 font-display text-3xl font-semibold tracking-normal text-white md:text-5xl">
            Market intelligence control room
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Heatmap signals, fraud telemetry, wallet movement, and AI forecasts for Pune and Mumbai investment decisions.
          </p>
        </div>
        <div className="rounded-full border border-white/10 bg-slate-950/70 px-4 py-2 text-sm text-slate-300 backdrop-blur-xl">
          Pune / Mumbai live scan
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1fr_370px]">
        <section className="space-y-6">
          <Card className="overflow-hidden border-emerald-500/15 bg-slate-950/80 text-white shadow-[0_0_90px_rgba(15,23,42,0.55)] backdrop-blur-xl">
            <CardContent className="p-0">
              <div className="flex flex-col justify-between gap-4 border-b border-white/10 p-5 md:flex-row md:items-center">
                <div>
                  <p className="text-sm text-slate-400">Hotspot Map</p>
                  <h2 className="mt-1 text-xl font-semibold">Location Growth Heatmap</h2>
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
                  <Map className="h-3.5 w-3.5" />
                  Stylized Pune / Mumbai layer
                </div>
              </div>

              <div className="relative min-h-[500px] overflow-hidden bg-slate-950">
                <div className="absolute inset-0 bg-[linear-gradient(rgba(16,185,129,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(16,185,129,0.06)_1px,transparent_1px)] bg-[size:44px_44px]" />
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_36%_47%,rgba(16,185,129,0.23),transparent_24%),radial-gradient(circle_at_76%_48%,rgba(59,130,246,0.18),transparent_27%),radial-gradient(circle_at_53%_48%,rgba(244,63,94,0.12),transparent_19%)]" />
                <div className="absolute left-[13%] top-[27%] h-56 w-80 rotate-[-17deg] rounded-[45%] border border-emerald-400/10 bg-emerald-400/5 blur-sm" />
                <div className="absolute right-[9%] top-[24%] h-64 w-72 rotate-12 rounded-[45%] border border-blue-400/10 bg-blue-400/5 blur-sm" />
                <div className="absolute left-[46%] top-[33%] h-56 w-44 rotate-6 rounded-[45%] border border-rose-400/10 bg-rose-500/5 blur-sm" />

                <div className="absolute left-6 top-6 rounded-lg border border-white/10 bg-slate-950/70 p-4 backdrop-blur-xl">
                  <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                    Legend
                  </p>
                  <div className="mt-3 grid gap-2">
                    {legend.map((item) => (
                      <div key={item.label} className="flex items-center gap-2 text-xs text-slate-300">
                        <span className={cn("h-2.5 w-2.5 rounded-full", item.className)} />
                        {item.label}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="absolute bottom-6 left-6 rounded-lg border border-white/10 bg-slate-950/70 p-4 text-xs text-slate-400 backdrop-blur-xl">
                  <p className="font-medium text-white">Map Layer Placeholder</p>
                  <p className="mt-2">Demand / infrastructure / pricing anomaly overlays</p>
                </div>

                {hotspots.map((hotspot, index) => (
                  <HotspotDot key={hotspot.name} hotspot={hotspot} index={index} />
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-5 lg:grid-cols-3">
            <BentoCard title="Area Alpha" value="+18%" icon={TrendingUp}>
              <div className="h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={alphaData}>
                    <defs>
                      <linearGradient id="alpha-fill" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0%" stopColor="#10b981" stopOpacity={0.36} />
                        <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="month" hide />
                    <YAxis hide domain={["dataMin - 6", "dataMax + 6"]} />
                    <Tooltip
                      contentStyle={{
                        background: "#020617",
                        border: "1px solid rgba(255,255,255,0.12)",
                        borderRadius: 10,
                        color: "#f8fafc"
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#10b981"
                      strokeWidth={2.5}
                      fill="url(#alpha-fill)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-2 text-xs text-slate-400">Kharadi six-month growth momentum</p>
            </BentoCard>

            <BentoCard title="Wallet Activity" value="ALG 4.82M" icon={Wallet}>
              <div className="rounded-lg border border-emerald-500/15 bg-emerald-500/10 p-4">
                <p className="text-sm text-emerald-200">Total Algorand platform volume</p>
                <div className="mt-4 flex items-center gap-2 text-xs text-slate-400">
                  <Activity className="h-4 w-4 text-emerald-300" />
                  +22.4% settlement flow this month
                </div>
              </div>
            </BentoCard>

            <BentoCard title="Supply vs Demand" value="Buyer Saturation" icon={Gauge}>
              <SaturationGauge value={78} />
            </BentoCard>
          </div>
        </section>

        <aside className="space-y-6">
          <Card className="border-white/10 bg-slate-950/80 text-white shadow-none backdrop-blur-xl">
            <CardContent className="p-5">
              <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400">Recent Security Scans</p>
                  <h2 className="mt-1 text-xl font-semibold">Fraud Detection Live Feed</h2>
                </div>
                <span className="grid h-10 w-10 place-items-center rounded-full bg-rose-500/10 text-rose-300">
                  <Database className="h-5 w-5" />
                </span>
              </div>

              <div className="space-y-3">
                {scans.map((scan, index) => {
                  const Icon = scan.icon;

                  return (
                    <motion.div
                      key={scan.property}
                      initial={{ opacity: 0, x: 18 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.08, duration: 0.28 }}
                      className="rounded-lg border border-white/10 bg-white/[0.03] p-4"
                    >
                      <div className="flex items-start gap-3">
                        <Icon className={cn("mt-1 h-4 w-4", toneClasses(scan.tone).text)} />
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-sm font-medium text-white">{scan.property}</p>
                            <StatusBadge tone={scan.tone} label={scan.status} />
                          </div>
                          <p className="mt-3 text-sm leading-5 text-slate-400">{scan.detail}</p>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="border-emerald-500/20 bg-slate-950/85 text-white shadow-[0_0_70px_rgba(16,185,129,0.08)] backdrop-blur-xl">
            <CardContent className="p-5">
              <div className="mb-4 flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-full bg-emerald-500/10 text-emerald-300">
                  <Sparkles className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-sm text-slate-400">AI Prediction Briefing</p>
                  <h2 className="text-xl font-semibold">Terminal Forecast</h2>
                </div>
              </div>
              <div className="min-h-48 rounded-lg border border-white/10 bg-black/50 p-4 font-mono">
                <div className="mb-4 flex items-center gap-2 border-b border-emerald-500/20 pb-3 text-xs uppercase tracking-[0.2em] text-emerald-500">
                  <Terminal className="h-4 w-4" />
                  Intelligence Agent
                </div>
                <TerminalBriefing />
              </div>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
