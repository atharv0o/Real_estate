import { create } from "zustand";

import type { PropertyData, PropertySearchParams } from "@/types/property";

type PropertyStoreState = {
  searchParams: PropertySearchParams | null;
  propertyData: PropertyData | null;
  loading: boolean;
  setSearchParams: (p: PropertySearchParams | null) => void;
  setPropertyData: (d: PropertyData | null) => void;
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
  loading: false,

  setSearchParams: (searchParams) => set({ searchParams }),
  setPropertyData: (propertyData) => set({ propertyData }),
  setLoading: (loading) => set({ loading }),

  reset: () =>
    set({
      searchParams: null,
      propertyData: null,
      loading: false
    })
}));

export { emptyParams };
