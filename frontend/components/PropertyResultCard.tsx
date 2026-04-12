import Image from "next/image";
import Link from "next/link";

import type { PropertyRecord } from "@/types/property";

import { BlockchainBadge } from "./BlockchainBadge";

type PropertyResultCardProps = {
  property: PropertyRecord;
};

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&q=80";

export function PropertyResultCard({ property }: PropertyResultCardProps) {
  return (
    <article className="group overflow-hidden rounded-2xl border border-white/10 bg-slate-900/50 shadow-xl transition hover:border-sky-500/30">
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-slate-800">
        <Image
          src={FALLBACK_IMAGE}
          alt={property.title}
          fill
          className="object-cover transition duration-500 group-hover:scale-[1.03]"
          sizes="(max-width:768px) 100vw, 400px"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-transparent to-transparent" />
        {property.blockchain_verified && (
          <div className="absolute right-3 top-3">
            <BlockchainBadge />
          </div>
        )}
      </div>
      <div className="space-y-3 p-5">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h3 className="font-display text-lg font-semibold text-white">{property.title}</h3>
            <p className="mt-1 text-sm text-slate-400">{property.location}</p>
            <p className="mt-2 text-2xl font-bold tracking-tight text-sky-300">{property.price}</p>
          </div>
          {typeof property.distance_km === "number" && (
            <span className="rounded-full bg-sky-500/15 px-2.5 py-1 text-xs font-medium text-sky-300">
              {property.distance_km.toFixed(2)} km
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
          <span>Area: {property.area_sqft ? `${property.area_sqft} sqft` : "N/A"}</span>
          <span>Source: {property.source ?? "pipeline"}</span>
        </div>
        <Link
          href={`/property/${property.external_id ?? property.id}`}
          className="inline-flex text-sm font-medium text-sky-400 hover:text-sky-300"
        >
          View property details
        </Link>
      </div>
    </article>
  );
}
