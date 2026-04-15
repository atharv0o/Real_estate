import axios, { AxiosError } from "axios";

import { API_BASE_URL } from "./constants";
import type {
  AiInsight,
  ApiEnvelope,
  Coordinates,
  FullSearchPayload,
  LocationQuery,
  PropertyData,
  PropertyFilters,
  PropertyRecord,
  PropertySearchParams
} from "@/types/property";

const REQUEST_TIMEOUT_MS = 30_000;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: REQUEST_TIMEOUT_MS
});

function normalizeError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ error?: string; message?: string }>;
    return (
      axiosError.response?.data?.error ||
      axiosError.response?.data?.message ||
      axiosError.message ||
      "Request failed"
    );
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong";
}

async function unwrapResponse<T>(request: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  const response = await request;
  const payload = response.data;
  if (!payload.success) {
    throw new Error(payload.error || "Request failed");
  }
  return payload.data;
}

function buildLocationQuery(query: LocationQuery): string {
  return [query.area, query.city, query.district, query.pinCode, query.landAreaCode]
    .filter(Boolean)
    .join(", ");
}

export async function resolveLocation(query: LocationQuery): Promise<Coordinates> {
  return unwrapResponse(
    apiClient.get<ApiEnvelope<Coordinates>>("/api/location", {
      params: { query: buildLocationQuery(query) }
    })
  );
}

function normalizeInsights(raw: Record<string, unknown>): AiInsight {
  const priceTrends = (raw.price_trends as AiInsight["price_trends"]) || [];
  const avg = Number(raw.average_price ?? raw.avg_price ?? 0);
  return {
    summary: String(raw.summary ?? ""),
    price_trends: priceTrends,
    average_price: avg,
    property_count: Number(raw.property_count ?? 0),
    price_trend: raw.price_trend as AiInsight["price_trend"],
    investment_score: Number(raw.investment_score ?? 0),
    avg_price: Number(raw.avg_price ?? avg)
  };
}

export async function postSearch(
  query: LocationQuery,
  filters: PropertyFilters
): Promise<FullSearchPayload> {
  const data = await unwrapResponse(
    apiClient.post<ApiEnvelope<FullSearchPayload>>("/api/search", {
      area: query.area,
      city: query.city,
      district: query.district,
      pinCode: query.pinCode,
      landAreaCode: query.landAreaCode,
      radius: filters.radius,
      minPrice: filters.minPrice,
      maxPrice: filters.maxPrice
    })
  );
  return {
    ...data,
    insights: normalizeInsights(data.insights as unknown as Record<string, unknown>)
  };
}

export async function searchLand(
  coords: Pick<Coordinates, "lat" | "lng">,
  filters: PropertyFilters
): Promise<PropertyRecord[]> {
  return unwrapResponse(
    apiClient.get<ApiEnvelope<PropertyRecord[]>>("/api/land/search", {
      params: {
        lat: coords.lat,
        lng: coords.lng,
        radius: filters.radius,
        min_price: filters.minPrice,
        max_price: filters.maxPrice
      }
    })
  );
}

export async function fetchPropertyById(propertyId: string): Promise<PropertyRecord> {
  return unwrapResponse(
    apiClient.get<ApiEnvelope<PropertyRecord>>(`/api/property/${propertyId}`)
  );
}

export async function queryRag(
  query: string,
  context?: {
    property_id?: string;
    location?: string;
    property_description?: string;
    property_title?: string;
    latitude?: number | null;
    longitude?: number | null;
  }
): Promise<{ answer: string }> {
  return unwrapResponse(
    apiClient.post<ApiEnvelope<{ answer: string }>>("/rag/query", {
      query,
      ...context
    })
  );
}

export async function fetchAiInsights(
  locationLabel: string,
  properties: PropertyRecord[]
): Promise<AiInsight> {
  return unwrapResponse(
    apiClient.post<ApiEnvelope<AiInsight>>("/api/ai-insights", {
      query: `Provide real estate insights for ${locationLabel}.`,
      location: locationLabel,
      properties
    })
  );
}

export function getApiErrorMessage(error: unknown): string {
  return normalizeError(error);
}

export function getMockPropertyData(params: PropertySearchParams): PropertyData {
  const slug = [params.area, params.city, params.district]
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
    imageUrl: "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&q=80",
    freshnessHours: 6,
    blockchainVerified: true,
    lat: null,
    lng: null,
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

export async function fetchPropertyData(params: PropertySearchParams): Promise<PropertyData> {
  const properties = await searchLand(
    await resolveLocation(params),
    { radius: 5, minPrice: undefined, maxPrice: undefined }
  );

  if (properties.length === 0) {
    return getMockPropertyData(params);
  }

  const first = properties[0];
  return {
    id: String(first.external_id ?? first.id),
    areaName: first.title,
    pricePerSqFt: Number(first.price_numeric ?? 0),
    trend: "up",
    trendPercent: 0,
    imageUrl: "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&q=80",
    freshnessHours: 1,
    blockchainVerified: Boolean(first.blockchain_verified),
    lat: first.lat ?? null,
    lng: first.lng ?? null,
    priceHistory: properties.slice(0, 6).map((property, index) => ({
      month: `P${index + 1}`,
      value: Number(property.price_numeric ?? 0)
    }))
  };
}
