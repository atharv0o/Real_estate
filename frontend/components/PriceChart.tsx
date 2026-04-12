"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export type PriceChartProps = {
  data: { month: string; value: number }[];
  className?: string;
};

/**
 * Bonus: lightweight price trend visualization (dummy or API-fed series).
 */
export function PriceChart({ data, className = "" }: PriceChartProps) {
  if (!data?.length) return null;

  return (
    <div className={`h-64 w-full rounded-2xl border border-white/10 bg-slate-900/40 p-4 ${className}`}>
      <p className="mb-2 text-sm font-medium text-slate-300">Price trend (₹ / sq ft)</p>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
          <XAxis
            dataKey="month"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `₹${v}`}
          />
          <Tooltip
            contentStyle={{
              background: "rgba(15,23,42,0.95)",
              border: "1px solid rgba(148,163,184,0.2)",
              borderRadius: "12px",
              fontSize: "12px"
            }}
            labelStyle={{ color: "#e2e8f0" }}
            formatter={(value: number) => [`₹${value.toLocaleString("en-IN")}`, "Avg"]}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#38bdf8"
            strokeWidth={2}
            fill="url(#priceFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
