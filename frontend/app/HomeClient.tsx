"use client";

import { useCallback, useState } from "react";

import { Charts } from "@/components/Charts";
import { Filters } from "@/components/Filters";
import { GoogleMapView } from "@/components/GoogleMapView";
import { PropertyResultCard } from "@/components/PropertyResultCard";
import { SearchBar } from "@/components/SearchBar";
import type {
  AiInsight,
  Coordinates,
  FullSearchPayload,
  LocationQuery,
  PropertyFilters,
  PropertyRecord
} from "@/types/property";

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
  const [pipelineResults, setPipelineResults] = useState<
    PropertyRecord[] | undefined
  >(undefined);
  const [prefetchedInsight, setPrefetchedInsight] =
    useState<AiInsight | null>(null);
  const [selectedProperty, setSelectedProperty] =
    useState<PropertyRecord | null>(null);
  const [showInsights, setShowInsights] = useState(false);

  const handleFullSearch = useCallback(
    (payload: FullSearchPayload, query: LocationQuery) => {
      setCoordinates(payload.coordinates);
      setLastQuery(query);
      setProperties(payload.properties);
      setPipelineResults(payload.properties);
      setPrefetchedInsight(payload.insights);
      setSelectedProperty(payload.properties[0] ?? null);
      setShowInsights(false);
    },
    []
  );

  const handleResultsChange = useCallback(
    (results: PropertyRecord[]) => {
      if (pipelineResults !== undefined) return;
      setProperties(results);
      setSelectedProperty(results[0] ?? null);
    },
    [pipelineResults]
  );

  return (
    <div className="relative pb-20 pt-8 md:pt-16">
      <div className="mx-auto max-w-3xl text-center">
        <p className="mb-4 inline-flex items-center rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium uppercase tracking-wider text-emerald-500">
          Verified marketplace - AI underwriting - on-chain trust
        </p>
        <h1 className="font-display text-4xl font-semibold tracking-tight text-foreground md:text-5xl lg:text-6xl">
          Search prime property signals and ask for
          <span className="bg-gradient-to-r from-blue-600 to-emerald-500 bg-clip-text text-transparent">
            {" "}
            AI insights
          </span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
          A quiet, high-signal workspace for marketplace discovery, investment
          intelligence, and verified property records.
        </p>
      </div>

      <div className="mx-auto mt-12 max-w-5xl space-y-6">
        <SearchBar
          initialValues={lastQuery ?? undefined}
          filters={filters}
          onFullSearch={handleFullSearch}
        />
        <Filters value={filters} onChange={setFilters} />

        <GoogleMapView
          coordinates={coordinates}
          filters={filters}
          onResultsChange={handleResultsChange}
          externalResults={pipelineResults}
        />

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-display text-xl font-semibold text-foreground">
              Nearby properties
            </h2>
            <p className="text-sm text-muted-foreground">
              {coordinates
                ? `Showing results for ${coordinates.label}`
                : "Submit the form to run the full search pipeline"}
            </p>
          </div>
          <button
            type="button"
            disabled={properties.length === 0}
            onClick={() => setShowInsights(true)}
            className="rounded-full bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-600/90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            View AI insights
          </button>
        </div>

        {properties.length === 0 && (
          <div className="rounded-lg border border-border bg-card/65 p-6 text-sm text-muted-foreground shadow-glass backdrop-blur-xl">
            No search results yet. Fill the form and search. Listings come from{" "}
            <code className="text-blue-600">backend/data/properties.json</code>,
            then sync to Postgres.
          </div>
        )}

        {properties.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2">
            {properties.map((property) => (
              <div
                key={String(property.external_id ?? property.id)}
                onClick={() => setSelectedProperty(property)}
                className="cursor-pointer text-left"
              >
                <PropertyResultCard property={property} />
              </div>
            ))}
          </div>
        )}

        {selectedProperty && (
          <div className="rounded-lg border border-border bg-card/65 p-5 text-sm text-muted-foreground shadow-glass backdrop-blur-xl">
            <p className="font-medium text-foreground">Selected property</p>
            <p className="mt-1">{selectedProperty.title}</p>
            <p className="mt-1 text-muted-foreground">
              {selectedProperty.description ?? "No description available."}
            </p>
          </div>
        )}

        <Charts
          enabled={showInsights}
          locationLabel={coordinates?.label ?? ""}
          properties={properties}
          prefetchedInsight={prefetchedInsight}
        />
      </div>
    </div>
  );
}
