import Link from "next/link";
import VenueNav from "@/components/VenueNav";
import ChatDrawerWrapper from "@/components/ChatDrawerWrapper";
import AdminDemoPanel from "@/components/AdminDemoPanel";

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
  const meta   = await fetchVenueMeta(id);

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar + mobile bottom nav */}
      <VenueNav venueId={id} />

      {/* Main area — offset for sidebar on md+ */}
      <div className="flex-1 md:ml-60 flex flex-col min-h-screen pb-16 md:pb-0">
        {/* Top app bar */}
        <header className="flex justify-between items-center w-full px-margin h-16 bg-surface border-b border-outline-variant sticky top-0 z-30">
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined text-primary text-[24px]">analytics</span>
            <h1 className="text-headline-md font-headline-md font-bold text-primary tracking-tighter hidden md:block">
              VENUE_INTELLIGENCE_v4.0
            </h1>
          </div>

          <div className="flex items-center gap-sm">
            {/* Deep Analysis link */}
            <Link
              href={`/venues/${id}/deep`}
              className="text-label-md font-label-md text-primary hover:bg-surface-container-highest transition-colors px-sm py-xs border border-outline-variant rounded flex items-center gap-xs"
            >
              <span className="hidden sm:inline">DEEP ANALYSIS</span>
              <span className="material-symbols-outlined text-[16px]">bolt</span>
            </Link>

            {/* Admin demo panel */}
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

      {/* Chat drawer — mounted once, survives tab navigation */}
      <ChatDrawerWrapper venueId={parseInt(id)} />
    </div>
  );
}
