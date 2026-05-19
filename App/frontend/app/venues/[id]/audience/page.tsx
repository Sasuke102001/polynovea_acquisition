import Link from "next/link";
import { getAudience, getAllSegments } from "@/lib/api";
import AudienceClient from "@/components/AudienceClient";

function VenueTabs({ venueId }: { venueId: string }) {
  const tabs = [
    { label: "Overview",    href: `/venues/${venueId}` },
    { label: "Competitors", href: `/venues/${venueId}/competitors` },
    { label: "Transform",   href: `/venues/${venueId}/transform` },
    { label: "Marketing",   href: `/venues/${venueId}/marketing` },
    { label: "Campaign",    href: `/venues/${venueId}/campaign` },
    { label: "Audience",    href: `/venues/${venueId}/audience` },
  ];
  return (
    <div className="flex gap-md border-b border-outline-variant mt-sm overflow-x-auto no-scrollbar">
      {tabs.map((tab) => (
        <Link
          key={tab.label}
          href={tab.href}
          className={`pb-sm px-sm text-label-md font-label-md whitespace-nowrap transition-colors ${
            tab.label === "Audience"
              ? "text-primary border-b-2 border-primary"
              : "text-on-surface-variant hover:text-primary"
          }`}
        >
          {tab.label}
        </Link>
      ))}
    </div>
  );
}

export default async function AudiencePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let currentData;
  let allSegments;
  try {
    [currentData, { segments: allSegments }] = await Promise.all([
      getAudience(id),
      getAllSegments(),
    ]);
  } catch {
    return (
      <div className="p-margin text-error font-body-sm text-body-sm">
        Failed to load audience data. Make sure the backend is running on port 8000.
      </div>
    );
  }

  return (
    <div className="p-margin flex flex-col gap-lg max-w-[1400px] w-full mx-auto">
      {/* Venue header */}
      <div className="flex flex-col gap-xs border-b border-outline-variant pb-md">
        <div className="flex items-baseline gap-sm flex-wrap">
          <h2 className="text-headline-lg font-headline-lg text-primary-container font-bold">
            {currentData.venue_name}
          </h2>
          <div className="flex items-center gap-xs text-on-surface-variant">
            <span className="material-symbols-outlined text-[16px]">location_on</span>
            <span className="text-body-sm font-body-sm">{currentData.venue_area}</span>
          </div>
        </div>
        <VenueTabs venueId={id} />
      </div>

      <AudienceClient currentData={currentData} allSegments={allSegments} />
    </div>
  );
}
