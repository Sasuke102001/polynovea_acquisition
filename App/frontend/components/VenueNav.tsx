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
    if (href === `/venues/${venueId}`) {
      // exact match for overview (avoid matching /venues/123/competitors etc.)
      return pathname === href;
    }
    return pathname.startsWith(href);
  }

  const isDeep = pathname.startsWith(`/venues/${venueId}/deep`);

  return (
    <>
      {/* ── Sidebar (desktop) ── */}
      <nav className="hidden md:flex flex-col bg-surface-container border-r border-outline-variant h-screen w-60 fixed left-0 top-0 z-40 py-lg px-md">
        <div className="mb-xl px-sm">
          <Link href="/" className="block">
            <h2 className="text-label-md font-label-md text-primary tracking-tighter font-bold uppercase">
              ANALYTICS_SUITE
            </h2>
          </Link>
        </div>

        <ul className="flex flex-col gap-xs">
          {NAV_ITEMS.map((item) => {
            const href = item.href(venueId);
            const active = isActive(href) && !isDeep;
            return (
              <li key={item.label}>
                <Link
                  href={href}
                  className={`flex items-center gap-md px-sm py-sm rounded-lg transition-colors text-label-md font-label-md ${
                    active
                      ? "bg-secondary-container text-on-secondary-container scale-[0.98]"
                      : "text-on-surface-variant hover:bg-surface-variant"
                  }`}
                >
                  <span className="material-symbols-outlined text-[20px]">
                    {item.icon}
                  </span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* ── Bottom nav (mobile) ── */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center h-14 bg-background border-t border-outline-variant">
        {NAV_ITEMS.map((item) => {
          const href = item.href(venueId);
          const active = isActive(href) && !isDeep;
          return (
            <Link
              key={item.label}
              href={href}
              className={`flex flex-col items-center justify-center w-16 h-full transition-all ${
                active
                  ? "text-primary font-bold translate-y-[-2px]"
                  : "text-on-surface-variant opacity-60 hover:text-primary"
              }`}
            >
              <span className="material-symbols-outlined text-[24px]">
                {item.icon}
              </span>
              <span className="text-label-sm font-label-sm mt-1">
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
