/** Shared property / search types */

export type PropertySearchParams = {
  district: string;
  city: string;
  area: string;
  pinCode: string;
  landAreaCode: string;
};

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
  /** Optional series for charts */
  priceHistory?: { month: string; value: number }[];
};
