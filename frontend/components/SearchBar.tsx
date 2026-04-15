"use client";

import { ChangeEvent, FormEvent, useCallback, useState } from "react";

import { MIN_AREA_LENGTH, PIN_CODE_REGEX } from "@/lib/constants";
import { getApiErrorMessage, postSearch, resolveLocation } from "@/lib/api";
import type { Coordinates, FullSearchPayload, LocationQuery, PropertyFilters } from "@/types/property";

export type SearchBarProps = {
  initialValues?: Partial<LocationQuery>;
  onResolved?: (coords: Coordinates, query: LocationQuery) => void;
  /** When set with filters, submits POST /api/search (full pipeline) instead of GET /location only. */
  filters?: PropertyFilters;
  onFullSearch?: (payload: FullSearchPayload, query: LocationQuery) => void;
  className?: string;
};

type FieldErrors = Partial<Record<keyof LocationQuery, string>>;

function validate(values: LocationQuery): FieldErrors {
  const errors: FieldErrors = {};

  if (!values.district.trim()) errors.district = "District is required";
  if (!values.city.trim()) errors.city = "City is required";
  if (!values.area.trim() || values.area.trim().length < MIN_AREA_LENGTH) {
    errors.area = `Area must be at least ${MIN_AREA_LENGTH} characters`;
  }
  if (!PIN_CODE_REGEX.test(values.pinCode.trim())) {
    errors.pinCode = "PIN code must be exactly 6 digits";
  }
  if (!values.landAreaCode.trim()) {
    errors.landAreaCode = "Land / area code is required";
  }

  return errors;
}

export function SearchBar({
  initialValues,
  onResolved,
  filters,
  onFullSearch,
  className = ""
}: SearchBarProps) {
  const [values, setValues] = useState<LocationQuery>({
    district: initialValues?.district ?? "",
    city: initialValues?.city ?? "",
    area: initialValues?.area ?? "",
    pinCode: initialValues?.pinCode ?? "",
    landAreaCode: initialValues?.landAreaCode ?? ""
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const onChange =
    (key: keyof LocationQuery) =>
    (e: ChangeEvent<HTMLInputElement>) => {
      setValues((v) => ({ ...v, [key]: e.target.value }));
      setErrors((er) => ({ ...er, [key]: undefined }));
    };

  const onSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      const next: LocationQuery = {
        district: values.district.trim(),
        city: values.city.trim(),
        area: values.area.trim(),
        pinCode: values.pinCode.trim(),
        landAreaCode: values.landAreaCode.trim()
      };
      const v = validate(next);
      if (Object.keys(v).length > 0) {
        setErrors(v);
        return;
      }

      setSubmitting(true);
      setApiError(null);
      try {
        if (onFullSearch && filters) {
          const coordinates = await resolveLocation(next);
          onResolved?.(coordinates, next);

          const payload = await postSearch(next, filters);
          onFullSearch(payload, next);
        } else {
          const coordinates = await resolveLocation(next);
          onResolved?.(coordinates, next);
        }
      } catch (error) {
        setApiError(getApiErrorMessage(error));
      } finally {
        setSubmitting(false);
      }
    },
    [onResolved, onFullSearch, filters, values]
  );

  const inputClass =
    "w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-sky-400/50 focus:ring-2 focus:ring-sky-500/20";

  return (
    <form
      onSubmit={onSubmit}
      className={`rounded-3xl border border-white/10 bg-slate-900/40 p-6 shadow-glass backdrop-blur-xl md:p-8 ${className}`}
    >
      <div className="mb-6 flex flex-col gap-2">
        <h2 className="font-display text-xl font-semibold tracking-tight text-white md:text-2xl">
          Find intelligence for any locality
        </h2>
        <p className="text-sm text-slate-400">
          Enter location details — we&apos;ll map the pin and fetch area insights.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            District
          </span>
          <input
            name="district"
            className={inputClass}
            placeholder="e.g. South Delhi"
            value={values.district}
            onChange={onChange("district")}
            autoComplete="address-level2"
          />
          {errors.district && (
            <span className="text-xs text-rose-400">{errors.district}</span>
          )}
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            City
          </span>
          <input
            name="city"
            className={inputClass}
            placeholder="e.g. New Delhi"
            value={values.city}
            onChange={onChange("city")}
            autoComplete="address-level1"
          />
          {errors.city && (
            <span className="text-xs text-rose-400">{errors.city}</span>
          )}
        </label>

        <label className="flex flex-col gap-1.5 sm:col-span-2 lg:col-span-1">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            Area
          </span>
          <input
            name="area"
            className={inputClass}
            placeholder="Neighborhood or sector"
            value={values.area}
            onChange={onChange("area")}
          />
          {errors.area && (
            <span className="text-xs text-rose-400">{errors.area}</span>
          )}
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            PIN code
          </span>
          <input
            name="pinCode"
            inputMode="numeric"
            maxLength={6}
            className={inputClass}
            placeholder="110001"
            value={values.pinCode}
            onChange={onChange("pinCode")}
            autoComplete="postal-code"
          />
          {errors.pinCode && (
            <span className="text-xs text-rose-400">{errors.pinCode}</span>
          )}
        </label>

        <label className="flex flex-col gap-1.5 sm:col-span-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            Land / area code
          </span>
          <input
            name="landAreaCode"
            className={inputClass}
            placeholder="Survey / plot / cadastral reference"
            value={values.landAreaCode}
            onChange={onChange("landAreaCode")}
          />
          {errors.landAreaCode && (
            <span className="text-xs text-rose-400">{errors.landAreaCode}</span>
          )}
        </label>
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-4">
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 px-8 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-sky-500/25 transition hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-sky-400/50"
        >
          {submitting ? (onFullSearch ? "Searching pipeline…" : "Resolving...") : "Search area"}
        </button>
        <span className="text-xs text-slate-500">
          Results are fetched from the backend using live coordinates.
        </span>
      </div>
      {apiError && <p className="mt-3 text-sm text-rose-400">{apiError}</p>}
    </form>
  );
}
