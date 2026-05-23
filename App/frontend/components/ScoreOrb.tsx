"use client";

import { useEffect, useRef } from "react";

type OrbVariant = "emerald" | "amber" | "coral" | "gold";

const VARIANT_MAP: Record<OrbVariant, { ring: string; glow: string; bg: string }> = {
  emerald: {
    ring: "#10B981",
    glow: "rgba(16,185,129,0.6)",
    bg: "radial-gradient(circle at 30% 30%, rgba(16,185,129,0.25), #0A0A0A)",
  },
  amber: {
    ring: "#F59E0B",
    glow: "rgba(245,158,11,0.6)",
    bg: "radial-gradient(circle at 30% 30%, rgba(245,158,11,0.25), #0A0A0A)",
  },
  coral: {
    ring: "#FB7185",
    glow: "rgba(251,113,133,0.6)",
    bg: "radial-gradient(circle at 30% 30%, rgba(251,113,133,0.25), #0A0A0A)",
  },
  gold: {
    ring: "#E6D3A3",
    glow: "rgba(230,211,163,0.6)",
    bg: "radial-gradient(circle at 30% 30%, rgba(230,211,163,0.25), #0A0A0A)",
  },
};

function scoreToVariant(score: number): OrbVariant {
  if (score >= 0.6) return "emerald";
  if (score >= 0.35) return "amber";
  return "coral";
}

interface ScoreOrbProps {
  label: string;
  score: number;
  variant?: OrbVariant;
}

export default function ScoreOrb({ label, score, variant }: ScoreOrbProps) {
  const orbRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const v = variant ?? scoreToVariant(score);
  const colors = VARIANT_MAP[v];
  const displayScore = Math.round(score * 100);

  // Arc ring drawn via SVG overlay
  const circumference = 2 * Math.PI * 38;
  const dash = circumference * score;

  useEffect(() => {
    const orb = orbRef.current;
    if (!orb) return;
    const ring = ringRef.current;

    function onEnter() {
      if (ring) ring.style.animation = "ringSpin3d 3s linear infinite";
    }
    function onLeave() {
      if (ring) ring.style.animation = "";
    }

    orb.addEventListener("mouseenter", onEnter);
    orb.addEventListener("mouseleave", onLeave);
    return () => {
      orb.removeEventListener("mouseenter", onEnter);
      orb.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return (
    <div
      ref={orbRef}
      className="flex flex-col items-center gap-3 cursor-pointer group"
      style={{ transformStyle: "preserve-3d", transition: "transform 0.4s cubic-bezier(0.175,0.885,0.32,1.275)" }}
      onMouseEnter={(e) => (e.currentTarget.style.transform = "scale3d(1.1,1.1,1.1) translateZ(20px)")}
      onMouseLeave={(e) => (e.currentTarget.style.transform = "scale3d(1,1,1) translateZ(0)")}
    >
      {/* Orb sphere */}
      <div
        className="relative flex items-center justify-center"
        style={{
          width: 88,
          height: 88,
          borderRadius: "50%",
          background: colors.bg,
          boxShadow: `inset -8px -8px 18px rgba(0,0,0,0.8), inset 8px 8px 18px rgba(255,255,255,0.06), 0 0 24px rgba(0,0,0,0.6)`,
          transformStyle: "preserve-3d",
        }}
      >
        {/* SVG arc ring */}
        <svg
          className="absolute inset-0 w-full h-full"
          viewBox="0 0 100 100"
          style={{ transform: "rotate(-90deg)" }}
        >
          <circle cx="50" cy="50" r="44" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="3" />
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke={colors.ring}
            strokeWidth="3"
            strokeDasharray={`${(circumference * score).toFixed(1)} ${circumference.toFixed(1)}`}
            strokeLinecap="round"
            style={{
              filter: `drop-shadow(0 0 4px ${colors.ring})`,
              transition: "stroke-dasharray 1s ease",
            }}
          />
        </svg>

        {/* Tilted decorative ring */}
        <div
          ref={ringRef}
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: "120%",
            height: "120%",
            border: `1.5px solid ${colors.ring}`,
            borderRadius: "50%",
            transform: "translate(-50%,-50%) rotateX(70deg) rotateY(20deg)",
            boxShadow: `0 0 10px ${colors.glow} inset`,
            transition: "all 0.4s ease",
            opacity: 0.7,
          }}
        />

        {/* Score value */}
        <span
          className="font-mono text-xl font-bold relative z-10"
          style={{
            color: "#E6D3A3",
            textShadow: `0 0 12px ${colors.glow}`,
            transform: "translateZ(20px)",
          }}
        >
          {displayScore}
        </span>
      </div>

      {/* Label */}
      <span
        className="text-[10px] uppercase tracking-widest font-medium text-center"
        style={{ color: "#A1A1AA", transform: "translateZ(10px)" }}
      >
        {label}
      </span>
    </div>
  );
}
