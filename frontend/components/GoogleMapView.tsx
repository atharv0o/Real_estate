"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { getApiErrorMessage, searchLand } from "@/lib/api";
import type { Coordinates, PropertyFilters, PropertyRecord } from "@/types/property";

type GoogleMapViewProps = {
  coordinates: Coordinates | null;
  filters: PropertyFilters;
  onResultsChange?: (results: PropertyRecord[]) => void;
  externalResults?: PropertyRecord[] | null;
};

declare global {
  interface Window {
    google?: typeof google;
    __googleMapsPromise?: Promise<typeof google>;
  }

  namespace google.maps {
    class Map {
      constructor(mapDiv: Element, opts?: MapOptions);
      fitBounds(bounds: LatLngBounds | LatLngBoundsLiteral, padding?: number): void;
      setCenter(latLng: LatLngLiteral): void;
      setZoom(zoom: number): void;
    }

    class Marker {
      constructor(opts?: MarkerOptions);
      setMap(map: Map | null): void;
    }

    class Circle {
      constructor(opts?: CircleOptions);
      setMap(map: Map | null): void;
    }

    class InfoWindow {
      constructor(opts?: InfoWindowOptions);
      close(): void;
      setContent(content: string): void;
      open(opts?: { anchor?: Marker; map?: Map }): void;
    }

    class LatLngBounds {
      extend(latLng: LatLngLiteral): void;
    }

    interface MapOptions {
      center?: LatLngLiteral;
      zoom?: number;
      mapTypeControl?: boolean;
      streetViewControl?: boolean;
      fullscreenControl?: boolean;
      styles?: unknown[];
    }

    interface MarkerOptions {
      map?: Map | null;
      position?: LatLngLiteral;
      title?: string;
      icon?: string | Icon;
    }

    interface CircleOptions {
      map?: Map | null;
      center?: LatLngLiteral;
      radius?: number;
      strokeColor?: string;
      strokeOpacity?: number;
      strokeWeight?: number;
      fillColor?: string;
      fillOpacity?: number;
    }

    interface InfoWindowOptions {
      content?: string;
    }

    interface Icon {
      path?: number;
      fillColor?: string;
      fillOpacity?: number;
      strokeColor?: string;
      strokeWeight?: number;
      scale?: number;
    }

    interface LatLngLiteral {
      lat: number;
      lng: number;
    }

    interface LatLngBoundsLiteral {
      east: number;
      north: number;
      south: number;
      west: number;
    }

    namespace event {
      function addListener(
        instance: object,
        eventName: string,
        handler: () => void
      ): { remove(): void };
      function clearInstanceListeners(instance: object): void;
    }

    const SymbolPath: {
      CIRCLE: number;
    };
  }
}

const GOOGLE_MAPS_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function loadGoogleMaps(key: string): Promise<typeof google | null> {
  if (!key || typeof window === "undefined") {
    return null;
  }

  if (window.google?.maps) {
    return window.google;
  }

  if (!window.__googleMapsPromise) {
    window.__googleMapsPromise = new Promise<typeof google>((resolve, reject) => {
      const existing = document.querySelector<HTMLScriptElement>("script[data-google-maps-loader='true']");
      if (existing) {
        existing.addEventListener("load", () => {
          if (window.google?.maps) {
            resolve(window.google);
          }
        });
        existing.addEventListener("error", () => reject(new Error("Failed to load Google Maps")));
        return;
      }

      const script = document.createElement("script");
      script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}`;
      script.async = true;
      script.defer = true;
      script.dataset.googleMapsLoader = "true";
      script.onload = () => {
        if (window.google?.maps) {
          resolve(window.google);
        } else {
          reject(new Error("Google Maps loaded without the maps namespace"));
        }
      };
      script.onerror = () => reject(new Error("Failed to load Google Maps"));
      document.head.appendChild(script);
    });
  }

  return window.__googleMapsPromise;
}

export function GoogleMapView({
  coordinates,
  filters,
  onResultsChange,
  externalResults
}: GoogleMapViewProps) {
  const [results, setResults] = useState<PropertyRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  const mapElementRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const infoWindowRef = useRef<google.maps.InfoWindow | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const circleRef = useRef<google.maps.Circle | null>(null);

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

  const mappableResults = useMemo(
    () =>
      results.filter(
        (result) =>
          typeof result.lat === "number" &&
          Number.isFinite(result.lat) &&
          typeof result.lng === "number" &&
          Number.isFinite(result.lng)
      ),
    [results]
  );

  useEffect(() => {
    let ignore = false;

    async function initMap() {
      if (!coordinates || !mapElementRef.current) {
        setMapReady(false);
        return;
      }

      const api = await loadGoogleMaps(GOOGLE_MAPS_API_KEY);
      if (ignore) {
        return;
      }

      if (!api?.maps) {
        setMapReady(false);
        setMapError(
          GOOGLE_MAPS_API_KEY
            ? "Google Maps could not be loaded. Showing embedded map instead."
            : "Showing embedded Google map. Add NEXT_PUBLIC_GOOGLE_MAPS_API_KEY for full interactive markers."
        );
        return;
      }

      const center = { lat: coordinates.lat, lng: coordinates.lng };
      setMapError(null);

      if (!mapRef.current) {
        mapRef.current = new api.maps.Map(mapElementRef.current, {
          center,
          zoom: 13,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: false,
          styles: [
            { elementType: "geometry", stylers: [{ color: "#0f172a" }] },
            { elementType: "labels.text.stroke", stylers: [{ color: "#0f172a" }] },
            { elementType: "labels.text.fill", stylers: [{ color: "#94a3b8" }] },
            { featureType: "road", elementType: "geometry", stylers: [{ color: "#1e293b" }] },
            { featureType: "water", elementType: "geometry", stylers: [{ color: "#0c4a6e" }] },
            { featureType: "poi", stylers: [{ visibility: "off" }] }
          ]
        });
        infoWindowRef.current = new api.maps.InfoWindow();
      } else {
        mapRef.current.setCenter(center);
        mapRef.current.setZoom(13);
      }

      markersRef.current.forEach((marker) => {
        api.maps.event.clearInstanceListeners(marker);
        marker.setMap(null);
      });
      markersRef.current = [];
      circleRef.current?.setMap(null);

      circleRef.current = new api.maps.Circle({
        map: mapRef.current,
        center,
        radius: filters.radius * 1000,
        strokeColor: "#38bdf8",
        strokeOpacity: 0.85,
        strokeWeight: 2,
        fillColor: "#0ea5e9",
        fillOpacity: 0.12
      });

      const bounds = new api.maps.LatLngBounds();
      bounds.extend(center);

      const centerMarker = new api.maps.Marker({
        map: mapRef.current,
        position: center,
        title: coordinates.label,
        icon: {
          path: api.maps.SymbolPath.CIRCLE,
          fillColor: "#f8fafc",
          fillOpacity: 1,
          strokeColor: "#0ea5e9",
          strokeWeight: 4,
          scale: 8
        }
      });
      markersRef.current.push(centerMarker);

      mappableResults.slice(0, 40).forEach((property) => {
        const marker = new api.maps.Marker({
          map: mapRef.current,
          position: { lat: Number(property.lat), lng: Number(property.lng) },
          title: property.title
        });

        api.maps.event.addListener(marker, "click", () => {
          const content = `
            <div style="max-width:240px;padding:4px 2px;color:#0f172a">
              <div style="font-weight:700;margin-bottom:6px;">${escapeHtml(property.title)}</div>
              <div style="font-size:12px;margin-bottom:4px;">${escapeHtml(property.location)}</div>
              <div style="font-size:12px;color:#0369a1;">${escapeHtml(property.price ?? "")}</div>
            </div>
          `;
          infoWindowRef.current?.close();
          infoWindowRef.current?.setContent(content);
          infoWindowRef.current?.open({ anchor: marker, map: mapRef.current ?? undefined });
        });

        markersRef.current.push(marker);
        bounds.extend({ lat: Number(property.lat), lng: Number(property.lng) });
      });

      mapRef.current.fitBounds(bounds, 80);
      setMapReady(true);
    }

    void initMap().catch((err: unknown) => {
      if (!ignore) {
        setMapReady(false);
        setMapError(err instanceof Error ? err.message : "Google Maps failed to initialize.");
      }
    });

    return () => {
      ignore = true;
    };
  }, [coordinates, filters.radius, mappableResults]);

  const mapEmbedUrl = coordinates
    ? `https://www.google.com/maps?q=${coordinates.lat},${coordinates.lng}&z=13&output=embed`
    : null;

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
        <div className="absolute left-3 top-3 z-10 rounded-lg bg-black/60 px-3 py-1 text-[10px] text-slate-300">
          {useExternal ? "Pipeline search" : "Live search"}
        </div>

        {coordinates ? (
          <>
            {mapEmbedUrl && (
              <iframe
                title={`Google map for ${coordinates.label}`}
                src={mapEmbedUrl}
                className={`absolute inset-0 h-full w-full border-0 ${mapReady ? "opacity-0" : "opacity-100"}`}
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            )}
            <div
              ref={mapElementRef}
              className={`absolute inset-0 h-full w-full transition-opacity ${mapReady ? "opacity-100" : "opacity-0"}`}
            />
            {!mapReady && (
              <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/90 to-transparent px-4 py-3 text-xs text-slate-300">
                {mapError ?? "Loading Google map..."}
              </div>
            )}
          </>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950/40 px-6 text-center text-sm text-slate-400">
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
          {loading && <p>Loading nearby properties...</p>}
          {error && <p className="text-rose-400">{error}</p>}
          {!loading && !error && coordinates && results.length === 0 && (
            <p>No properties found for this search.</p>
          )}
          {!loading && results.length > 0 && (
            <ul className="space-y-1">
              {results.slice(0, 4).map((result, index) => (
                <li key={`${result.external_id ?? result.id ?? result.title}-${index}`} className="truncate">
                  {result.title} - {result.location}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
