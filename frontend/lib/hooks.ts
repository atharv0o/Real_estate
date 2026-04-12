"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import type { PropertySearchParams } from "@/types/property";

/**
 * Reads search-related query params from the current URL into a typed object.
 */
export function useSearchParamsFromUrl(): PropertySearchParams | null {
  const searchParams = useSearchParams();

  return useMemo(() => {
    const district = searchParams.get("district") ?? "";
    const city = searchParams.get("city") ?? "";
    const area = searchParams.get("area") ?? "";
    const pinCode = searchParams.get("pinCode") ?? "";
    const landAreaCode = searchParams.get("landAreaCode") ?? "";

    if (!district && !city && !area && !pinCode && !landAreaCode) {
      return null;
    }

    return { district, city, area, pinCode, landAreaCode };
  }, [searchParams]);
}

/**
 * Debounced value for inputs that should not fire on every keystroke.
 */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(id);
  }, [value, delayMs]);

  return debounced;
}

/**
 * Mock geocoding: deterministic lat/lng from query string (replace with Google Maps Geocoding in prod).
 */
export function useMockGeocode(
  params: PropertySearchParams | null
): { lat: number; lng: number; label: string } | null {
  return useMemo(() => {
    if (!params) return null;
    const seed =
      params.city +
      params.area +
      params.pinCode +
      params.district +
      params.landAreaCode;
    if (!seed.trim()) return null;

    // Simple hash → pseudo coordinates near DEFAULT_MAP_CENTER region
    let h = 0;
    for (let i = 0; i < seed.length; i++) {
      h = Math.imul(31, h) + seed.charCodeAt(i);
      h |= 0;
    }
    const lat = 28.4 + ((h >>> 0) % 500) / 5000;
    const lng = 77.0 + (((h >>> 8) % 500) / 5000);

    return {
      lat,
      lng,
      label: [params.area, params.city, params.district]
        .filter(Boolean)
        .join(", ")
    };
  }, [params]);
}

