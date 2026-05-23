import Link from "next/link";
import VenueNav from "@/components/VenueNav";
import ChatDrawerWrapper from "@/components/ChatDrawerWrapper";

export default async function VenueHubLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

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

          <div className="flex items-center gap-md">
            {/* Deep Analysis link */}
            <Link
              href={`/venues/${id}/deep`}
              className="text-label-md font-label-md text-primary hover:bg-surface-container-highest transition-colors px-sm py-xs border border-outline-variant rounded flex items-center gap-xs"
            >
              <span className="hidden sm:inline">DEEP ANALYSIS</span>
              <span className="material-symbols-outlined text-[16px]">bolt</span>
            </Link>
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
