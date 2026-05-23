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

// ─── Shared style tokens ──────────────────────────────────────────────────────

const S = {
  panel:      { background: "#0e0e11", borderLeft: "1px solid rgba(39,39,42,0.9)" },
  header:     { background: "rgba(18,18,24,0.97)", borderBottom: "1px solid rgba(39,39,42,0.7)" },
  input:      { background: "rgba(24,24,27,0.8)", border: "1px solid rgba(39,39,42,0.8)", color: "#F5F5F5", fontFamily: "'Inter', sans-serif" },
  inputFocus: { borderColor: "rgba(230,211,163,0.4)" },
  card:       { background: "rgba(24,24,27,0.7)", border: "1px solid rgba(39,39,42,0.7)" },
  label:      { fontFamily: "'JetBrains Mono', monospace", color: "#71717A" } as React.CSSProperties,
  mono:       { fontFamily: "'JetBrains Mono', monospace" } as React.CSSProperties,
  btnPrimary: { background: "rgba(230,211,163,0.1)", border: "1px solid rgba(230,211,163,0.3)", color: "#E6D3A3", fontFamily: "'JetBrains Mono', monospace" } as React.CSSProperties,
  btnMuted:   { background: "transparent", border: "1px solid rgba(39,39,42,0.7)", color: "#71717A", fontFamily: "'JetBrains Mono', monospace" } as React.CSSProperties,
};

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

  const [useCurrentVenue, setUseCurrentVenue] = useState(true);
  const [venueQuery, setVenueQuery]           = useState("");
  const [venueResults, setVenueResults]       = useState<VenueResult[]>([]);
  const [selectedVenue, setSelectedVenue]     = useState<VenueResult | null>(null);
  const [searching, setSearching]             = useState(false);
  const [prospectName, setProspectName]       = useState("");
  const [hours, setHours]                     = useState(72);
  const [generating, setGenerating]           = useState(false);
  const [error, setError]                     = useState<string | null>(null);

  const [result, setResult]   = useState<GeneratedToken | null>(null);
  const [copied, setCopied]   = useState(false);
  const [history, setHistory] = useState<GeneratedToken[]>([]);

  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) { setAdminKey(stored); setAuthed(true); }
    const hist = localStorage.getItem(HISTORY_KEY);
    if (hist) { try { setHistory(JSON.parse(hist)); } catch { /* ignore */ } }
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const handleAuth = () => {
    if (!keyInput.trim()) return;
    localStorage.setItem(STORAGE_KEY, keyInput.trim());
    setAdminKey(keyInput.trim());
    setAuthed(true);
    setKeyError(false);
  };

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

  const activeVenueId   = useCurrentVenue ? venueId   : selectedVenue?.id;
  const activeVenueName = useCurrentVenue ? venueName : selectedVenue?.name ?? "";

  const handleGenerate = async () => {
    if (!activeVenueId || !prospectName.trim()) return;
    setGenerating(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/demo/generate", {
        method:  "POST",
        headers: { "Content-Type": "application/json", "X-Admin-Key": adminKey },
        body: JSON.stringify({ venue_id: activeVenueId, prospect_name: prospectName.trim(), expires_hours: hours }),
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
        venueId: activeVenueId, venueName: activeVenueName,
        prospectName: prospectName.trim(), url: data.demo_url,
        generatedAt: new Date().toISOString(), expiresHours: hours,
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

  return (
    <>
      {/* Trigger button */}
      <button
        onClick={() => setOpen(true)}
        title="Admin — Generate demo link"
        className="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-bold uppercase tracking-wider transition-all"
        style={{ fontFamily: "'JetBrains Mono', monospace", border: "1px solid rgba(39,39,42,0.7)", color: "#71717A", background: "transparent" }}
        onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(230,211,163,0.3)"; (e.currentTarget as HTMLElement).style.color = "#E6D3A3"; }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(39,39,42,0.7)"; (e.currentTarget as HTMLElement).style.color = "#71717A"; }}
      >
        <span className="material-symbols-outlined text-[15px]">admin_panel_settings</span>
      </button>

      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40"
          style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(2px)" }}
          onClick={() => setOpen(false)}
        />
      )}

      {/* Slide-over panel */}
      <div
        className={`fixed top-0 right-0 h-screen w-full max-w-[420px] z-50 flex flex-col shadow-2xl transition-transform duration-300 ${open ? "translate-x-0" : "translate-x-full"}`}
        style={S.panel}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 shrink-0" style={S.header}>
          <div className="flex items-center gap-2.5">
            <div
              className="w-7 h-7 rounded flex items-center justify-center shrink-0"
              style={{ background: "rgba(230,211,163,0.08)", border: "1px solid rgba(230,211,163,0.15)" }}
            >
              <span className="material-symbols-outlined text-[14px]" style={{ color: "#E6D3A3" }}>token</span>
            </div>
            <div>
              <p className="text-[9px] font-bold uppercase tracking-widest" style={S.label}>Admin</p>
              <h2 className="text-[14px] font-bold" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>Demo Link Generator</h2>
            </div>
          </div>
          <button
            onClick={() => setOpen(false)}
            className="transition-colors"
            style={{ color: "#71717A" }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#F5F5F5")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "#71717A")}
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto custom-scrollbar px-5 py-5 flex flex-col gap-5" style={{ background: "#0e0e11", minHeight: 0 }}>

          {/* ── Auth gate ── */}
          {!authed ? (
            <div className="flex flex-col gap-4">
              <p className="text-[13px]" style={{ color: "#A1A1AA" }}>Enter admin key to continue.</p>

              {keyError && (
                <p className="text-[12px] rounded-lg px-3 py-2" style={{ color: "#FB7185", background: "rgba(251,113,133,0.08)", border: "1px solid rgba(251,113,133,0.2)" }}>
                  Wrong key — try again.
                </p>
              )}

              <input
                type="password"
                placeholder="Admin key"
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAuth()}
                className="w-full rounded-lg px-3 py-2.5 text-[14px] focus:outline-none transition-all"
                style={S.input}
                onFocus={(e) => (e.target.style.borderColor = "rgba(230,211,163,0.4)")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(39,39,42,0.8)")}
              />
              <button
                onClick={handleAuth}
                disabled={!keyInput.trim()}
                className="rounded-lg py-2.5 text-[13px] font-bold uppercase tracking-wider transition-all disabled:opacity-40"
                style={S.btnPrimary}
              >
                Unlock
              </button>
            </div>

          ) : (
            <>
              {/* ── Venue selector ── */}
              <div className="flex flex-col gap-2">
                <label className="text-[9px] font-bold uppercase tracking-widest" style={S.label}>Venue</label>
                <div className="flex gap-1.5">
                  {[true, false].map((isCurrent) => (
                    <button
                      key={String(isCurrent)}
                      onClick={() => { setUseCurrentVenue(isCurrent); if (isCurrent) { setSelectedVenue(null); setVenueQuery(""); } }}
                      className="text-[11px] font-bold px-2.5 py-1 rounded transition-all"
                      style={useCurrentVenue === isCurrent ? S.btnPrimary : S.btnMuted}
                    >
                      {isCurrent ? "Current venue" : "Search other"}
                    </button>
                  ))}
                </div>

                {useCurrentVenue ? (
                  <p className="text-[12px] flex items-center gap-1.5" style={{ color: "#E6D3A3" }}>
                    <span className="material-symbols-outlined text-[13px]">check_circle</span>
                    {venueName} — {venueArea}
                  </p>
                ) : (
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Search venue…"
                      value={venueQuery}
                      onChange={(e) => { setVenueQuery(e.target.value); setSelectedVenue(null); }}
                      className="w-full rounded-lg px-3 py-2.5 text-[13px] focus:outline-none transition-all"
                      style={S.input}
                      onFocus={(e) => (e.target.style.borderColor = "rgba(230,211,163,0.4)")}
                      onBlur={(e) => (e.target.style.borderColor = "rgba(39,39,42,0.8)")}
                    />
                    {searching && (
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[11px]" style={{ color: "#71717A" }}>searching…</span>
                    )}
                    {venueResults.length > 0 && (
                      <div className="absolute top-full left-0 right-0 mt-1 rounded-xl z-10 overflow-hidden shadow-2xl" style={{ background: "#18181b", border: "1px solid rgba(39,39,42,0.9)" }}>
                        {venueResults.map((v) => (
                          <button
                            key={v.id}
                            onClick={() => selectVenue(v)}
                            className="w-full text-left px-3 py-2.5 transition-colors border-b last:border-0"
                            style={{ borderColor: "rgba(39,39,42,0.5)" }}
                            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = "rgba(39,39,42,0.5)")}
                            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = "transparent")}
                          >
                            <p className="text-[13px] font-medium" style={{ color: "#F5F5F5" }}>{v.name}</p>
                            <p className="text-[11px]" style={{ color: "#71717A" }}>{v.area}, {v.city}</p>
                          </button>
                        ))}
                      </div>
                    )}
                    {selectedVenue && (
                      <p className="text-[12px] flex items-center gap-1.5 mt-1.5" style={{ color: "#E6D3A3" }}>
                        <span className="material-symbols-outlined text-[13px]">check_circle</span>
                        {selectedVenue.name} — {selectedVenue.area}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* ── Prospect name ── */}
              <div className="flex flex-col gap-2">
                <label className="text-[9px] font-bold uppercase tracking-widest" style={S.label}>Prospect name</label>
                <input
                  type="text"
                  placeholder="e.g. Rahul, The Sharma Group"
                  value={prospectName}
                  onChange={(e) => setProspectName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                  className="w-full rounded-lg px-3 py-2.5 text-[13px] focus:outline-none transition-all"
                  style={S.input}
                  onFocus={(e) => (e.target.style.borderColor = "rgba(230,211,163,0.4)")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(39,39,42,0.8)")}
                />
              </div>

              {/* ── Expiry ── */}
              <div className="flex flex-col gap-2">
                <label className="text-[9px] font-bold uppercase tracking-widest" style={S.label}>Link expiry</label>
                <div className="flex gap-1.5 flex-wrap">
                  {[24, 48, 72, 168].map((h) => (
                    <button
                      key={h}
                      onClick={() => setHours(h)}
                      className="px-2.5 py-1 rounded text-[12px] font-bold transition-all"
                      style={hours === h ? S.btnPrimary : S.btnMuted}
                    >
                      {h === 24 ? "24h" : h === 48 ? "48h" : h === 72 ? "72h" : "1 week"}
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <p className="text-[12px] rounded-lg px-3 py-2" style={{ color: "#FB7185", background: "rgba(251,113,133,0.08)", border: "1px solid rgba(251,113,133,0.2)" }}>
                  {error}
                </p>
              )}

              <button
                onClick={handleGenerate}
                disabled={!activeVenueId || !prospectName.trim() || generating}
                className="rounded-lg py-2.5 text-[13px] font-bold uppercase tracking-wider transition-all disabled:opacity-40 flex items-center justify-center gap-2"
                style={S.btnPrimary}
              >
                {generating ? (
                  <><div className="w-3.5 h-3.5 border-2 rounded-full animate-spin" style={{ borderColor: "rgba(230,211,163,0.3)", borderTopColor: "#E6D3A3" }} />Generating…</>
                ) : (
                  <><span className="material-symbols-outlined text-[15px]">link</span>Generate demo link</>
                )}
              </button>

              {/* ── Result ── */}
              {result && (
                <div className="rounded-xl p-4 flex flex-col gap-3" style={{ background: "rgba(16,185,129,0.05)", border: "1px solid rgba(16,185,129,0.2)" }}>
                  <p className="text-[13px] font-bold flex items-center gap-1.5" style={{ color: "#10B981" }}>
                    <span className="material-symbols-outlined text-[15px]">check_circle</span>
                    {result.prospectName} · {result.expiresHours}h
                  </p>
                  <div className="flex items-center gap-2 rounded-lg px-3 py-2" style={S.card}>
                    <p className="flex-1 text-[10px] break-all" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#A1A1AA" }}>{result.url}</p>
                    <button
                      onClick={() => copyUrl(result.url)}
                      className="shrink-0 rounded px-2 py-1 text-[11px] font-bold flex items-center gap-1 transition-all"
                      style={S.btnPrimary}
                    >
                      <span className="material-symbols-outlined text-[12px]">{copied ? "check" : "content_copy"}</span>
                      {copied ? "Copied!" : "Copy"}
                    </button>
                  </div>
                </div>
              )}

              {/* ── History ── */}
              {history.length > 0 && (
                <div className="flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <p className="text-[9px] font-bold uppercase tracking-widest" style={S.label}>Recent links</p>
                    <button
                      onClick={() => { setHistory([]); localStorage.removeItem(HISTORY_KEY); }}
                      className="text-[11px] transition-colors"
                      style={{ color: "rgba(161,161,170,0.4)" }}
                      onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#FB7185")}
                      onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(161,161,170,0.4)")}
                    >
                      Clear
                    </button>
                  </div>
                  {history.slice(0, 8).map((h, idx) => (
                    <div key={idx} className="rounded-lg px-3 py-2.5 flex items-center gap-3" style={S.card}>
                      <div className="flex-1 min-w-0">
                        <p className="text-[13px] font-medium truncate" style={{ color: "#F5F5F5" }}>{h.prospectName}</p>
                        <p className="text-[11px] truncate" style={{ color: "#71717A" }}>{h.venueName} · {h.expiresHours}h</p>
                      </div>
                      <button
                        onClick={() => copyUrl(h.url)}
                        title="Copy"
                        className="shrink-0 transition-colors"
                        style={{ color: "#71717A" }}
                        onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#E6D3A3")}
                        onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "#71717A")}
                      >
                        <span className="material-symbols-outlined text-[16px]">content_copy</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Sign out */}
              <button
                onClick={() => { localStorage.removeItem(STORAGE_KEY); setAuthed(false); setAdminKey(""); setKeyInput(""); }}
                className="text-[11px] flex items-center gap-1.5 mt-auto pt-4 border-t transition-colors"
                style={{ borderColor: "rgba(39,39,42,0.5)", color: "rgba(161,161,170,0.4)" }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#FB7185")}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(161,161,170,0.4)")}
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
