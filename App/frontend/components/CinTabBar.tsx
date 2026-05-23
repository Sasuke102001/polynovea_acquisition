import Link from "next/link";

interface CinTabBarProps {
  venueId: string;
  active: string;
}

const TABS = [
  { label: "Overview",    href: (id: string) => `/venues/${id}` },
  { label: "Competitors", href: (id: string) => `/venues/${id}/competitors` },
  { label: "Transform",   href: (id: string) => `/venues/${id}/transform` },
  { label: "Marketing",   href: (id: string) => `/venues/${id}/marketing` },
  { label: "Campaign",    href: (id: string) => `/venues/${id}/campaign` },
  { label: "Audience",    href: (id: string) => `/venues/${id}/audience` },
];

export default function CinTabBar({ venueId, active }: CinTabBarProps) {
  return (
    <div
      className="flex gap-6 overflow-x-auto no-scrollbar pb-1"
      style={{ borderBottom: "1px solid rgba(39,39,42,0.6)" }}
    >
      {TABS.map((t) => {
        const isActive = t.label === active;
        return (
          <Link
            key={t.label}
            href={t.href(venueId)}
            className="whitespace-nowrap pb-2 text-xs font-medium tracking-wider uppercase transition-colors"
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              color: isActive ? "#E6D3A3" : "#71717A",
              borderBottom: isActive ? "2px solid #E6D3A3" : "2px solid transparent",
            }}
          >
            {t.label}
          </Link>
        );
      })}
    </div>
  );
}
