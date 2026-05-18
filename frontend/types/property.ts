export type LocationQuery = {
  district: string;
  city: string;
  area: string;
  pinCode: string;
  landAreaCode: string;
};

export type Coordinates = {
  query: string;
  label: string;
  lat: number;
  lng: number;
  source: string;
};

export type PropertyFilters = {
  radius: number;
  minPrice?: number;
  maxPrice?: number;
};

export type PropertyRecord = {
  id: number;
  external_id?: string;
  title: string;
  price: string;
  price_numeric?: number;
  location: string;
  area_sqft?: number | null;
  source?: string;
  description?: string;
  owner?: string | null;
  registration_id?: string | null;
  verified_status?: boolean | null;
  lat?: number | null;
  lng?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  distance_km?: number;
  blockchain_verified?: boolean;
  blockchain_hash?: string | null;
  blockchain_tx_id?: string | null;
  verification_hash?: string | null;
  ai_summary?: string;
  trust_score?: number;
  trust_label?: string;
  created_at?: string;
  updated_at?: string;
};

export type AiInsight = {
  summary: string;
  price_trends: { label: string; value: number }[];
  average_price: number;
  property_count: number;
  price_trend?: string;
  investment_score?: number;
  avg_price?: number;
};

export type FullSearchPayload = {
  coordinates: Coordinates;
  properties: PropertyRecord[];
  insights: AiInsight;
  count: number;
  store?: { upserted: number; vector_notify_count: number };
};

export type TrustScore = {
  score: number;
  label: string;
};

export type InvestmentAdvisor = {
  trust_score: TrustScore;
  roi_prediction: number;
  rental_yield: number;
  rationale: string;
};

export type NegotiationAdvice = {
  asking_price: number;
  suggested_offer_price: number;
  negotiation_strategy: string[];
};

export type LegalAdvice = {
  risk_level: string;
  missing_documents: string[];
};

export type Recommendation = {
  property: PropertyRecord;
  investment_advisor: InvestmentAdvisor;
};

export type RecommendationsPayload = {
  recommendations: Recommendation[];
};

export type AnalyticsDashboard = {
  summary: {
    property_count: number;
    average_price: number;
  };
  investment_hotspots: {
    location: string;
    demand_score: number;
    growth_prediction: number;
    average_price: number;
  }[];
  demand_zones: {
    location: string;
    demand_score: number;
  }[];
  growth_prediction: {
    location: string;
    growth_prediction: number;
  }[];
};

export type ApiEnvelope<T> = {
  success: boolean;
  status?: string;
  data: T;
  error: string | null;
};

export type PropertySearchParams = LocationQuery;

export type PropertyTrend = "up" | "down" | "flat";

export type PropertyData = {
  id: string;
  areaName: string;
  pricePerSqFt: number;
  trend: PropertyTrend;
  trendPercent: number;
  imageUrl: string;
  freshnessHours: number;
  blockchainVerified: boolean;
  lat?: number | null;
  lng?: number | null;
  priceHistory?: { month: string; value: number }[];
};
