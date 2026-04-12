import { SearchBar } from "@/components/SearchBar";

/**
 * Hero landing: glassmorphism search form → navigates to /search with query params.
 */
export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-30" />
      <div className="pointer-events-none absolute -left-40 top-20 h-96 w-96 rounded-full bg-sky-500/20 blur-[120px]" />
      <div className="pointer-events-none absolute -right-40 bottom-0 h-80 w-80 rounded-full bg-violet-500/15 blur-[100px]" />

      <div className="relative mx-auto max-w-6xl px-4 pb-24 pt-16 md:pt-24">
        <div className="mx-auto max-w-3xl text-center">
          <p className="mb-4 inline-flex items-center rounded-full border border-sky-500/20 bg-sky-500/10 px-3 py-1 text-xs font-medium uppercase tracking-wider text-sky-300">
            Area intelligence · Maps · RAG-ready
          </p>
          <h1 className="font-display text-4xl font-bold tracking-tight text-white md:text-5xl lg:text-6xl">
            Know every locality before you{" "}
            <span className="bg-gradient-to-r from-sky-400 to-cyan-300 bg-clip-text text-transparent">
              commit
            </span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400">
            Search by district, city, area, PIN, and land reference. We pin the
            location on the map and let you pull structured property signals from
            your API.
          </p>
        </div>

        <div className="mx-auto mt-14 max-w-4xl">
          <SearchBar />
        </div>

        <div className="mx-auto mt-16 grid max-w-4xl gap-6 sm:grid-cols-3">
          {[
            {
              title: "Precision search",
              body: "Controlled inputs with validation before you ever hit the map."
            },
            {
              title: "Map-first UX",
              body: "Mock geocoding today — drop in Google Maps when you are ready."
            },
            {
              title: "API-ready",
              body: "Zustand store and Axios client wired to GET /api/property-data."
            }
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-2xl border border-white/5 bg-slate-900/30 p-5 text-left backdrop-blur-sm"
            >
              <h3 className="font-display font-semibold text-white">{item.title}</h3>
              <p className="mt-2 text-sm text-slate-500">{item.body}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
