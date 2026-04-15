import { create } from "zustand";

import type { PropertyData, PropertyRecord, PropertySearchParams } from "@/types/property";

type PropertyContext = {
  propertyId?: string;
  title?: string;
  location?: string;
  description?: string;
  latitude?: number | null;
  longitude?: number | null;
};

type PropertyStoreState = {
  searchParams: PropertySearchParams | null;
  propertyData: PropertyData | null;
  activePropertyContext: PropertyContext | null;
  loading: boolean;
  setSearchParams: (p: PropertySearchParams | null) => void;
  setPropertyData: (d: PropertyData | null) => void;
  setActivePropertyContext: (context: PropertyContext | null) => void;
  setPropertyContextFromRecord: (record: PropertyRecord | null) => void;
  setLoading: (v: boolean) => void;
  reset: () => void;
};

const emptyParams: PropertySearchParams = {
  district: "",
  city: "",
  area: "",
  pinCode: "",
  landAreaCode: ""
};

export const usePropertyStore = create<PropertyStoreState>((set) => ({
  searchParams: null,
  propertyData: null,
  activePropertyContext: null,
  loading: false,

  setSearchParams: (searchParams) => set({ searchParams }),
  setPropertyData: (propertyData) => set({ propertyData }),
  setActivePropertyContext: (activePropertyContext) => set({ activePropertyContext }),
  setPropertyContextFromRecord: (record) =>
    set({
      activePropertyContext: record
        ? {
            propertyId: String(record.external_id ?? record.id),
            title: record.title,
            location: record.location,
            description: record.description,
            latitude: record.lat ?? null,
            longitude: record.lng ?? null
          }
        : null
    }),
  setLoading: (loading) => set({ loading }),

  reset: () =>
    set({
      searchParams: null,
      propertyData: null,
      activePropertyContext: null,
      loading: false
    })
}));

export { emptyParams };
