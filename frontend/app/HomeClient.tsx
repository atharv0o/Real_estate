"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { Charts } from "@/components/Charts";
import { Filters } from "@/components/Filters";
import { GoogleMapView } from "@/components/GoogleMapView";
import { PropertyResultCard } from "@/components/PropertyResultCard";
import { SearchBar } from "@/components/SearchBar";
import { usePropertyStore } from "@/store/usePropertyStore";

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

function sameJson(a: unknown, b: unknown) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function sameProperties(a: PropertyRecord[] | undefined | null, b: PropertyRecord[] | undefined | null) {
  if ((a?.length ?? 0) !== (b?.length ?? 0)) return false;
  return sameJson(a ?? [], b ?? []);
}

export function HomeClient() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  const persistedSnapshot = usePropertyStore((s) => s.searchSnapshot);
  const setSearchParamsInStore = usePropertyStore((s) => s.setSearchParams);
  const setSearchSnapshot = usePropertyStore((s) => s.setSearchSnapshot);

  const initializedRef = useRef(false);
  const urlAppliedRef = useRef("");
  const lastSavedSnapshotRef = useRef("");

  const [coordinates, setCoordinates] = useState<Coordinates | null>(null);
  const [lastQuery, setLastQuery] = useState<LocationQuery | null>(null);
  const [filters, setFilters] = useState<PropertyFilters>(DEFAULT_FILTERS);
  const [properties, setProperties] = useState<PropertyRecord[]>([]);
  const [pipelineResults, setPipelineResults] = useState<PropertyRecord[]>();
  const [prefetchedInsight, setPrefetchedInsight] = useState<AiInsight | null>(null);
  const [selectedProperty, setSelectedProperty] = useState<PropertyRecord | null>(null);
  const [showInsights, setShowInsights] = useState(false);

  const searchQueryString = searchParams.toString();

  // Restore snapshot only once.
  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;
    if (!persistedSnapshot) return;

    setCoordinates((prev) =>
      sameJson(prev, persistedSnapshot.coordinates) ? prev : persistedSnapshot.coordinates
    );
    setLastQuery((prev) =>
      sameJson(prev, persistedSnapshot.query) ? prev : persistedSnapshot.query
    );
    setFilters((prev) =>
      sameJson(prev, persistedSnapshot.filters) ? prev : persistedSnapshot.filters
    );
    setProperties((prev) =>
      sameProperties(prev, persistedSnapshot.properties) ? prev : persistedSnapshot.properties
    );
    setPipelineResults((prev) =>
      sameProperties(prev, persistedSnapshot.pipelineResults) ? prev : persistedSnapshot.pipelineResults ?? undefined
    );
    setPrefetchedInsight((prev) =>
      sameJson(prev, persistedSnapshot.prefetchedInsight) ? prev : persistedSnapshot.prefetchedInsight
    );

    const selected =
      persistedSnapshot.properties.find(
        (p) =>
          String(p.external_id ?? p.id) ===
          persistedSnapshot.selectedPropertyId
      ) ?? persistedSnapshot.properties[0];

    setSelectedProperty((prev) => (sameJson(prev, selected ?? null) ? prev : selected ?? null));
    setShowInsights((prev) => (prev === persistedSnapshot.showInsights ? prev : persistedSnapshot.showInsights));

    requestAnimationFrame(() => {
      window.scrollTo({
        top: persistedSnapshot.scrollY ?? 0,
        behavior: "auto"
      });
    });
  }, [persistedSnapshot]);

  // URL to state.
  useEffect(() => {
    if (!searchQueryString) return;
    if (urlAppliedRef.current === searchQueryString) return;

    urlAppliedRef.current = searchQueryString;

    const params = Object.fromEntries(searchParams.entries());

    const query: LocationQuery = {
      district: params.district || "",
      city: params.city || "",
      area: params.area || "",
      pinCode: params.pinCode || "",
      landAreaCode: params.landAreaCode || ""
    };

    const nextFilters: PropertyFilters = {
      radius: Number(params.radius) || 5,
      minPrice: params.minPrice ? Number(params.minPrice) : undefined,
      maxPrice: params.maxPrice ? Number(params.maxPrice) : undefined
    };

    setLastQuery((prev) =>
      JSON.stringify(prev) === JSON.stringify(query) ? prev : query
    );

    setFilters((prev) =>
      JSON.stringify(prev) === JSON.stringify(nextFilters)
        ? prev
        : nextFilters
    );

    setSearchParamsInStore(query);
  }, [searchParams, searchQueryString, setSearchParamsInStore]);

  // State to URL without circular updates.
  useEffect(() => {
    if (!lastQuery) return;

    const params = new URLSearchParams();

    Object.entries(lastQuery).forEach(([k, v]) => v && params.set(k, v));
    params.set("radius", String(filters.radius));

    if (filters.minPrice) params.set("minPrice", String(filters.minPrice));
    if (filters.maxPrice) params.set("maxPrice", String(filters.maxPrice));

    const nextQueryString = params.toString();
    const newUrl = nextQueryString ? `${pathname}?${nextQueryString}` : pathname;
    const currentUrl = searchQueryString ? `${pathname}?${searchQueryString}` : pathname;

    if (newUrl === currentUrl) return;

    router.replace(newUrl, { scroll: false });
  }, [filters, lastQuery, pathname, router, searchQueryString]);

  // Search handler.
  const handleFullSearch = useCallback(
    (payload: FullSearchPayload, query: LocationQuery) => {
      setCoordinates((prev) => (sameJson(prev, payload.coordinates) ? prev : payload.coordinates));
      setLastQuery((prev) => (sameJson(prev, query) ? prev : query));
      setProperties((prev) => (sameProperties(prev, payload.properties) ? prev : payload.properties));
      setPipelineResults((prev) => (sameProperties(prev, payload.properties) ? prev : payload.properties));
      setPrefetchedInsight((prev) => (sameJson(prev, payload.insights) ? prev : payload.insights));
      setSelectedProperty((prev) => (sameJson(prev, payload.properties[0] ?? null) ? prev : payload.properties[0] ?? null));
      setShowInsights((prev) => (prev === false ? prev : false));
      setSearchParamsInStore(query);
    },
    [setSearchParamsInStore]
  );

  const handleMapResultsChange = useCallback((results: PropertyRecord[]) => {
    setProperties((prev) => (sameProperties(prev, results) ? prev : results));
  }, []);

  const saveCurrentSnapshot = useCallback(() => {
    if (!lastQuery && properties.length === 0) return;

    const snapshot = {
      query: lastQuery,
      coordinates,
      filters,
      properties,
      pipelineResults: pipelineResults ?? null,
      prefetchedInsight,
      selectedPropertyId: selectedProperty
        ? String(selectedProperty.external_id ?? selectedProperty.id)
        : null,
      showInsights,
      scrollY: window.scrollY
    };
    const snapshotKey = JSON.stringify(snapshot);
    if (lastSavedSnapshotRef.current === snapshotKey) return;
    lastSavedSnapshotRef.current = snapshotKey;
    setSearchSnapshot({ ...snapshot, updatedAt: Date.now() });
  }, [
    coordinates,
    filters,
    lastQuery,
    pipelineResults,
    prefetchedInsight,
    properties,
    selectedProperty,
    setSearchSnapshot,
    showInsights
  ]);

  // Snapshot save.
  useEffect(() => {
    saveCurrentSnapshot();
  }, [saveCurrentSnapshot]);

  return (
  <div className="p-6 space-y-6">
    
    {/* Top Section (Full Width) */}
    <SearchBar
      initialValues={lastQuery ?? undefined}
      filters={filters}
      onFullSearch={handleFullSearch}
    />

    <Filters value={filters} onChange={setFilters} />

    <GoogleMapView
      coordinates={coordinates}
      filters={filters}
      externalResults={pipelineResults}
      onResultsChange={handleMapResultsChange}
    />

    {/* ✅ PROPERTY GRID (ONLY THIS SHOULD BE GRID) */}
    {properties.length > 0 && (
      <div className="grid gap-6 md:grid-cols-2">
        {properties.map((p) => (
          <div
            key={String(p.external_id ?? p.id)}
            className="cursor-pointer text-left"
            onClick={() => setSelectedProperty(p)}
          >
            <PropertyResultCard
              property={p}
              returnTo={`${pathname}?${searchQueryString}`}
              onNavigate={saveCurrentSnapshot}
            />
          </div>
        ))}
      </div>
    )}

    {/* Bottom Section */}
    <Charts
      enabled={showInsights}
      locationLabel={coordinates?.label ?? ""}
      properties={properties}
      prefetchedInsight={prefetchedInsight}
    />
  </div>
);
}
