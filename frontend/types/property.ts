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
  distance_km?: number;
  blockchain_verified?: boolean;
  blockchain_hash?: string | null;
  blockchain_tx_id?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type AiInsight = {
  summary: string;
  price_trends: { label: string; value: number }[];
  average_price: number;
  property_count: number;
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
  priceHistory?: { month: string; value: number }[];
};
