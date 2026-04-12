import Image from "next/image";

import type { PropertyTrend } from "@/types/property";

import { BlockchainBadge } from "./BlockchainBadge";
import { FreshnessScore } from "./FreshnessScore";

export type PropertyCardProps = {
  areaName: string;
  pricePerSqFt: number;
  trend: PropertyTrend;
  imageUrl: string;
  freshnessHours: number;
  blockchainVerified?: boolean;
  className?: string;
};

function TrendPill({ trend }: { trend: PropertyTrend }) {
  const config = {
    up: { label: "Trending up", className: "bg-emerald-500/15 text-emerald-300" },
    down: { label: "Cooling", className: "bg-rose-500/15 text-rose-300" },
    flat: { label: "Stable", className: "bg-slate-500/20 text-slate-300" }
  }[trend];

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.className}`}
    >
      {config.label}
    </span>
  );
}

export function PropertyCard({
  areaName,
  pricePerSqFt,
  trend,
  imageUrl,
  freshnessHours,
  blockchainVerified = false,
  className = ""
}: PropertyCardProps) {
  return (
    <article
      className={`group overflow-hidden rounded-2xl border border-white/10 bg-slate-900/50 shadow-xl transition hover:border-sky-500/30 ${className}`}
    >
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-slate-800">
        <Image
          src={imageUrl}
          alt={areaName}
          fill
          className="object-cover transition duration-500 group-hover:scale-[1.03]"
          sizes="(max-width:768px) 100vw, 400px"
          priority={false}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-transparent to-transparent" />
        {blockchainVerified && (
          <div className="absolute right-3 top-3">
            <BlockchainBadge />
          </div>
        )}
      </div>
      <div className="space-y-3 p-5">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h3 className="font-display text-lg font-semibold text-white">
              {areaName}
            </h3>
            <p className="mt-1 text-2xl font-bold tracking-tight text-sky-300">
              ₹{pricePerSqFt.toLocaleString("en-IN")}
              <span className="text-sm font-normal text-slate-400"> / sq ft</span>
            </p>
          </div>
          <TrendPill trend={trend} />
        </div>
        <FreshnessScore hours={freshnessHours} />
      </div>
    </article>
  );
}
