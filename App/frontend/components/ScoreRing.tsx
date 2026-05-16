"use client";

interface ScoreRingProps {
  score: number;
  /** diameter in px — defaults to 80 (search cards) */
  size?: number;
  strokeWidth?: number;
}

function scoreColor(score: number): string {
  if (score >= 70) return "#22c55e";
  if (score >= 40) return "#f59e0b";
  return "#ef4444";
}

/**
 * Circular SVG health score ring.
 * Animates stroke-dashoffset on mount via CSS transition.
 */
export default function ScoreRing({
  score,
  size = 80,
  strokeWidth = 4,
}: ScoreRingProps) {
  const r = size / 2 - strokeWidth * 2;
  const circumference = 2 * Math.PI * r;
  const offset = circumference * (1 - score / 100);
  const color = scoreColor(score);
  const cx = size / 2;

  return (
    <div
      className="relative flex-shrink-0 flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg className="w-full h-full" viewBox={`0 0 ${size} ${size}`}>
        {/* Track */}
        <circle
          cx={cx}
          cy={cx}
          r={r}
          fill="none"
          stroke="#27272a"
          strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <circle
          cx={cx}
          cy={cx}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cx})`}
          style={{ transition: "stroke-dashoffset 0.8s ease-in-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span
          className="font-data-mono text-data-mono font-bold"
          style={{ color }}
        >
          {score}
        </span>
      </div>
    </div>
  );
}
