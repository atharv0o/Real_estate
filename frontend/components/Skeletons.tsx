export function MapSkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-white/10 bg-slate-800/60">
      <div className="aspect-[16/9] w-full rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900" />
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="animate-pulse overflow-hidden rounded-2xl border border-white/10 bg-slate-900/50">
      <div className="aspect-[16/10] bg-slate-800" />
      <div className="space-y-3 p-5">
        <div className="h-5 w-2/3 rounded bg-slate-700" />
        <div className="h-8 w-1/2 rounded bg-slate-700" />
        <div className="h-4 w-1/3 rounded bg-slate-800" />
      </div>
    </div>
  );
}

export function SearchPageFallback() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <div className="mb-8 h-8 w-48 animate-pulse rounded bg-slate-800" />
      <MapSkeleton />
      <div className="mt-6 h-12 w-64 animate-pulse rounded-xl bg-slate-800" />
    </div>
  );
}
