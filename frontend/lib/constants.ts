/** API and app-wide constants */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Default map center (India — approximate) when no coords */
export const DEFAULT_MAP_CENTER = { lat: 28.6139, lng: 77.209 };

/** Validation helpers */
export const PIN_CODE_REGEX = /^\d{6}$/;

export const MIN_AREA_LENGTH = 2;
