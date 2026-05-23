"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface VenueNavProps {
  venueId: string;
}

const NAV_ITEMS = [
  { label: "Overview",    icon: "dashboard",       href: (id: string) => `/venues/${id}` },
  { label: "Competitors", icon: "compare_arrows",  href: (id: string) => `/venues/${id}/competitors` },
  { label: "Transform",   icon: "auto_graph",      href: (id: string) => `/venues/${id}/transform` },
  { label: "Marketing",   icon: "campaign",        href: (id: string) => `/venues/${id}/marketing` },
  { label: "Audience",    icon: "groups",          href: (id: string) => `/venues/${id}/audience` },
];

export default function VenueNav({ venueId }: VenueNavProps) {
  const pathname = usePathname();

  function isActive(href: string): boolean {
    if (href === `/venues/${venueId}`) return pathname === href;
    return pathname.startsWith(href);
  }

  const isDeep = pathname.startsWith(`/venues/${venueId}/deep`);

  return (
    <>
      {/* ── Sidebar (desktop) ── */}
      <nav
        className="hidden md:flex flex-col h-screen w-60 fixed left-0 top-0 z-40 py-8 px-4"
        style={{
          background: "rgba(10,10,10,0.92)",
          backdropFilter: "blur(20px)",
          borderRight: "1px solid rgba(39,39,42,0.7)",
          boxShadow: "4px 0 30px rgba(0,0,0,0.5)",
        }}
      >
        {/* Logo */}
        <div className="mb-10 px-2">
          <Link href="/" className="block group">
            <div className="flex items-center gap-2">
              <div
                className="w-7 h-7 rounded flex items-center justify-center"
                style={{ background: "rgba(230,211,163,0.12)", border: "1px solid rgba(230,211,163,0.25)" }}
              >
                <span className="material-symbols-outlined text-[16px]" style={{ color: "#E6D3A3" }}>analytics</span>
              </div>
              <span
                className="text-xs font-bold tracking-widest uppercase"
                style={{ fontFamily: "'JetBrains Mono', monospace", color: "#E6D3A3" }}
              >
                POLYNOVEA
              </span>
            </div>
            <div className="text-[9px] tracking-[0.2em] uppercase mt-1 ml-9" style={{ color: "#71717A" }}>
              Intelligence Suite
            </div>
          </Link>
        </div>

        {/* Nav items */}
        <ul className="flex flex-col gap-1">
          {NAV_ITEMS.map((item, idx) => {
            const href = item.href(venueId);
            const active = isActive(href) && !isDeep;
            return (
              <li key={item.label}>
                <Link
                  href={href}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-xs font-medium tracking-wider uppercase group relative"
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    background: active ? "rgba(230,211,163,0.1)" : "transparent",
                    color: active ? "#E6D3A3" : "#71717A",
                    border: active ? "1px solid rgba(230,211,163,0.2)" : "1px solid transparent",
                    boxShadow: active ? "0 0 20px rgba(230,211,163,0.05) inset" : "none",
                    animationDelay: `${idx * 0.08}s`,
                  }}
                >
                  {/* Active indicator line */}
                  {active && (
                    <span
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 rounded-full"
                      style={{ background: "#E6D3A3", boxShadow: "0 0 8px #E6D3A3" }}
                    />
                  )}
                  <span
                    className="material-symbols-outlined text-[18px] transition-colors"
                    style={{ color: active ? "#E6D3A3" : "#71717A" }}
                  >
                    {item.icon}
                  </span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Footer divider */}
        <div className="mt-auto pt-6 border-t" style={{ borderColor: "rgba(39,39,42,0.5)" }}>
          <div className="text-[9px] tracking-widest uppercase px-2" style={{ color: "#3F3F46" }}>
            v4.0 · ACQUISITION SYSTEM
          </div>
        </div>
      </nav>

      {/* ── Bottom nav (mobile) ── */}
      <nav
        className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center h-14"
        style={{
          background: "rgba(10,10,10,0.95)",
          backdropFilter: "blur(20px)",
          borderTop: "1px solid rgba(39,39,42,0.7)",
        }}
      >
        {NAV_ITEMS.map((item) => {
          const href = item.href(venueId);
          const active = isActive(href) && !isDeep;
          return (
            <Link
              key={item.label}
              href={href}
              className="flex flex-col items-center justify-center w-16 h-full transition-all"
              style={{ color: active ? "#E6D3A3" : "#71717A" }}
            >
              <span className="material-symbols-outlined text-[22px]">{item.icon}</span>
              <span className="text-[9px] mt-0.5 tracking-wider uppercase" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
