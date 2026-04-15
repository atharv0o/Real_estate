"use client";

import { useEffect, useState } from "react";

import { fetchAiInsights, getApiErrorMessage } from "@/lib/api";
import type { AiInsight, PropertyRecord } from "@/types/property";

import { PriceChart } from "./PriceChart";

type ChartsProps = {
  enabled: boolean;
  locationLabel: string;
  properties: PropertyRecord[];
  prefetchedInsight?: AiInsight | null;
};

export function Charts({ enabled, locationLabel, properties, prefetchedInsight }: ChartsProps) {
  const [insight, setInsight] = useState<AiInsight | null>(prefetchedInsight ?? null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (prefetchedInsight) {
      setInsight(prefetchedInsight);
      return;
    }
  }, [prefetchedInsight]);

  useEffect(() => {
    let ignore = false;

    async function loadInsights() {
      if (!enabled || !locationLabel || properties.length === 0) return;
      if (prefetchedInsight) return;
      setLoading(true);
      setError(null);
      try {
        const nextInsight = await fetchAiInsights(locationLabel, properties);
        if (!ignore) setInsight(nextInsight);
      } catch (err) {
        if (!ignore) setError(getApiErrorMessage(err));
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    void loadInsights();
    return () => {
      ignore = true;
    };
  }, [enabled, locationLabel, properties, prefetchedInsight]);

  if (!enabled) {
    return null;
  }

  return (
    <section className="space-y-4 rounded-2xl border border-white/10 bg-slate-900/40 p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="font-display text-xl font-semibold text-white">AI insights</h2>
          <p className="text-sm text-slate-400">RAG summary and price trend snapshot</p>
        </div>
        {loading && <span className="text-sm text-sky-300">Loading…</span>}
      </div>

      {error && <p className="text-sm text-rose-400">{error}</p>}

      {insight && (
        <>
          <p className="rounded-xl border border-white/5 bg-black/20 p-4 text-sm leading-6 text-slate-200">
            {insight.summary}
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-white/5 bg-black/20 p-4 sm:col-span-1">
              <p className="text-xs uppercase tracking-wide text-slate-500">Average price</p>
              <p className="mt-2 text-2xl font-semibold text-sky-300">
                ₹{insight.average_price.toLocaleString("en-IN")}
              </p>
              <p className="mt-1 text-sm text-slate-400">
                Based on {insight.property_count} nearby properties
              </p>
            </div>
            <div className="rounded-xl border border-white/5 bg-black/20 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-500">Price trend</p>
              <p className="mt-2 text-lg font-semibold capitalize text-violet-300">
                {insight.price_trend ?? "—"}
              </p>
            </div>
            <div className="rounded-xl border border-white/5 bg-black/20 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-500">Investment score</p>
              <p className="mt-2 text-lg font-semibold text-emerald-300">
                {insight.investment_score != null ? `${insight.investment_score} / 10` : "—"}
              </p>
            </div>
          </div>
          <PriceChart data={insight.price_trends} />
        </>
      )}
    </section>
  );
}
