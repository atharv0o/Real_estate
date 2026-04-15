"use client";

export type MapProps = {
  lat: number;
  lng: number;
  label?: string;
  className?: string;
};

function isValidCoordinate(value: number): boolean {
  return typeof value === "number" && Number.isFinite(value);
}

export function Map({ lat, lng, label, className = "" }: MapProps) {
  const hasCoordinates = isValidCoordinate(lat) && isValidCoordinate(lng);

  if (!hasCoordinates) {
    return (
      <div
        className={`flex items-center justify-center rounded-2xl border border-white/10 bg-slate-900/50 px-6 py-10 text-sm text-slate-400 ${className}`}
      >
        Location not available
      </div>
    );
  }

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-white/10 bg-slate-900/50 shadow-inner ${className}`}
      role="img"
      aria-label={label ? `Map showing ${label} at ${lat.toFixed(4)}, ${lng.toFixed(4)}` : `Map at ${lat.toFixed(4)}, ${lng.toFixed(4)}`}
    >
      <div
        className="absolute inset-0 opacity-90"
        style={{
          background:
            "radial-gradient(ellipse at 30% 20%, rgba(56,189,248,0.25), transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(14,165,233,0.15), transparent 45%), linear-gradient(180deg, #0f172a 0%, #1e293b 100%)"
        }}
      />
      <div className="absolute inset-0 bg-grid opacity-40" />

      <div className="absolute left-3 top-3 flex gap-2 rounded-lg bg-black/40 px-2 py-1 text-[10px] text-slate-300 backdrop-blur">
        <span className="rounded bg-white/10 px-1.5 py-0.5">Map</span>
        <span className="opacity-60">Satellite</span>
      </div>

      <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-full flex-col items-center">
        <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-sky-500 shadow-lg shadow-sky-500/40 ring-4 ring-sky-500/30">
          <span className="h-3 w-3 rounded-full bg-white" />
        </div>
        <div className="h-4 w-px bg-gradient-to-b from-sky-400/80 to-transparent" />
      </div>

      <div className="absolute bottom-0 left-0 right-0 border-t border-white/10 bg-slate-950/80 p-4 backdrop-blur-md">
        <p className="truncate text-sm font-medium text-white">{label ?? "Selected location"}</p>
        <p className="font-mono text-xs text-sky-300/90">
          {lat.toFixed(6)}, {lng.toFixed(6)}
        </p>
        <p className="mt-1 text-[10px] text-slate-500">
          Google Maps integration placeholder with explicit lat/lng rendering.
        </p>
      </div>
    </div>
  );
}
