"use client";

import { useCallback, useState } from "react";

import { Charts } from "@/components/Charts";
import { Filters } from "@/components/Filters";
import { MapView } from "@/components/MapView";
import { PropertyResultCard } from "@/components/PropertyResultCard";
import { SearchBar } from "@/components/SearchBar";
import type { Coordinates, LocationQuery, PropertyFilters, PropertyRecord } from "@/types/property";

const DEFAULT_FILTERS: PropertyFilters = {
  radius: 5,
  minPrice: undefined,
  maxPrice: undefined
};

export function HomeClient() {
  const [coordinates, setCoordinates] = useState<Coordinates | null>(null);
  const [lastQuery, setLastQuery] = useState<LocationQuery | null>(null);
  const [filters, setFilters] = useState<PropertyFilters>(DEFAULT_FILTERS);
  const [properties, setProperties] = useState<PropertyRecord[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<PropertyRecord | null>(null);
  const [showInsights, setShowInsights] = useState(false);

  const handleResolved = useCallback((nextCoordinates: Coordinates, query: LocationQuery) => {
    setCoordinates(nextCoordinates);
    setLastQuery(query);
    setProperties([]);
    setSelectedProperty(null);
    setShowInsights(false);
  }, []);

  const handleResultsChange = useCallback((results: PropertyRecord[]) => {
    setProperties(results);
    setSelectedProperty(results[0] ?? null);
  }, []);

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-30" />
      <div className="pointer-events-none absolute -left-40 top-20 h-96 w-96 rounded-full bg-sky-500/20 blur-[120px]" />
      <div className="pointer-events-none absolute -right-40 bottom-0 h-80 w-80 rounded-full bg-violet-500/15 blur-[100px]" />

      <div className="relative mx-auto max-w-6xl px-4 pb-24 pt-16 md:pt-24">
        <div className="mx-auto max-w-3xl text-center">
          <p className="mb-4 inline-flex items-center rounded-full border border-sky-500/20 bg-sky-500/10 px-3 py-1 text-xs font-medium uppercase tracking-wider text-sky-300">
            Full-stack search · DB-backed · RAG insights
          </p>
          <h1 className="font-display text-4xl font-bold tracking-tight text-white md:text-5xl lg:text-6xl">
            Search live land data and ask for
            <span className="bg-gradient-to-r from-sky-400 to-cyan-300 bg-clip-text text-transparent">
              {" "}AI insights
            </span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400">
            Location resolves through the backend, nearby properties load from PostgreSQL,
            and AI summaries are generated from the connected RAG service.
          </p>
        </div>

        <div className="mx-auto mt-12 max-w-5xl space-y-6">
          <SearchBar initialValues={lastQuery ?? undefined} onResolved={handleResolved} />
          <Filters value={filters} onChange={setFilters} />

          <MapView
            coordinates={coordinates}
            filters={filters}
            onResultsChange={handleResultsChange}
          />

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-xl font-semibold text-white">Nearby properties</h2>
              <p className="text-sm text-slate-400">
                {coordinates
                  ? `Showing results for ${coordinates.label}`
                  : "Resolve a location to begin searching"}
              </p>
            </div>
            <button
              type="button"
              disabled={properties.length === 0}
              onClick={() => setShowInsights(true)}
              className="rounded-xl bg-gradient-to-r from-violet-500 to-sky-500 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              View AI insights
            </button>
          </div>

          {properties.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-slate-900/30 p-6 text-sm text-slate-400">
              No search results yet. Resolve a location above and the map will fetch nearby properties automatically.
            </div>
          )}

          {properties.length > 0 && (
            <div className="grid gap-6 md:grid-cols-2">
              {properties.map((property) => (
                <div
                  key={property.id}
                  onClick={() => setSelectedProperty(property)}
                  className="cursor-pointer text-left"
                >
                  <PropertyResultCard property={property} />
                </div>
              ))}
            </div>
          )}

          {selectedProperty && (
            <div className="rounded-2xl border border-white/10 bg-slate-900/30 p-5 text-sm text-slate-300">
              <p className="font-medium text-white">Selected property</p>
              <p className="mt-1">{selectedProperty.title}</p>
              <p className="mt-1 text-slate-400">{selectedProperty.description ?? "No description available."}</p>
            </div>
          )}

          <Charts
            enabled={showInsights}
            locationLabel={coordinates?.label ?? ""}
            properties={properties}
          />
        </div>
      </div>
    </div>
  );
}
