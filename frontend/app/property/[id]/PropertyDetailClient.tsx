"use client";

import Image from "next/image";

import { Map } from "@/components/Map";
import { BlockchainBadge } from "@/components/BlockchainBadge";
import { FreshnessScore } from "@/components/FreshnessScore";
import { PriceChart } from "@/components/PriceChart";
import type { PropertyData } from "@/types/property";
import { usePropertyStore } from "@/store/usePropertyStore";

type Props = {
  id: string;
  fallback: PropertyData;
};

export function PropertyDetailClient({ id, fallback }: Props) {
  const propertyData = usePropertyStore((s) => s.propertyData);

  const data = propertyData?.id === id ? propertyData : { ...fallback, id };
  const hasCoordinates = typeof data.lat === "number" && typeof data.lng === "number";

  return (
    <>
      <div className="relative mb-8 aspect-[21/9] overflow-hidden rounded-2xl border border-white/10 bg-slate-800">
        <Image src={data.imageUrl} alt={data.areaName} fill className="object-cover" priority />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent" />
        {data.blockchainVerified && (
          <div className="absolute right-4 top-4">
            <BlockchainBadge />
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-white md:text-4xl">{data.areaName}</h1>
          <p className="mt-2 text-3xl font-bold text-sky-300">
            Rs. {data.pricePerSqFt.toLocaleString("en-IN")}
            <span className="text-base font-normal text-slate-400"> / sq ft</span>
          </p>
        </div>
        <span
          className={
            data.trend === "up"
              ? "rounded-full bg-emerald-500/15 px-3 py-1 text-sm font-medium text-emerald-300"
              : data.trend === "down"
                ? "rounded-full bg-rose-500/15 px-3 py-1 text-sm font-medium text-rose-300"
                : "rounded-full bg-slate-500/20 px-3 py-1 text-sm font-medium text-slate-300"
          }
        >
          Trend: {data.trend}
          {typeof data.trendPercent === "number" && <span className="ml-1 opacity-80">({data.trendPercent}%)</span>}
        </span>
      </div>

      <div className="mt-6">
        <FreshnessScore hours={data.freshnessHours} />
      </div>

      {data.priceHistory && data.priceHistory.length > 0 && (
        <div className="mt-10">
          <PriceChart data={data.priceHistory} />
        </div>
      )}

      <div className="mt-10 space-y-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">View on Map</p>
          <p className="text-sm text-slate-400">
            {hasCoordinates ? "Pinned location for this property." : "Location not available."}
          </p>
        </div>
        {hasCoordinates ? (
          <Map lat={Number(data.lat)} lng={Number(data.lng)} label={data.areaName} className="min-h-[280px]" />
        ) : (
          <div className="rounded-2xl border border-white/10 bg-slate-900/40 px-4 py-8 text-sm text-slate-400">
            Location not available
          </div>
        )}
      </div>

      {propertyData?.id !== id && (
        <p className="mt-8 rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-200/90">
          Showing demo data for this URL. Run a search and fetch details to sync live data from your API into the app store.
        </p>
      )}
    </>
  );
}