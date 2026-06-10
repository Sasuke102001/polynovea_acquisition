"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { searchVenues, type VenueCard } from "@/lib/api";
import ParticleCanvas from "@/components/ParticleCanvas";
import ScoreRing from "@/components/ScoreRing";

const CITY_FILTERS = [
  { label: "All",         value: "" },
  { label: "Mumbai",      value: "Mumbai" },
  { label: "Navi Mumbai", value: "Navi Mumbai" },
  { label: "Thane",       value: "Thane" },
];

const TYPE_OPTIONS = [
  { label: "All Types",       value: "" },
  { label: "Restaurant",      value: "restaurant" },
  { label: "Café",            value: "cafe" },
  { label: "Bar",             value: "bar" },
  { label: "Night Club",      value: "night_club" },
  { label: "Pub",             value: "pub" },
  { label: "Bakery",          value: "bakery" },
  { label: "Coffee Shop",     value: "coffee_shop" },
  { label: "Fine Dining",     value: "fine_dining_restaurant" },
  { label: "Fast Food",       value: "fast_food_restaurant" },
  { label: "Dessert Shop",    value: "dessert_shop" },
  { label: "Hookah Bar",      value: "hookah_bar" },
  { label: "Wine Bar",        value: "wine_bar" },
  { label: "Cocktail Bar",    value: "cocktail_bar" },
];

// ─── Venue card ───────────────────────────────────────────────────────────────

function VenueCardItem({ venue }: { venue: VenueCard }) {
  return (
    <Link href={`/venues/${venue.id}`}>
      <article
        className="rounded-xl p-5 flex flex-row items-start justify-between cursor-pointer gap-4 group transition-all duration-200"
        style={{
          background: "rgba(24,24,27,0.6)",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(39,39,42,0.7)",
          boxShadow: "0 12px 32px -8px rgba(0,0,0,0.6)",
          transformStyle: "preserve-3d",
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.transform = "translateY(-3px)";
          (e.currentTarget as HTMLElement).style.borderColor = "rgba(230,211,163,0.3)";
          (e.currentTarget as HTMLElement).style.boxShadow = "0 20px 40px -8px rgba(0,0,0,0.7), 0 0 0 1px rgba(230,211,163,0.1)";
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
          (e.currentTarget as HTMLElement).style.borderColor = "rgba(39,39,42,0.7)";
          (e.currentTarget as HTMLElement).style.boxShadow = "0 12px 32px -8px rgba(0,0,0,0.6)";
        }}
      >
        <div className="flex flex-col gap-2.5 flex-1 min-w-0">
          <div>
            <h3 className="text-sm font-bold tracking-tight truncate" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>
              {venue.name}
            </h3>
            <p className="text-xs mt-0.5" style={{ color: "#71717A" }}>
              {venue.area}, {venue.city}
            </p>
          </div>

          {venue.types.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {venue.types.slice(0, 3).map((t) => (
                <span
                  key={t}
                  className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
                  style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(230,211,163,0.08)", border: "1px solid rgba(230,211,163,0.15)", color: "#A1A1AA" }}
                >
                  {t}
                </span>
              ))}
            </div>
          )}

          {venue.top_segments.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {venue.top_segments.map((s) => (
                <span
                  key={s}
                  className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
                  style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.15)", color: "#10B981" }}
                >
                  {s}
                </span>
              ))}
            </div>
          )}

          {venue.top_archetypes.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {venue.top_archetypes.slice(0, 2).map((a) => (
                <span
                  key={a.name}
                  className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
                  title={a.demographic_label}
                  style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(124,58,237,0.1)", border: "1px solid rgba(124,58,237,0.2)", color: "#c4b5fd" }}
                >
                  {a.name}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex-shrink-0 pt-1 flex flex-col items-center gap-2">
          <ScoreRing score={venue.health_score} size={72} />
          {venue.energy_band && (
            <span
              className="px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-widest rounded"
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                background: venue.energy_band === "HIGH"
                  ? "rgba(16,185,129,0.12)"
                  : venue.energy_band === "MEDIUM"
                  ? "rgba(245,158,11,0.12)"
                  : "rgba(113,113,122,0.12)",
                border: `1px solid ${venue.energy_band === "HIGH" ? "rgba(16,185,129,0.3)" : venue.energy_band === "MEDIUM" ? "rgba(245,158,11,0.3)" : "rgba(113,113,122,0.3)"}`,
                color: venue.energy_band === "HIGH" ? "#10B981" : venue.energy_band === "MEDIUM" ? "#F59E0B" : "#71717A",
              }}
            >
              {venue.energy_band}
            </span>
          )}
        </div>
      </article>
    </Link>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function VenueSearchPage() {
  const [query, setQuery]             = useState("");
  const [city, setCity]               = useState("");
  const [venueType, setVenueType]     = useState("");
  const [venues, setVenues]           = useState<VenueCard[]>([]);
  const [total, setTotal]             = useState(0);
  const [loading, setLoading]         = useState(false);
  const [offline, setOffline]         = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const doSearch = useCallback(async (q: string, c: string, vt: string) => {
    setLoading(true);
    setOffline(false);
    try {
      const data = await searchVenues(q, c || undefined, vt || undefined);
      setVenues(data.venues);
      setTotal(data.total);
      setHasSearched(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      if (msg === "Failed to fetch" || msg.includes("fetch")) setOffline(true);
      setVenues([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { doSearch("", "", ""); }, [doSearch]);

  useEffect(() => {
    const t = setTimeout(() => doSearch(query, city, venueType), 280);
    return () => clearTimeout(t);
  }, [query, city, venueType, doSearch]);

  return (
    <div className="flex flex-col min-h-screen" style={{ background: "#0A0A0A", color: "#F5F5F5", position: "relative" }}>
      <ParticleCanvas />

      {/* ── Top bar ── */}
      <header
        className="w-full top-0 sticky flex items-center justify-between px-6 h-14 z-50"
        style={{
          background: "rgba(10,10,10,0.9)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(39,39,42,0.6)",
          boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-6 h-6 rounded flex items-center justify-center"
            style={{ background: "rgba(230,211,163,0.1)", border: "1px solid rgba(230,211,163,0.2)" }}
          >
            <span className="material-symbols-outlined text-[13px]" style={{ color: "#E6D3A3" }}>analytics</span>
          </div>
          <span
            className="text-xs font-bold tracking-widest uppercase hidden sm:block"
            style={{ fontFamily: "'JetBrains Mono', monospace", color: "#E6D3A3" }}
          >
            VENUE_INTELLIGENCE_v4.0
          </span>
        </div>
        <div className="flex items-center gap-2">
          {offline && (
            <span className="flex items-center gap-1.5 text-xs font-mono" style={{ color: "#F59E0B" }}>
              <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B] animate-pulse inline-block" />
              API offline
            </span>
          )}
          {!offline && hasSearched && (
            <span className="flex items-center gap-1.5 text-xs font-mono" style={{ color: "#10B981" }}>
              <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] inline-block" />
              API live
            </span>
          )}
        </div>
      </header>

      {/* ── Main ── */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-5 md:px-8 py-12 flex flex-col gap-8" style={{ position: "relative", zIndex: 1 }}>

        {/* Hero */}
        <section className="flex flex-col gap-3 items-center text-center max-w-2xl mx-auto">
          <div
            className="text-[10px] font-bold tracking-widest uppercase mb-1"
            style={{ fontFamily: "'JetBrains Mono', monospace", color: "#9A8F6A" }}
          >
            POLYNOVEA · BEHAVIORAL INTELLIGENCE
          </div>
          <h2
            className="text-4xl md:text-5xl font-bold tracking-tight gold-glow"
            style={{ fontFamily: "'Clash Display', 'Inter', sans-serif" }}
          >
            Find Your Venue
          </h2>
          <p className="text-sm" style={{ color: "#71717A" }}>
            Search by name, area, or neighbourhood across Mumbai.
          </p>
        </section>

        {/* Search bar on 3D card */}
        <section className="w-full max-w-3xl mx-auto">
          <div
            className="rounded-2xl p-5"
            style={{
              background: "rgba(24,24,27,0.7)",
              backdropFilter: "blur(16px)",
              border: "1px solid rgba(39,39,42,0.8)",
              boxShadow: "0 24px 48px -12px rgba(0,0,0,0.7)",
            }}
          >
            <div className="relative w-full">
              <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                <span className="material-symbols-outlined text-[18px]" style={{ color: "#71717A" }}>search</span>
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder='Try "Bistro", "Bandra", "Cafe"...'
                className="w-full rounded-lg pl-10 pr-4 py-3 text-sm focus:outline-none transition-all"
                style={{
                  background: "rgba(39,39,42,0.5)",
                  border: "1px solid rgba(39,39,42,0.8)",
                  color: "#F5F5F5",
                  fontFamily: "'Inter', sans-serif",
                }}
                onFocus={(e) => (e.target.style.borderColor = "rgba(230,211,163,0.4)")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(39,39,42,0.8)")}
              />
              {query && (
                <button
                  onClick={() => setQuery("")}
                  className="absolute inset-y-0 right-0 flex items-center pr-4 transition-colors"
                  style={{ color: "#71717A" }}
                >
                  <span className="material-symbols-outlined text-[16px]">close</span>
                </button>
              )}
            </div>

            <div className="relative mt-3">
              <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                <span className="material-symbols-outlined text-[16px]" style={{ color: "#71717A" }}>category</span>
              </div>
              <select
                value={venueType}
                onChange={(e) => setVenueType(e.target.value)}
                className="w-full rounded-lg pl-10 pr-8 py-3 text-sm appearance-none focus:outline-none transition-all cursor-pointer"
                style={{
                  background: "rgba(39,39,42,0.5)",
                  border: `1px solid ${venueType ? "rgba(230,211,163,0.4)" : "rgba(39,39,42,0.8)"}`,
                  color: venueType ? "#F5F5F5" : "#71717A",
                  fontFamily: "'Inter', sans-serif",
                }}
                onFocus={(e) => (e.target.style.borderColor = "rgba(230,211,163,0.4)")}
                onBlur={(e) => (e.target.style.borderColor = venueType ? "rgba(230,211,163,0.4)" : "rgba(39,39,42,0.8)")}
              >
                {TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value} style={{ background: "#18181B", color: "#F5F5F5" }}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                <span className="material-symbols-outlined text-[14px]" style={{ color: "#71717A" }}>expand_more</span>
              </div>
            </div>
          </div>
        </section>

        {/* City filter chips */}
        <section className="w-full max-w-3xl mx-auto overflow-x-auto no-scrollbar -mt-3">
          <div className="flex gap-2 items-center flex-nowrap">
            {CITY_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setCity(f.value)}
                className="px-3 py-1 rounded text-[10px] font-bold uppercase tracking-widest whitespace-nowrap transition-all duration-200"
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  background: city === f.value ? "rgba(230,211,163,0.1)" : "transparent",
                  border: city === f.value ? "1px solid rgba(230,211,163,0.3)" : "1px solid rgba(39,39,42,0.6)",
                  color: city === f.value ? "#E6D3A3" : "#71717A",
                }}
              >
                {f.label}
              </button>
            ))}
          </div>
        </section>

        {/* Results */}
        <section className="w-full max-w-4xl mx-auto flex flex-col gap-4">

          {/* Offline banner */}
          {offline && (
            <div className="rounded-xl p-4 flex flex-col gap-2" style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)" }}>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px]" style={{ color: "#F59E0B" }}>wifi_off</span>
                <span className="text-xs font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#F59E0B" }}>
                  Backend not running
                </span>
              </div>
              <p className="text-xs" style={{ color: "#71717A" }}>
                Cannot reach the backend. Check that the EC2 instance is running and port 8000 is open.
              </p>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-16">
              <span className="material-symbols-outlined animate-spin text-[28px]" style={{ color: "#E6D3A3" }}>progress_activity</span>
            </div>
          )}

          {/* No results */}
          {!loading && hasSearched && venues.length === 0 && !offline && (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <span className="material-symbols-outlined text-[40px] opacity-20" style={{ color: "#A1A1AA" }}>search_off</span>
              <p className="text-sm" style={{ color: "#71717A" }}>
                No venues found{query ? <> for <span style={{ color: "#F5F5F5" }}>&ldquo;{query}&rdquo;</span></> : ""}. Try a different name or area.
              </p>
            </div>
          )}

          {/* Results list */}
          {!loading && venues.length > 0 && (
            <>
              <div className="flex items-center justify-between">
                <p className="text-xs" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
                  Showing{" "}
                  <span style={{ color: "#F5F5F5" }}>{venues.length}</span>{" "}
                  of{" "}
                  <span style={{ color: "#E6D3A3" }}>{total}</span>{" "}
                  venues
                  {query && <> for <span style={{ color: "#E6D3A3" }}>&ldquo;{query}&rdquo;</span></>}
                  {venueType && <> · <span style={{ color: "#E6D3A3" }}>{TYPE_OPTIONS.find(o => o.value === venueType)?.label}</span></>}
                </p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {venues.map((venue) => (
                  <VenueCardItem key={venue.id} venue={venue} />
                ))}
              </div>

              {total > venues.length && (
                <p className="text-center text-xs pt-2" style={{ color: "#3F3F46" }}>
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
