"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

import { BlockchainBadge } from "@/components/BlockchainBadge";
import { fetchPropertyById, getApiErrorMessage } from "@/lib/api";
import type { PropertyRecord } from "@/types/property";

type Props = {
  id: string;
};

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&q=80";

export function PropertyDetailLiveClient({ id }: Props) {
  const [property, setProperty] = useState<PropertyRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    async function loadProperty() {
      setLoading(true);
      setError(null);
      try {
        const record = await fetchPropertyById(id);
        if (!ignore) setProperty(record);
      } catch (err) {
        if (!ignore) setError(getApiErrorMessage(err));
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    void loadProperty();
    return () => {
      ignore = true;
    };
  }, [id]);

  if (loading) {
    return <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-6 text-slate-300">Loading property…</div>;
  }

  if (error || !property) {
    return (
      <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-6 text-rose-200">
        {error ?? "Property not found."}
      </div>
    );
  }

  return (
    <>
      <div className="relative mb-8 aspect-[21/9] overflow-hidden rounded-2xl border border-white/10 bg-slate-800">
        <Image src={FALLBACK_IMAGE} alt={property.title} fill className="object-cover" priority />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent" />
        {property.blockchain_verified && (
          <div className="absolute right-4 top-4">
            <BlockchainBadge />
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-white md:text-4xl">{property.title}</h1>
          <p className="mt-2 text-lg text-slate-400">{property.location}</p>
          <p className="mt-2 text-3xl font-bold text-sky-300">{property.price}</p>
        </div>
        <span className="rounded-full bg-sky-500/15 px-3 py-1 text-sm font-medium text-sky-300">
          {property.area_sqft ? `${property.area_sqft} sqft` : "Area unavailable"}
        </span>
      </div>

      <div className="mt-6 grid gap-4 rounded-2xl border border-white/10 bg-slate-900/30 p-5 md:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Registration ID</p>
          <p className="mt-1 text-slate-200">{property.registration_id ?? "Unavailable"}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Owner</p>
          <p className="mt-1 text-slate-200">{property.owner ?? "Unavailable"}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Coordinates</p>
          <p className="mt-1 text-slate-200">
            {typeof property.lat === "number" && typeof property.lng === "number"
              ? `${property.lat}, ${property.lng}`
              : "Unavailable"}
          </p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Source</p>
          <p className="mt-1 text-slate-200">{property.source ?? "pipeline"}</p>
        </div>
      </div>

      <div className="mt-8 rounded-2xl border border-white/10 bg-slate-900/30 p-5">
        <p className="text-xs uppercase tracking-wide text-slate-500">Description</p>
        <p className="mt-2 text-sm leading-6 text-slate-300">
          {property.description ?? "No description available."}
        </p>
      </div>
    </>
  );
}
