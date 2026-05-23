"use client";

import { useEffect, useRef, useState } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface VenueResult {
  id: number;
  name: string;
  area: string;
  city: string;
}

interface GeneratedToken {
  venueId: number;
  venueName: string;
  prospectName: string;
  url: string;
  generatedAt: string;
  expiresHours: number;
}

const STORAGE_KEY = "polynovea_admin_key";
const HISTORY_KEY = "polynovea_demo_history";

// ─── Main page ────────────────────────────────────────────────────────────────

export default function AdminDemoPage() {
  const [adminKey, setAdminKey]           = useState("");
  const [authed, setAuthed]               = useState(false);
  const [keyInput, setKeyInput]           = useState("");
  const [keyError, setKeyError]           = useState(false);

  // Form state
  const [venueQuery, setVenueQuery]       = useState("");
  const [venueResults, setVenueResults]   = useState<VenueResult[]>([]);
  const [selectedVenue, setSelectedVenue] = useState<VenueResult | null>(null);
  const [searching, setSearching]         = useState(false);
  const [prospectName, setProspectName]   = useState("");
  const [hours, setHours]                 = useState(72);
  const [generating, setGenerating]       = useState(false);
  const [error, setError]                 = useState<string | null>(null);

  // Results
  const [result, setResult]               = useState<GeneratedToken | null>(null);
  const [copied, setCopied]               = useState(false);
  const [history, setHistory]             = useState<GeneratedToken[]>([]);

  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Load persisted auth + history ────────────────────────────────────────
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) { setAdminKey(stored); setAuthed(true); }
    const hist = localStorage.getItem(HISTORY_KEY);
    if (hist) { try { setHistory(JSON.parse(hist)); } catch { /* ignore */ } }
  }, []);

  // ── Auth gate ─────────────────────────────────────────────────────────────
  const handleAuth = () => {
    if (!keyInput.trim()) return;
    localStorage.setItem(STORAGE_KEY, keyInput.trim());
    setAdminKey(keyInput.trim());
    setAuthed(true);
    setKeyError(false);
  };

  // ── Venue search (debounced) ──────────────────────────────────────────────
  useEffect(() => {
    if (!venueQuery.trim() || venueQuery.length < 2) {
      setVenueResults([]);
      return;
    }
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res  = await fetch(`/api/venues/search?q=${encodeURIComponent(venueQuery)}&limit=8`);
        const data = await res.json();
        setVenueResults(data.venues ?? []);
      } catch {
        setVenueResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);
  }, [venueQuery]);

  const selectVenue = (v: VenueResult) => {
    setSelectedVenue(v);
    setVenueQuery(v.name);
    setVenueResults([]);
  };

  // ── Generate token ────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!selectedVenue || !prospectName.trim()) return;
    setGenerating(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/demo/generate", {
        method:  "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Key":  adminKey,
        },
        body: JSON.stringify({
          venue_id:      selectedVenue.id,
          prospect_name: prospectName.trim(),
          expires_hours: hours,
        }),
      });

      if (res.status === 403) {
        setKeyError(true);
        setAuthed(false);
        localStorage.removeItem(STORAGE_KEY);
        setGenerating(false);
        return;
      }

      if (!res.ok) {
        const body = await res.json();
        setError(body.detail ?? `Error ${res.status}`);
        setGenerating(false);
        return;
      }

      const data = await res.json();
      const token: GeneratedToken = {
        venueId:      selectedVenue.id,
        venueName:    selectedVenue.name,
        prospectName: prospectName.trim(),
        url:          data.demo_url,
        generatedAt:  new Date().toISOString(),
        expiresHours: hours,
      };

      setResult(token);
      const updated = [token, ...history].slice(0, 20);
      setHistory(updated);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));

      // Reset form
      setSelectedVenue(null);
      setVenueQuery("");
      setProspectName("");
      setHours(72);

    } catch {
      setError("Could not reach the server.");
    } finally {
      setGenerating(false);
    }
  };

  const copyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // ── Auth screen ───────────────────────────────────────────────────────────
  if (!authed) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-lg">
        <div className="w-full max-w-[380px] bg-surface-dim border border-outline-variant rounded-2xl p-xl flex flex-col gap-md">
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined text-primary text-[28px]">admin_panel_settings</span>
            <div>
              <h1 className="text-[18px] font-bold text-on-surface">Admin Access</h1>
              <p className="text-[13px] text-on-surface-variant">Polynovea · Demo Token Generator</p>
            </div>
          </div>

          {keyError && (
            <p className="text-[13px] text-error bg-error/10 border border-error/30 rounded-lg px-md py-sm">
              Wrong admin key — try again.
            </p>
          )}

          <input
            type="password"
            placeholder="Enter admin key"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAuth()}
            className="bg-surface border border-outline-variant rounded-lg px-md py-sm text-[15px] text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary"
          />
          <button
            onClick={handleAuth}
            disabled={!keyInput.trim()}
            className="bg-primary text-surface rounded-lg py-sm text-[15px] font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            Enter
          </button>
        </div>
      </div>
    );
  }

  // ── Main admin UI ─────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-surface">

      {/* Header */}
      <header className="bg-surface-dim border-b border-outline-variant px-lg py-md flex items-center justify-between">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined text-primary text-[24px]">token</span>
          <div>
            <p className="text-[11px] font-label-sm uppercase tracking-widest text-on-surface-variant/70">
              Polynovea · Admin
            </p>
            <h1 className="text-[18px] font-bold text-on-surface">Demo Token Generator</h1>
          </div>
        </div>
        <button
          onClick={() => { localStorage.removeItem(STORAGE_KEY); setAuthed(false); setAdminKey(""); setKeyInput(""); }}
          className="text-[12px] text-on-surface-variant/60 hover:text-error transition-colors flex items-center gap-xs"
        >
          <span className="material-symbols-outlined text-[15px]">logout</span>
          Sign out
        </button>
      </header>

      <div className="max-w-[720px] mx-auto px-lg py-xl flex flex-col gap-xl">

        {/* ── Generator form ── */}
        <div className="bg-surface-dim border border-outline-variant rounded-2xl p-xl flex flex-col gap-lg">
          <h2 className="text-[16px] font-bold text-on-surface">Generate a demo link</h2>

          {/* Venue search */}
          <div className="flex flex-col gap-xs">
            <label className="text-[12px] font-label-sm uppercase tracking-wide text-on-surface-variant">
              Venue
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="Search venue by name or area…"
                value={venueQuery}
                onChange={(e) => { setVenueQuery(e.target.value); setSelectedVenue(null); }}
                className="w-full bg-surface border border-outline-variant rounded-lg px-md py-sm text-[15px] text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary"
              />
              {searching && (
                <span className="absolute right-md top-1/2 -translate-y-1/2 text-[12px] text-on-surface-variant/50">
                  searching…
                </span>
              )}
              {venueResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-xs bg-surface border border-outline-variant rounded-xl shadow-lg z-10 overflow-hidden">
                  {venueResults.map((v) => (
                    <button
                      key={v.id}
                      onClick={() => selectVenue(v)}
                      className="w-full text-left px-md py-sm hover:bg-surface-dim transition-colors border-b border-outline-variant last:border-0"
                    >
                      <p className="text-[14px] font-medium text-on-surface">{v.name}</p>
                      <p className="text-[12px] text-on-surface-variant">{v.area}, {v.city} · ID {v.id}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>
            {selectedVenue && (
              <p className="text-[12px] text-primary flex items-center gap-xs">
                <span className="material-symbols-outlined text-[14px]">check_circle</span>
                {selectedVenue.name} — {selectedVenue.area} · venue_id={selectedVenue.id}
              </p>
            )}
          </div>

          {/* Prospect name */}
          <div className="flex flex-col gap-xs">
            <label className="text-[12px] font-label-sm uppercase tracking-wide text-on-surface-variant">
              Prospect name
            </label>
            <input
              type="text"
              placeholder="e.g. Svanika, The Kapoor Group"
              value={prospectName}
              onChange={(e) => setProspectName(e.target.value)}
              className="bg-surface border border-outline-variant rounded-lg px-md py-sm text-[15px] text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary"
            />
          </div>

          {/* Expiry */}
          <div className="flex flex-col gap-xs">
            <label className="text-[12px] font-label-sm uppercase tracking-wide text-on-surface-variant">
              Link expiry
            </label>
            <div className="flex gap-sm">
              {[24, 48, 72, 168].map((h) => (
                <button
                  key={h}
                  onClick={() => setHours(h)}
                  className={`px-md py-xs rounded-lg text-[13px] border transition-colors ${
                    hours === h
                      ? "bg-primary text-surface border-primary"
                      : "bg-surface text-on-surface-variant border-outline-variant hover:border-primary"
                  }`}
                >
                  {h === 24 ? "24h" : h === 48 ? "48h" : h === 72 ? "72h" : "1 week"}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <p className="text-[13px] text-error bg-error/10 border border-error/30 rounded-lg px-md py-sm">
              {error}
            </p>
          )}

          <button
            onClick={handleGenerate}
            disabled={!selectedVenue || !prospectName.trim() || generating}
            className="bg-primary text-surface rounded-lg py-sm text-[15px] font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-xs"
          >
            {generating ? (
              <>
                <div className="w-4 h-4 border-2 border-surface/40 border-t-surface rounded-full animate-spin" />
                Generating…
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]">link</span>
                Generate demo link
              </>
            )}
          </button>
        </div>

        {/* ── Result ── */}
        {result && (
          <div className="bg-surface border-2 border-primary/40 rounded-2xl p-xl flex flex-col gap-md">
            <div className="flex items-center gap-xs text-primary">
              <span className="material-symbols-outlined text-[20px]">check_circle</span>
              <p className="text-[15px] font-bold">Link generated for {result.prospectName}</p>
            </div>
            <p className="text-[13px] text-on-surface-variant">
              {result.venueName} · expires in {result.expiresHours}h
            </p>
            <div className="bg-surface-dim border border-outline-variant rounded-xl px-md py-sm flex items-center gap-sm">
              <p className="flex-1 text-[13px] text-on-surface font-data-mono break-all">{result.url}</p>
              <button
                onClick={() => copyUrl(result.url)}
                className="shrink-0 bg-primary text-surface rounded-lg px-md py-xs text-[13px] font-medium hover:opacity-90 transition-opacity flex items-center gap-xs"
              >
                <span className="material-symbols-outlined text-[15px]">{copied ? "check" : "content_copy"}</span>
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>
        )}

        {/* ── History ── */}
        {history.length > 0 && (
          <div className="flex flex-col gap-md">
            <div className="flex items-center justify-between">
              <h2 className="text-[15px] font-bold text-on-surface">Recent links</h2>
              <button
                onClick={() => { setHistory([]); localStorage.removeItem(HISTORY_KEY); }}
                className="text-[12px] text-on-surface-variant/50 hover:text-error transition-colors"
              >
                Clear
              </button>
            </div>
            <div className="flex flex-col gap-sm">
              {history.map((h, idx) => (
                <div
                  key={idx}
                  className="bg-surface-dim border border-outline-variant rounded-xl px-md py-sm flex items-center gap-md"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-[14px] font-medium text-on-surface truncate">{h.prospectName}</p>
                    <p className="text-[12px] text-on-surface-variant truncate">{h.venueName} · {h.expiresHours}h</p>
                  </div>
                  <button
                    onClick={() => copyUrl(h.url)}
                    className="shrink-0 text-on-surface-variant hover:text-primary transition-colors"
                    title="Copy link"
                  >
                    <span className="material-symbols-outlined text-[18px]">content_copy</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
