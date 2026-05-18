import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type {
  AiInsight,
  Coordinates,
  PropertyData,
  PropertyFilters,
  PropertyRecord,
  PropertySearchParams
} from "@/types/property";

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
  homeSearchState: HomeSearchState;
  loading: boolean;
  setSearchParams: (p: PropertySearchParams | null) => void;
  setPropertyData: (d: PropertyData | null) => void;
  setActivePropertyContext: (context: PropertyContext | null) => void;
  setPropertyContextFromRecord: (record: PropertyRecord | null) => void;
  setHomeSearchState: (state: Partial<HomeSearchState>) => void;
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

const defaultFilters: PropertyFilters = {
  radius: 5,
  minPrice: undefined,
  maxPrice: undefined
};

type HomeSearchState = {
  coordinates: Coordinates | null;
  lastQuery: PropertySearchParams | null;
  filters: PropertyFilters;
  properties: PropertyRecord[];
  pipelineResults: PropertyRecord[] | undefined;
  prefetchedInsight: AiInsight | null;
  selectedProperty: PropertyRecord | null;
  showInsights: boolean;
  scrollY: number;
};

const emptyHomeSearchState: HomeSearchState = {
  coordinates: null,
  lastQuery: null,
  filters: defaultFilters,
  properties: [],
  pipelineResults: undefined,
  prefetchedInsight: null,
  selectedProperty: null,
  showInsights: false,
  scrollY: 0
};

export const usePropertyStore = create<PropertyStoreState>()(
  persist(
    (set) => ({
      searchParams: null,
      propertyData: null,
      activePropertyContext: null,
      homeSearchState: emptyHomeSearchState,
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
      setHomeSearchState: (homeSearchState) =>
        set((state) => ({
          homeSearchState: { ...state.homeSearchState, ...homeSearchState }
        })),
      setLoading: (loading) => set({ loading }),

      reset: () =>
        set({
          searchParams: null,
          propertyData: null,
          activePropertyContext: null,
          homeSearchState: emptyHomeSearchState,
          loading: false
        })
    }),
    {
      name: "real-estate-property-state",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        searchParams: state.searchParams,
        propertyData: state.propertyData,
        homeSearchState: state.homeSearchState
      })
    }
  )
);

export { emptyParams };
