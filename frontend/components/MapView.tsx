"use client";

import { useEffect, useMemo, useState } from "react";

import { getApiErrorMessage, searchLand } from "@/lib/api";
import type { Coordinates, PropertyFilters, PropertyRecord } from "@/types/property";

type MapViewProps = {
  coordinates: Coordinates | null;
  filters: PropertyFilters;
  onResultsChange?: (results: PropertyRecord[]) => void;
  /** When set (including []), skips network search and uses these listings for markers. */
  externalResults?: PropertyRecord[] | null;
};

export function MapView({ coordinates, filters, onResultsChange, externalResults }: MapViewProps) {
  const [results, setResults] = useState<PropertyRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const useExternal = externalResults !== undefined && externalResults !== null;

  useEffect(() => {
    if (useExternal) {
      setResults(externalResults);
      setError(null);
      setLoading(false);
      onResultsChange?.(externalResults);
      return;
    }

    if (!coordinates) {
      setResults([]);
      setError(null);
      onResultsChange?.([]);
      return;
    }

    let ignore = false;
    const timerId = window.setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const nextResults = await searchLand(coordinates, filters);
        if (!ignore) {
          setResults(nextResults);
          onResultsChange?.(nextResults);
        }
      } catch (err) {
        const message = getApiErrorMessage(err);
        if (!ignore) {
          setError(message);
          setResults([]);
          onResultsChange?.([]);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }, 400);

    return () => {
      ignore = true;
      window.clearTimeout(timerId);
    };
  }, [coordinates, filters, onResultsChange, externalResults, useExternal]);

  const markers = useMemo(() => {
    if (!coordinates || results.length === 0) return [];
    const maxShow = 24;
    const slice = results.slice(0, maxShow);
    const dlat = slice.map((r) => Number(r.lat) - coordinates.lat);
    const dlng = slice.map((r) => Number(r.lng) - coordinates.lng);
    const maxD = Math.max(
      1e-6,
      ...dlat.map((a) => Math.abs(a)),
      ...dlng.map((a) => Math.abs(a))
    );
    const scale = 38 / maxD;
    return slice.map((r, i) => ({
      id: `${r.id}-${i}`,
      leftPct: 50 + (Number(r.lng) - coordinates.lng) * scale,
      topPct: 50 - (Number(r.lat) - coordinates.lat) * scale,
      title: r.title
    }));
  }, [coordinates, results]);

  return (
    <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/50 shadow-inner">
      <div
        className="relative aspect-[16/9] w-full overflow-hidden"
        aria-label={
          coordinates
            ? `Map showing ${coordinates.label} at ${coordinates.lat.toFixed(4)}, ${coordinates.lng.toFixed(4)}`
            : "Map awaiting location"
        }
      >
        <div
          className="absolute inset-0 opacity-90"
          style={{
            background:
              "radial-gradient(ellipse at 30% 20%, rgba(56,189,248,0.25), transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(14,165,233,0.15), transparent 45%), linear-gradient(180deg, #0f172a 0%, #1e293b 100%)"
          }}
        />
        <div className="absolute inset-0 bg-grid opacity-40" />

        <div className="absolute left-3 top-3 rounded-lg bg-black/40 px-3 py-1 text-[10px] text-slate-300">
          {useExternal ? "Pipeline search" : "Live search"}
        </div>

        {coordinates ? (
          <>
            <div className="absolute left-1/2 top-1/2 z-10 flex -translate-x-1/2 -translate-y-full flex-col items-center">
              <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-sky-500 shadow-lg shadow-sky-500/40 ring-4 ring-sky-500/30">
                <span className="h-3 w-3 rounded-full bg-white" />
              </div>
              <div className="h-4 w-px bg-gradient-to-b from-sky-400/80 to-transparent" />
            </div>
            {markers.map((m) => (
              <div
                key={m.id}
                title={m.title}
                className="absolute z-[5] h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-violet-400 shadow-md shadow-violet-500/50 ring-2 ring-white/20"
                style={{
                  left: `${Math.min(96, Math.max(4, m.leftPct))}%`,
                  top: `${Math.min(92, Math.max(8, m.topPct))}%`
                }}
              />
            ))}
          </>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-sm text-slate-400">
            Enter a location to resolve coordinates and load nearby properties.
          </div>
        )}
      </div>

      <div className="border-t border-white/10 bg-slate-950/80 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-white">
              {coordinates?.label ?? "No location selected"}
            </p>
            <p className="text-xs text-sky-300/90">
              {coordinates
                ? `${coordinates.lat.toFixed(6)}, ${coordinates.lng.toFixed(6)}`
                : "Waiting for coordinates"}
            </p>
          </div>
          <p className="text-xs text-slate-400">Radius: {filters.radius} km</p>
        </div>

        <div className="mt-3 rounded-xl border border-white/5 bg-black/20 p-3 text-sm text-slate-300">
          {loading && <p>Loading nearby properties…</p>}
          {error && <p className="text-rose-400">{error}</p>}
          {!loading && !error && coordinates && results.length === 0 && (
            <p>No properties found for this search.</p>
          )}
          {!loading && results.length > 0 && (
            <ul className="space-y-1">
              {results.slice(0, 4).map((result) => (
                <li key={result.id} className="truncate">
                  {result.title} • {result.location}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
