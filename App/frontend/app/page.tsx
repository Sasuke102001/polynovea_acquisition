"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { searchVenues, type VenueCard } from "@/lib/api";
import ScoreRing from "@/components/ScoreRing";

const CITY_FILTERS = [
  { label: "All",        value: "" },
  { label: "Mumbai",     value: "Mumbai" },
  { label: "Navi Mumbai",value: "Navi Mumbai" },
  { label: "Thane",      value: "Thane" },
];

// ─── Backend offline banner ───────────────────────────────────────────────────

function OfflineBanner() {
  return (
    <div className="bg-[#1a0f00] border border-[#f59e0b]/30 rounded-lg p-md flex flex-col gap-sm">
      <div className="flex items-center gap-sm">
        <span className="material-symbols-outlined text-signal-warning text-[18px]">
          wifi_off
        </span>
        <span className="text-signal-warning font-label-sm text-label-sm font-bold uppercase tracking-wider">
          Backend not running
        </span>
      </div>
      <p className="text-on-surface-variant text-body-sm font-body-sm">
        The API server at{" "}
        <code className="text-primary-container font-data-mono text-[13px] bg-surface-container px-xs py-[1px] rounded">
          http://localhost:8000
        </code>{" "}
        is unreachable. Start it with:
      </p>
      <div className="bg-[#0d0d11] border border-[#27272a] rounded p-sm font-data-mono text-[13px] text-primary-container select-all">
        cd App/backend &amp;&amp; uvicorn main:app --reload --port 8000
      </div>
    </div>
  );
}

// ─── Venue card ───────────────────────────────────────────────────────────────

function VenueCardItem({ venue }: { venue: VenueCard }) {
  return (
    <Link href={`/venues/${venue.id}`}>
      <article className="venue-card bg-surface rounded-lg p-lg flex flex-row items-start justify-between border cursor-pointer group gap-md">
        <div className="flex flex-col gap-sm flex-1 min-w-0">
          {/* Name + location */}
          <div>
            <h3 className="text-[15px] font-bold text-on-surface tracking-tight truncate">
              {venue.name}
            </h3>
            <p className="text-[12px] text-on-surface-variant font-body-sm mt-[2px]">
              {venue.area}, {venue.city}
            </p>
          </div>

          {/* Venue type chips (champagne gold) */}
          {venue.types.length > 0 && (
            <div className="flex flex-wrap gap-xs">
              {venue.types.slice(0, 3).map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center px-xs py-[2px] rounded font-label-sm text-label-sm uppercase bg-primary-container/10 text-primary-container border border-primary-container/20"
                >
                  {t}
                </span>
              ))}
            </div>
          )}

          {/* Segment chips (teal) */}
          {venue.top_segments.length > 0 && (
            <div className="flex flex-wrap gap-xs">
              {venue.top_segments.map((s) => (
                <span
                  key={s}
                  className="inline-flex items-center px-xs py-[2px] rounded font-label-sm text-label-sm uppercase bg-[#0D9488]/10 text-[#0D9488] border border-[#0D9488]/25"
                >
                  {s}
                </span>
              ))}
            </div>
          )}

          {/* Archetype chips (violet) */}
          {venue.top_archetypes.length > 0 && (
            <div className="flex flex-wrap gap-xs">
              {venue.top_archetypes.slice(0, 2).map((a) => (
                <span
                  key={a.name}
                  className="inline-flex items-center px-xs py-[2px] rounded text-[10px] uppercase bg-[#7C3AED]/10 text-[#7C3AED] border border-[#7C3AED]/20"
                  title={a.demographic_label}
                >
                  {a.name}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Health ring */}
        <div className="flex-shrink-0 pt-xs">
          <ScoreRing score={venue.health_score} size={80} />
        </div>
      </article>
    </Link>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function VenueSearchPage() {
  const [query, setQuery]       = useState("");
  const [city, setCity]         = useState("");
  const [venues, setVenues]     = useState<VenueCard[]>([]);
  const [total, setTotal]       = useState(0);
  const [loading, setLoading]   = useState(false);
  const [offline, setOffline]   = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const doSearch = useCallback(async (q: string, c: string) => {
    setLoading(true);
    setOffline(false);
    try {
      const data = await searchVenues(q, c || undefined);
      setVenues(data.venues);
      setTotal(data.total);
      setHasSearched(true);
    } catch (err: unknown) {
      // Distinguish "backend down" (TypeError: Failed to fetch) from other errors
      const msg = err instanceof Error ? err.message : "";
      if (msg === "Failed to fetch" || msg.includes("fetch")) {
        setOffline(true);
      }
      setVenues([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Show all venues on first load
  useEffect(() => {
    doSearch("", "");
  }, [doSearch]);

  // Debounced re-search as user types
  useEffect(() => {
    const t = setTimeout(() => doSearch(query, city), 280);
    return () => clearTimeout(t);
  }, [query, city, doSearch]);

  return (
    <div className="flex flex-col min-h-screen bg-background text-on-surface">

      {/* ── Top bar ── */}
      <header className="bg-background w-full top-0 sticky border-b border-outline-variant flex items-center justify-between px-md h-16 z-50">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined text-primary">analytics</span>
          <h1 className="font-headline-md text-headline-md font-bold text-primary tracking-tighter hidden sm:block">
            VENUE_INTELLIGENCE_v4.0
          </h1>
        </div>
        <div className="flex items-center gap-xs">
          {offline && (
            <span className="text-signal-warning text-label-sm font-label-sm flex items-center gap-xs">
              <span className="w-2 h-2 rounded-full bg-signal-warning animate-pulse inline-block" />
              API offline
            </span>
          )}
          {!offline && hasSearched && (
            <span className="text-signal-positive text-label-sm font-label-sm flex items-center gap-xs">
              <span className="w-2 h-2 rounded-full bg-signal-positive inline-block" />
              API live
            </span>
          )}
        </div>
      </header>

      {/* ── Main ── */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-md md:px-lg py-xl flex flex-col gap-lg">

        {/* Hero */}
        <section className="flex flex-col gap-sm items-center text-center max-w-2xl mx-auto pt-md">
          <h2 className="font-headline-md text-display-lg text-primary-container font-bold tracking-tight">
            Find Your Venue
          </h2>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Search by name, area, or neighbourhood across Mumbai.
          </p>
        </section>

        {/* Search bar */}
        <section className="w-full max-w-3xl mx-auto">
          <div className="relative w-full">
            <div className="absolute inset-y-0 left-0 flex items-center pl-sm pointer-events-none">
              <span className="material-symbols-outlined text-on-surface-variant text-[20px]">
                search
              </span>
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='Try "Bistro", "Bandra", "Cafe"...'
              className="w-full bg-surface-container border border-outline-variant text-on-surface font-body-md rounded pl-[40px] pr-sm py-md focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition-all placeholder:text-on-surface-variant/50"
            />
            {query && (
              <button
                onClick={() => setQuery("")}
                className="absolute inset-y-0 right-0 flex items-center pr-sm text-on-surface-variant hover:text-on-surface transition-colors"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            )}
          </div>
        </section>

        {/* City filter chips */}
        <section className="w-full max-w-3xl mx-auto overflow-x-auto no-scrollbar -mt-sm">
          <div className="flex gap-sm items-center flex-nowrap">
            {CITY_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setCity(f.value)}
                className={`px-sm py-xs rounded border font-label-sm text-label-sm uppercase whitespace-nowrap transition-colors ${
                  city === f.value
                    ? "border-primary-container bg-primary-container/10 text-primary-container"
                    : "border-outline-variant text-on-surface-variant hover:text-on-surface hover:border-outline"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </section>

        {/* Results */}
        <section className="w-full max-w-4xl mx-auto flex flex-col gap-md">

          {/* Offline banner */}
          {offline && <OfflineBanner />}

          {/* Loading */}
          {loading && (
            <div className="text-center text-on-surface-variant py-xl">
              <span className="material-symbols-outlined text-primary text-[32px] animate-spin inline-block">
                progress_activity
              </span>
            </div>
          )}

          {/* No results */}
          {!loading && hasSearched && venues.length === 0 && !offline && (
            <div className="text-center text-on-surface-variant py-xl">
              <span className="material-symbols-outlined text-[40px] mb-sm block opacity-30">
                search_off
              </span>
              <p className="font-body-md text-body-md">
                No venues found for{" "}
                {query ? (
                  <span className="text-on-surface">&ldquo;{query}&rdquo;</span>
                ) : (
                  "this filter"
                )}
                . Try a different name or area.
              </p>
            </div>
          )}

          {/* Results list */}
          {!loading && venues.length > 0 && (
            <>
              <div className="flex items-center justify-between">
                <p className="text-on-surface-variant text-body-sm font-body-sm">
                  Showing{" "}
                  <span className="text-on-surface font-bold">{venues.length}</span>{" "}
                  of{" "}
                  <span className="text-on-surface font-bold font-data-mono">{total}</span>{" "}
                  venues
                  {query && (
                    <>
                      {" for "}
                      <span className="text-primary-container">&ldquo;{query}&rdquo;</span>
                    </>
                  )}
                </p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-md">
                {venues.map((venue) => (
                  <VenueCardItem key={venue.id} venue={venue} />
                ))}
              </div>

              {total > venues.length && (
                <p className="text-center text-on-surface-variant text-body-sm font-body-sm pt-sm">
                  Refine your search to see more results.
                </p>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}
