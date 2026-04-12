"use client";

import { useMemo } from "react";

import type { PropertyFilters } from "@/types/property";

type FiltersProps = {
  value: PropertyFilters;
  onChange: (value: PropertyFilters) => void;
};

export function Filters({ value, onChange }: FiltersProps) {
  const normalizedMaxPrice = useMemo(
    () => (typeof value.maxPrice === "number" ? value.maxPrice : ""),
    [value.maxPrice]
  );

  return (
    <div className="grid gap-4 rounded-2xl border border-white/10 bg-slate-900/40 p-4 md:grid-cols-3">
      <label className="flex flex-col gap-2 text-sm text-slate-300">
        <span className="text-xs uppercase tracking-wide text-slate-500">Radius (km)</span>
        <input
          type="range"
          min={1}
          max={25}
          step={1}
          value={value.radius}
          onChange={(event) =>
            onChange({ ...value, radius: Number(event.target.value) || 5 })
          }
        />
        <span className="text-sm font-medium text-white">{value.radius} km</span>
      </label>

      <label className="flex flex-col gap-2 text-sm text-slate-300">
        <span className="text-xs uppercase tracking-wide text-slate-500">Min price</span>
        <input
          type="number"
          min={0}
          placeholder="0"
          value={value.minPrice ?? ""}
          onChange={(event) =>
            onChange({
              ...value,
              minPrice: event.target.value ? Number(event.target.value) : undefined
            })
          }
          className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:ring-2 focus:ring-sky-500/30"
        />
      </label>

      <label className="flex flex-col gap-2 text-sm text-slate-300">
        <span className="text-xs uppercase tracking-wide text-slate-500">Max price</span>
        <input
          type="number"
          min={0}
          placeholder="No max"
          value={normalizedMaxPrice}
          onChange={(event) =>
            onChange({
              ...value,
              maxPrice: event.target.value ? Number(event.target.value) : undefined
            })
          }
          className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:ring-2 focus:ring-sky-500/30"
        />
      </label>
    </div>
  );
}
