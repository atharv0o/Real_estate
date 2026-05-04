"use client";

import { motion } from "framer-motion";
import Image from "next/image";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
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
  verificationHash?: string | null;
  aiSummary?: string;
  locationLine?: string;
  className?: string;
};

function TrendPill({ trend }: { trend: PropertyTrend }) {
  const config = {
    up: {
      label: "Trending up",
      className: "bg-emerald-500/15 text-emerald-500"
    },
    down: { label: "Cooling", className: "bg-rose-500/15 text-rose-400" },
    flat: {
      label: "Stable",
      className: "bg-slate-500/15 text-muted-foreground"
    }
  }[trend];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium",
        config.className
      )}
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
  verificationHash,
  aiSummary,
  locationLine,
  className
}: PropertyCardProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      whileHover={{ y: -6, scale: 1.01 }}
      viewport={{ once: true, amount: 0.35 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className={cn("group", className)}
    >
      <Card className="overflow-hidden border-white/10 bg-card/70 shadow-glass backdrop-blur-xl transition-colors hover:border-blue-600/40">
        <div className="relative aspect-[16/10] w-full overflow-hidden bg-slate-900">
          <Image
            src={imageUrl}
            alt={areaName}
            fill
            className="object-cover transition duration-700 group-hover:scale-[1.04]"
            sizes="(max-width:768px) 100vw, 420px"
            priority={false}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/85 via-slate-950/10 to-transparent" />
          {(blockchainVerified || verificationHash) && (
            <div className="absolute right-3 top-3 max-w-[min(220px,48%)]">
              <BlockchainBadge
                verified={blockchainVerified}
                hash={verificationHash}
              />
            </div>
          )}
        </div>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="font-display text-lg font-semibold tracking-tight text-foreground">
                {areaName}
              </h3>
              {locationLine ? (
                <p className="mt-1 text-xs text-muted-foreground">
                  {locationLine}
                </p>
              ) : null}
            </div>
            <TrendPill trend={trend} />
          </div>

          <p className="text-2xl font-semibold tracking-tight text-emerald-500">
            Rs {pricePerSqFt.toLocaleString("en-IN")}
            <span className="text-sm font-normal text-muted-foreground">
              {" "}
              / sq ft
            </span>
          </p>

          {aiSummary ? (
            <p className="line-clamp-3 text-sm leading-6 text-muted-foreground">
              {aiSummary}
            </p>
          ) : (
            <div className="space-y-2" aria-label="Property insight loading">
              <div className="h-3 w-full rounded-full bg-muted" />
              <div className="h-3 w-3/4 rounded-full bg-muted" />
            </div>
          )}

          <FreshnessScore hours={freshnessHours} />
        </CardContent>
      </Card>
    </motion.article>
  );
}
