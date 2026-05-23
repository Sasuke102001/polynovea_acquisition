"use client";

import { useRef, MouseEvent, ReactNode } from "react";

interface Tilt3DCardProps {
  children: ReactNode;
  className?: string;
  intensity?: number;
}

export default function Tilt3DCard({ children, className = "", intensity = 10 }: Tilt3DCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);

  function handleMouseMove(e: MouseEvent<HTMLDivElement>) {
    const card = cardRef.current;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
    const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
    card.style.transform = `perspective(600px) rotateY(${nx * intensity}deg) rotateX(${-ny * intensity}deg) translateZ(8px)`;
  }

  function handleMouseLeave() {
    const card = cardRef.current;
    if (!card) return;
    card.style.transform = "perspective(600px) rotateY(0deg) rotateX(0deg) translateZ(0px)";
  }

  return (
    <div
      ref={cardRef}
      className={className}
      style={{ transition: "transform 0.4s cubic-bezier(0.175,0.885,0.32,1.275)", transformStyle: "preserve-3d" }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </div>
  );
}
