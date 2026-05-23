import { getAudience, getAllSegments } from "@/lib/api";
import AudienceClient from "@/components/AudienceClient";
import CinTabBar from "@/components/CinTabBar";

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
      <div className="p-8 text-xs font-mono" style={{ color: "#FB7185" }}>
        Failed to load audience data. Make sure the backend is running on port 8000.
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 flex flex-col gap-6 max-w-[1400px] w-full mx-auto cin-stagger">
      <div className="flex flex-col gap-3">
        <div className="flex items-baseline gap-3 flex-wrap">
          <h2
            className="text-2xl md:text-3xl font-bold gold-glow"
            style={{ fontFamily: "'Clash Display', 'Inter', sans-serif" }}
          >
            {currentData.venue_name}
          </h2>
          <div className="flex items-center gap-1.5 text-xs" style={{ color: "#71717A" }}>
            <span className="material-symbols-outlined text-[14px]">location_on</span>
            {currentData.venue_area}
          </div>
        </div>
        <CinTabBar venueId={id} active="Audience" />
      </div>

      <AudienceClient currentData={currentData} allSegments={allSegments} />
    </div>
  );
}
