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

const STORAGE_KEY  = "polynovea_admin_key";
const HISTORY_KEY  = "polynovea_demo_history";

// ─── Component ────────────────────────────────────────────────────────────────

export default function AdminDemoPanel({
  venueId,
  venueName,
  venueArea,
}: {
  venueId:   number;
  venueName: string;
  venueArea: string;
}) {
  const [open, setOpen]           = useState(false);
  const [adminKey, setAdminKey]   = useState("");
  const [authed, setAuthed]       = useState(false);
  const [keyInput, setKeyInput]   = useState("");
  const [keyError, setKeyError]   = useState(false);

  // Form
  const [useCurrentVenue, setUseCurrentVenue] = useState(true);
  const [venueQuery, setVenueQuery]           = useState("");
  const [venueResults, setVenueResults]       = useState<VenueResult[]>([]);
  const [selectedVenue, setSelectedVenue]     = useState<VenueResult | null>(null);
  const [searching, setSearching]             = useState(false);
  const [prospectName, setProspectName]       = useState("");
  const [hours, setHours]                     = useState(72);
  const [generating, setGenerating]           = useState(false);
  const [error, setError]                     = useState<string | null>(null);

  // Result
  const [result, setResult]   = useState<GeneratedToken | null>(null);
  const [copied, setCopied]   = useState(false);
  const [history, setHistory] = useState<GeneratedToken[]>([]);

  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Load persisted auth + history ──────────────────────────────────────────
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) { setAdminKey(stored); setAuthed(true); }
    const hist = localStorage.getItem(HISTORY_KEY);
    if (hist) { try { setHistory(JSON.parse(hist)); } catch { /* ignore */ } }
  }, []);

  // ── Close on Escape ────────────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // ── Auth ───────────────────────────────────────────────────────────────────
  const handleAuth = () => {
    if (!keyInput.trim()) return;
    localStorage.setItem(STORAGE_KEY, keyInput.trim());
    setAdminKey(keyInput.trim());
    setAuthed(true);
    setKeyError(false);
  };

  // ── Venue search ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (useCurrentVenue || !venueQuery.trim() || venueQuery.length < 2) {
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
      } catch { setVenueResults([]); }
      finally  { setSearching(false); }
    }, 300);
  }, [venueQuery, useCurrentVenue]);

  const selectVenue = (v: VenueResult) => {
    setSelectedVenue(v);
    setVenueQuery(v.name);
    setVenueResults([]);
  };

  // ── Active venue for the form ──────────────────────────────────────────────
  const activeVenueId   = useCurrentVenue ? venueId   : selectedVenue?.id;
  const activeVenueName = useCurrentVenue ? venueName : selectedVenue?.name ?? "";

  // ── Generate ───────────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!activeVenueId || !prospectName.trim()) return;
    setGenerating(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/demo/generate", {
        method:  "POST",
        headers: { "Content-Type": "application/json", "X-Admin-Key": adminKey },
        body: JSON.stringify({
          venue_id:      activeVenueId,
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
        venueId:      activeVenueId,
        venueName:    activeVenueName,
        prospectName: prospectName.trim(),
        url:          data.demo_url,
        generatedAt:  new Date().toISOString(),
        expiresHours: hours,
      };

      setResult(token);
      const updated = [token, ...history].slice(0, 20);
      setHistory(updated);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
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

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Trigger button — sits next to Deep Analysis in the header */}
      <button
        onClick={() => setOpen(true)}
        title="Admin — Generate demo link"
        className="text-label-md font-label-md text-on-surface-variant hover:text-primary hover:bg-surface-container-highest transition-colors px-sm py-xs border border-outline-variant rounded flex items-center gap-xs"
      >
        <span className="material-symbols-outlined text-[16px]">admin_panel_settings</span>
      </button>

      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Slide-over panel */}
      <div className={`fixed top-0 right-0 h-full w-full max-w-[420px] bg-surface border-l border-outline-variant z-50 flex flex-col shadow-2xl transition-transform duration-300 ${open ? "translate-x-0" : "translate-x-full"}`}>

        {/* Header */}
        <div className="flex items-center justify-between px-lg py-md border-b border-outline-variant bg-surface-dim shrink-0">
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined text-primary text-[20px]">token</span>
            <div>
              <p className="text-[10px] font-label-sm uppercase tracking-widest text-on-surface-variant/60">Admin</p>
              <h2 className="text-[15px] font-bold text-on-surface">Demo Link Generator</h2>
            </div>
          </div>
          <button onClick={() => setOpen(false)} className="text-on-surface-variant hover:text-on-surface transition-colors">
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-lg py-lg flex flex-col gap-lg">

          {/* ── Auth gate ── */}
          {!authed ? (
            <div className="flex flex-col gap-md">
              <p className="text-[13px] text-on-surface-variant">Enter admin key to continue.</p>
              {keyError && (
                <p className="text-[12px] text-error bg-error/10 border border-error/30 rounded-lg px-md py-sm">
                  Wrong key — try again.
                </p>
              )}
              <input
                type="password"
                placeholder="Admin key"
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAuth()}
                className="bg-surface-dim border border-outline-variant rounded-lg px-md py-sm text-[14px] text-on-surface placeholder-on-surface-variant/40 focus:outline-none focus:border-primary"
              />
              <button
                onClick={handleAuth}
                disabled={!keyInput.trim()}
                className="bg-primary text-surface rounded-lg py-sm text-[14px] font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                Unlock
              </button>
            </div>
          ) : (
            <>
              {/* ── Venue selector ── */}
              <div className="flex flex-col gap-xs">
                <label className="text-[11px] font-label-sm uppercase tracking-wide text-on-surface-variant">Venue</label>

                {/* Toggle */}
                <div className="flex gap-xs">
                  <button
                    onClick={() => { setUseCurrentVenue(true); setSelectedVenue(null); setVenueQuery(""); }}
                    className={`text-[12px] px-sm py-xs rounded border transition-colors ${useCurrentVenue ? "bg-primary text-surface border-primary" : "bg-surface text-on-surface-variant border-outline-variant hover:border-primary"}`}
                  >
                    Current venue
                  </button>
                  <button
                    onClick={() => setUseCurrentVenue(false)}
                    className={`text-[12px] px-sm py-xs rounded border transition-colors ${!useCurrentVenue ? "bg-primary text-surface border-primary" : "bg-surface text-on-surface-variant border-outline-variant hover:border-primary"}`}
                  >
                    Search other
                  </button>
                </div>

                {useCurrentVenue ? (
                  <p className="text-[13px] text-primary flex items-center gap-xs">
                    <span className="material-symbols-outlined text-[14px]">check_circle</span>
                    {venueName} — {venueArea}
                  </p>
                ) : (
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Search venue…"
                      value={venueQuery}
                      onChange={(e) => { setVenueQuery(e.target.value); setSelectedVenue(null); }}
                      className="w-full bg-surface-dim border border-outline-variant rounded-lg px-md py-sm text-[14px] text-on-surface placeholder-on-surface-variant/40 focus:outline-none focus:border-primary"
                    />
                    {searching && <span className="absolute right-md top-1/2 -translate-y-1/2 text-[11px] text-on-surface-variant/40">searching…</span>}
                    {venueResults.length > 0 && (
                      <div className="absolute top-full left-0 right-0 mt-xs bg-surface border border-outline-variant rounded-xl shadow-lg z-10 overflow-hidden">
                        {venueResults.map((v) => (
                          <button key={v.id} onClick={() => selectVenue(v)}
                            className="w-full text-left px-md py-sm hover:bg-surface-dim transition-colors border-b border-outline-variant last:border-0">
                            <p className="text-[13px] font-medium text-on-surface">{v.name}</p>
                            <p className="text-[11px] text-on-surface-variant">{v.area}, {v.city}</p>
                          </button>
                        ))}
                      </div>
                    )}
                    {selectedVenue && (
                      <p className="text-[12px] text-primary flex items-center gap-xs mt-xs">
                        <span className="material-symbols-outlined text-[13px]">check_circle</span>
                        {selectedVenue.name} — {selectedVenue.area}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* ── Prospect name ── */}
              <div className="flex flex-col gap-xs">
                <label className="text-[11px] font-label-sm uppercase tracking-wide text-on-surface-variant">Prospect name</label>
                <input
                  type="text"
                  placeholder="e.g. Svanika, The Kapoor Group"
                  value={prospectName}
                  onChange={(e) => setProspectName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                  className="bg-surface-dim border border-outline-variant rounded-lg px-md py-sm text-[14px] text-on-surface placeholder-on-surface-variant/40 focus:outline-none focus:border-primary"
                />
              </div>

              {/* ── Expiry ── */}
              <div className="flex flex-col gap-xs">
                <label className="text-[11px] font-label-sm uppercase tracking-wide text-on-surface-variant">Link expiry</label>
                <div className="flex gap-xs flex-wrap">
                  {[24, 48, 72, 168].map((h) => (
                    <button key={h} onClick={() => setHours(h)}
                      className={`px-sm py-xs rounded text-[12px] border transition-colors ${hours === h ? "bg-primary text-surface border-primary" : "bg-surface text-on-surface-variant border-outline-variant hover:border-primary"}`}>
                      {h === 24 ? "24h" : h === 48 ? "48h" : h === 72 ? "72h" : "1 week"}
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <p className="text-[12px] text-error bg-error/10 border border-error/30 rounded-lg px-md py-sm">{error}</p>
              )}

              <button
                onClick={handleGenerate}
                disabled={!activeVenueId || !prospectName.trim() || generating}
                className="bg-primary text-surface rounded-lg py-sm text-[14px] font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-xs"
              >
                {generating ? (
                  <><div className="w-3.5 h-3.5 border-2 border-surface/40 border-t-surface rounded-full animate-spin" />Generating…</>
                ) : (
                  <><span className="material-symbols-outlined text-[16px]">link</span>Generate demo link</>
                )}
              </button>

              {/* ── Result ── */}
              {result && (
                <div className="bg-surface-dim border border-primary/30 rounded-xl p-md flex flex-col gap-sm">
                  <p className="text-[13px] font-bold text-primary flex items-center gap-xs">
                    <span className="material-symbols-outlined text-[16px]">check_circle</span>
                    {result.prospectName} · {result.expiresHours}h
                  </p>
                  <div className="flex items-center gap-sm bg-surface border border-outline-variant rounded-lg px-sm py-xs">
                    <p className="flex-1 text-[11px] text-on-surface font-data-mono break-all">{result.url}</p>
                    <button onClick={() => copyUrl(result.url)}
                      className="shrink-0 bg-primary text-surface rounded px-sm py-xs text-[11px] font-medium hover:opacity-90 flex items-center gap-xs">
                      <span className="material-symbols-outlined text-[13px]">{copied ? "check" : "content_copy"}</span>
                      {copied ? "Copied!" : "Copy"}
                    </button>
                  </div>
                </div>
              )}

              {/* ── History ── */}
              {history.length > 0 && (
                <div className="flex flex-col gap-sm">
                  <div className="flex items-center justify-between">
                    <p className="text-[11px] font-label-sm uppercase tracking-wide text-on-surface-variant">Recent links</p>
                    <button onClick={() => { setHistory([]); localStorage.removeItem(HISTORY_KEY); }}
                      className="text-[11px] text-on-surface-variant/40 hover:text-error transition-colors">Clear</button>
                  </div>
                  {history.slice(0, 8).map((h, idx) => (
                    <div key={idx} className="bg-surface-dim border border-outline-variant rounded-lg px-md py-sm flex items-center gap-md">
                      <div className="flex-1 min-w-0">
                        <p className="text-[13px] font-medium text-on-surface truncate">{h.prospectName}</p>
                        <p className="text-[11px] text-on-surface-variant truncate">{h.venueName} · {h.expiresHours}h</p>
                      </div>
                      <button onClick={() => copyUrl(h.url)} className="shrink-0 text-on-surface-variant hover:text-primary transition-colors" title="Copy">
                        <span className="material-symbols-outlined text-[16px]">content_copy</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Sign out */}
              <button
                onClick={() => { localStorage.removeItem(STORAGE_KEY); setAuthed(false); setAdminKey(""); setKeyInput(""); }}
                className="text-[11px] text-on-surface-variant/40 hover:text-error transition-colors flex items-center gap-xs mt-auto pt-md border-t border-outline-variant"
              >
                <span className="material-symbols-outlined text-[13px]">logout</span>
                Sign out of admin
              </button>
            </>
          )}
        </div>
      </div>
    </>
  );
}
