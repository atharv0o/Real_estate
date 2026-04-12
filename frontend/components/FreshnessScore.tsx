export type FreshnessScoreProps = {
  hours: number;
  className?: string;
};

export function FreshnessScore({ hours, className = "" }: FreshnessScoreProps) {
  const safe = Number.isFinite(hours) && hours >= 0 ? Math.round(hours) : 0;

  return (
    <p
      className={`text-sm text-slate-400 ${className}`}
      title="Time since underlying records were last synced"
    >
      Data Freshness:{" "}
      <span className="font-medium text-slate-200">
        {safe} {safe === 1 ? "hour" : "hours"} ago
      </span>
    </p>
  );
}
