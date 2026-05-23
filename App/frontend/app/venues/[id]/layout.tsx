import Link from "next/link";
import VenueNav from "@/components/VenueNav";
import ChatDrawerWrapper from "@/components/ChatDrawerWrapper";
import AdminDemoPanel from "@/components/AdminDemoPanel";
import ParticleCanvas from "@/components/ParticleCanvas";

async function fetchVenueMeta(id: string): Promise<{ name: string; area: string }> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/venues/${id}/overview`,
      { next: { revalidate: 3600 } }
    );
    if (!res.ok) return { name: "", area: "" };
    const data = await res.json();
    return { name: data.venue_name ?? "", area: data.area ?? "" };
  } catch {
    return { name: "", area: "" };
  }
}

export default async function VenueHubLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const meta = await fetchVenueMeta(id);

  return (
    <div className="flex min-h-screen" style={{ background: "#0A0A0A" }}>
      {/* Ambient particle layer */}
      <ParticleCanvas />

      {/* Sidebar + mobile bottom nav */}
      <VenueNav venueId={id} />

      {/* Main area */}
      <div className="flex-1 md:ml-60 flex flex-col min-h-screen pb-16 md:pb-0" style={{ position: "relative", zIndex: 1 }}>
        {/* Cinematic top bar */}
        <header
          className="flex justify-between items-center w-full px-6 h-14 sticky top-0 z-30"
          style={{
            background: "rgba(10,10,10,0.88)",
            backdropFilter: "blur(20px)",
            borderBottom: "1px solid rgba(39,39,42,0.6)",
            boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
          }}
        >
          {/* Left: logo mark + title */}
          <div className="flex items-center gap-3">
            <div
              className="w-6 h-6 rounded flex items-center justify-center"
              style={{ background: "rgba(230,211,163,0.1)", border: "1px solid rgba(230,211,163,0.2)" }}
            >
              <span className="material-symbols-outlined text-[13px]" style={{ color: "#E6D3A3" }}>analytics</span>
            </div>
            <span
              className="text-xs font-bold tracking-widest uppercase hidden md:block"
              style={{ fontFamily: "'JetBrains Mono', monospace", color: "#E6D3A3" }}
            >
              VENUE_INTELLIGENCE_v4.0
            </span>
          </div>

          {/* Right: deep analysis + admin */}
          <div className="flex items-center gap-3">
            <Link
              href={`/venues/${id}/deep`}
              className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold tracking-widest uppercase transition-all duration-200"
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                color: "#E6D3A3",
                border: "1px solid rgba(230,211,163,0.25)",
                borderRadius: 4,
                background: "rgba(230,211,163,0.05)",
              }}
            >
              <span className="hidden sm:inline">DEEP ANALYSIS</span>
              <span className="material-symbols-outlined text-[14px]">bolt</span>
            </Link>

            <AdminDemoPanel
              venueId={parseInt(id)}
              venueName={meta.name}
              venueArea={meta.area}
            />
          </div>
        </header>

        {/* Page content */}
        {children}
      </div>

      {/* Chat drawer */}
      <ChatDrawerWrapper venueId={parseInt(id)} />
    </div>
  );
}
