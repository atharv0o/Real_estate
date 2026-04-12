"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ChatBox } from "@/components/ChatBox";
import { Map } from "@/components/Map";
import { PriceChart } from "@/components/PriceChart";
import { PropertyCard } from "@/components/PropertyCard";
import { CardSkeleton, MapSkeleton } from "@/components/Skeletons";
import { fetchPropertyData, getApiErrorMessage } from "@/lib/api";
import { useMockGeocode, useSearchParamsFromUrl } from "@/lib/hooks";
import { usePropertyStore } from "@/store/usePropertyStore";

/**
 * Search route body: reads URL → mock geocode → map → fetch property data into Zustand.
 */
export default function SearchContent() {
  const params = useSearchParamsFromUrl();
  const coords = useMockGeocode(params);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const {
    searchParams,
    propertyData,
    loading,
    setSearchParams,
    setPropertyData,
    setLoading
  } = usePropertyStore();

  useEffect(() => {
    if (params) setSearchParams(params);
  }, [params, setSearchParams]);

  const handleFetchDetails = useCallback(async () => {
    if (!params) return;
    setFetchError(null);
    setLoading(true);
    try {
      const data = await fetchPropertyData(params);
      setPropertyData(data);
    } catch (e) {
      setFetchError(getApiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [params, setLoading, setPropertyData]);

  if (!params) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center">
        <h1 className="font-display text-2xl font-semibold text-white">
          No search query
        </h1>
        <p className="mt-2 text-slate-400">
          Start from the home page and submit the location form.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-xl bg-sky-500 px-6 py-3 text-sm font-semibold text-slate-950"
        >
          Back to home
        </Link>
      </div>
    );
  }

  const showMapSkeleton = !coords;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 md:py-14">
      <div className="mb-8 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-white md:text-3xl">
            Search results
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Mock geocoding from your query — pin shows the resolved coordinates.
          </p>
        </div>
        <Link
          href="/"
          className="text-sm font-medium text-sky-400 hover:text-sky-300"
        >
          ← Edit search
        </Link>
      </div>

      <div className="grid gap-8 lg:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          {showMapSkeleton ? (
            <MapSkeleton />
          ) : (
            <Map
              lat={coords.lat}
              lng={coords.lng}
              label={coords.label}
              className="aspect-[16/9] w-full min-h-[280px]"
            />
          )}

          <div className="flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={handleFetchDetails}
              disabled={loading}
              className="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-violet-500 to-sky-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-500/20 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Fetching…" : "Fetch Details of the Area"}
            </button>
            {fetchError && (
              <span className="text-sm text-rose-400" role="alert">
                {fetchError}
              </span>
            )}
          </div>

          {loading && <CardSkeleton />}

          {propertyData && !loading && (
            <>
              <PropertyCard
                areaName={propertyData.areaName}
                pricePerSqFt={propertyData.pricePerSqFt}
                trend={propertyData.trend}
                imageUrl={propertyData.imageUrl}
                freshnessHours={propertyData.freshnessHours}
                blockchainVerified={propertyData.blockchainVerified}
              />
              {propertyData.priceHistory && (
                <PriceChart data={propertyData.priceHistory} />
              )}
              <Link
                href={`/property/${propertyData.id}`}
                className="inline-block text-sm font-medium text-sky-400 hover:text-sky-300"
              >
                Open full property view →
              </Link>
            </>
          )}
        </div>

        <div className="lg:sticky lg:top-24 lg:self-start">
          <ChatBox />
        </div>
      </div>

      {/* Debug: surface normalized params from store */}
      {searchParams && (
        <details className="mt-10 rounded-xl border border-white/5 bg-slate-900/30 p-4 text-xs text-slate-500">
          <summary className="cursor-pointer text-slate-400">Stored search params</summary>
          <pre className="mt-2 overflow-x-auto font-mono text-[11px] text-slate-400">
            {JSON.stringify(searchParams, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}
