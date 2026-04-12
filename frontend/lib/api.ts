import axios, { type AxiosError } from "axios";

import { API_BASE_URL } from "./constants";
import type { PropertySearchParams, PropertyData } from "@/types/property";

/**
 * Axios client for the RealestateRag backend.
 * Base URL defaults to http://localhost:5000 (override via NEXT_PUBLIC_API_URL).
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000
});

/** Deterministic mock when backend is unavailable or NEXT_PUBLIC_USE_MOCK_API=true */
export function getMockPropertyData(params: PropertySearchParams): PropertyData {
  const slug = [
    params.area,
    params.city,
    params.district
  ]
    .filter(Boolean)
    .join("-")
    .toLowerCase()
    .replace(/\s+/g, "-") || "sample-area";

  return {
    id: `mock-${slug}`,
    areaName: params.area || params.city || "Selected area",
    pricePerSqFt: 8450 + (params.pinCode.length % 7) * 120,
    trend: "up",
    trendPercent: 3.2,
    imageUrl: `https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&q=80`,
    freshnessHours: 6,
    blockchainVerified: true,
    priceHistory: [
      { month: "Jan", value: 7800 },
      { month: "Feb", value: 7950 },
      { month: "Mar", value: 8100 },
      { month: "Apr", value: 8200 },
      { month: "May", value: 8320 },
      { month: "Jun", value: 8450 }
    ]
  };
}

/**
 * Fetches aggregated property / area intelligence from the backend.
 * GET /api/property-data?district=...&city=...
 *
 * Set NEXT_PUBLIC_USE_MOCK_API=true to skip the network (local demos without a server).
 */
export async function fetchPropertyData(
  params: PropertySearchParams
): Promise<PropertyData> {
  if (process.env.NEXT_PUBLIC_USE_MOCK_API === "true") {
    await new Promise((r) => setTimeout(r, 600));
    return getMockPropertyData(params);
  }

  const { data } = await apiClient.get<PropertyData>("/api/property-data", {
    params: {
      district: params.district,
      city: params.city,
      area: params.area,
      pinCode: params.pinCode,
      landAreaCode: params.landAreaCode
    }
  });
  return data;
}

/** Typed error helper for UI */
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const ax = error as AxiosError<{ message?: string }>;
    return ax.response?.data?.message ?? ax.message ?? "Request failed";
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong";
}
