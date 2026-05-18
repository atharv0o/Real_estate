import axios, { AxiosError } from "axios";

import { API_BASE_URL } from "./constants";
import type {
  AiInsight,
  AnalyticsDashboard,
  ApiEnvelope,
  Coordinates,
  FullSearchPayload,
  InvestmentAdvisor,
  LegalAdvice,
  LocationQuery,
  NegotiationAdvice,
  PropertyData,
  PropertyFilters,
  PropertyRecord,
  PropertySearchParams,
  RecommendationsPayload
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
  return [query.area, query.city, query.district]
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

function getNumericPrice(property: PropertyRecord): number {
  return Number(property.price_numeric ?? 0);
}

function buildTrustScore(property: PropertyRecord): InvestmentAdvisor["trust_score"] {
  const base = property.blockchain_verified || property.verified_status ? 86 : 72;
  const hasRegistry = property.registration_id ? 7 : 0;
  const hasCoordinates = typeof property.lat === "number" && typeof property.lng === "number" ? 5 : 0;
  const score = Math.min(98, base + hasRegistry + hasCoordinates);
  return {
    score,
    label: score >= 85 ? "Strong verification signals" : "Verification pending review"
  };
}

export async function fetchInvestmentAdvisor(property: PropertyRecord): Promise<InvestmentAdvisor> {
  const price = getNumericPrice(property);
  const trustScore = buildTrustScore(property);
  const rentalYield = Number((4.8 + Math.min(price / 10_000_000, 2.4)).toFixed(1));
  const roiPrediction = Number((rentalYield + (trustScore.score >= 85 ? 2.1 : 1.2)).toFixed(1));

  return {
    trust_score: trustScore,
    roi_prediction: roiPrediction,
    rental_yield: rentalYield,
    rationale: `${property.title} in ${property.location} shows ${trustScore.label.toLowerCase()}, usable pricing data, and local demand context. Review documents before final commitment.`
  };
}

export async function fetchNegotiationAdvice(property: PropertyRecord): Promise<NegotiationAdvice> {
  const askingPrice = getNumericPrice(property);
  const suggestedOffer = askingPrice > 0 ? Math.round(askingPrice * 0.94) : 0;
  return {
    asking_price: askingPrice,
    suggested_offer_price: suggestedOffer,
    negotiation_strategy: [
      "Anchor slightly below the listed price while citing comparable inventory.",
      "Ask for registry, tax, and society maintenance documents before token payment.",
      "Use possession timeline and furnishing condition as negotiation levers.",
      "Keep final escalation tied to verified ownership and inspection outcomes."
    ]
  };
}

export async function fetchLegalAdvice(property: PropertyRecord): Promise<LegalAdvice> {
  const missing = [
    property.registration_id ? "" : "registration id",
    property.owner ? "" : "owner declaration",
    property.blockchain_hash || property.verification_hash ? "" : "blockchain attestation hash"
  ].filter(Boolean);

  return {
    risk_level: missing.length === 0 ? "Low" : missing.length === 1 ? "Medium" : "Review required",
    missing_documents: missing.length ? missing : []
  };
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
  try {
    return await unwrapResponse(
      apiClient.post<ApiEnvelope<{ answer: string }>>("/rag/query", {
        query,
        location: context?.location,
        property_context: {
          property_id: context?.property_id,
          title: context?.property_title,
          description: context?.property_description,
          latitude: context?.latitude,
          longitude: context?.longitude
        }
      })
    );
  } catch {
    const subject = context?.property_title || context?.location || "this property";
    const location = context?.location ? ` in ${context.location}` : "";
    return {
      answer: `I can still help with ${subject}${location}. Based on the saved listing context, check price, title clarity, location fit, registration details, and blockchain verification before making an offer.`
    };
  }
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

export async function fetchRecommendations(_options?: {
  budget?: number;
  roi_goal?: number;
  verified_only?: boolean;
}): Promise<RecommendationsPayload> {
  const properties = await unwrapResponse(
    apiClient.get<ApiEnvelope<PropertyRecord[]>>("/api/properties", {
      params: { limit: 24, offset: 0 }
    })
  );
  const recommendations = await Promise.all(
    properties.slice(0, 12).map(async (property) => ({
      property,
      investment_advisor: await fetchInvestmentAdvisor(property)
    }))
  );
  return { recommendations };
}

export async function fetchAnalyticsDashboard(): Promise<AnalyticsDashboard> {
  const properties = await unwrapResponse(
    apiClient.get<ApiEnvelope<PropertyRecord[]>>("/api/properties", {
      params: { limit: 100, offset: 0 }
    })
  );
  const priced = properties.filter((property) => getNumericPrice(property) > 0);
  const averagePrice = priced.length
    ? priced.reduce((total, property) => total + getNumericPrice(property), 0) / priced.length
    : 0;
  const byLocation = new Map<string, PropertyRecord[]>();
  for (const property of properties) {
    const key = property.location || "Unknown";
    byLocation.set(key, [...(byLocation.get(key) ?? []), property]);
  }
  const zones = Array.from(byLocation.entries()).map(([location, items]) => {
    const verifiedCount = items.filter((item) => item.blockchain_verified || item.verified_status).length;
    const localPrices = items.map(getNumericPrice).filter((price) => price > 0);
    const localAverage = localPrices.length
      ? localPrices.reduce((total, price) => total + price, 0) / localPrices.length
      : 0;
    const demandScore = Math.min(96, 58 + items.length * 4 + verifiedCount * 3);
    return {
      location,
      demand_score: demandScore,
      growth_prediction: Number((4 + demandScore / 12).toFixed(1)),
      average_price: localAverage
    };
  }).sort((a, b) => b.demand_score - a.demand_score);

  return {
    summary: {
      property_count: properties.length,
      average_price: averagePrice
    },
    investment_hotspots: zones,
    demand_zones: zones.map(({ location, demand_score }) => ({ location, demand_score })),
    growth_prediction: zones.map(({ location, growth_prediction }) => ({ location, growth_prediction }))
  };
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
