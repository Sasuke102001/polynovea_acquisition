"use client";

/**
 * ChatDrawerWrapper
 * Mounted once in the venue layout — stays alive across all tab navigations.
 * Derives the current tab from the URL so ChatDrawer always gets the right context.
 */

import { usePathname } from "next/navigation";
import ChatDrawer from "./ChatDrawer";

type Tab = "marketing" | "competitors" | "transform" | "deep_risk" | "overview" | "audience";

const PATH_TO_TAB: Record<string, Tab> = {
  campaign:    "marketing",
  marketing:   "marketing",
  competitors: "competitors",
  transform:   "transform",
  deep:        "deep_risk",
  audience:    "audience",
};

interface ChatDrawerWrapperProps {
  venueId: number;
}

export default function ChatDrawerWrapper({ venueId }: ChatDrawerWrapperProps) {
  const pathname = usePathname();
  // Last segment of the path — if it's a number we're on the overview page
  const segment  = pathname.split("/").at(-1) ?? "";
  const tab: Tab = PATH_TO_TAB[segment] ?? "overview";

  return <ChatDrawer venueId={venueId} tab={tab} />;
}
