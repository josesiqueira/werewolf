import type { PersuasionProfile } from "@/types/player";

const PROFILE_CONFIG: Record<
  PersuasionProfile,
  { label: string; color: string; glow: string }
> = {
  ethos: {
    label: "Ethos",
    color: "var(--color-ethos)",
    glow: "var(--color-ethos-glow)",
  },
  pathos: {
    label: "Pathos",
    color: "var(--color-pathos)",
    glow: "var(--color-pathos-glow)",
  },
  logos: {
    label: "Logos",
    color: "var(--color-logos)",
    glow: "var(--color-logos-glow)",
  },
  authority_socialproof: {
    label: "Authority",
    color: "var(--color-authority)",
    glow: "var(--color-authority-glow)",
  },
  reciprocity_liking: {
    label: "Reciprocity",
    color: "var(--color-reciprocity)",
    glow: "var(--color-reciprocity-glow)",
  },
  scarcity_commitment: {
    label: "Scarcity",
    color: "var(--color-scarcity)",
    glow: "var(--color-scarcity-glow)",
  },
  baseline: {
    label: "Baseline",
    color: "var(--color-baseline)",
    glow: "var(--color-baseline-glow)",
  },
};

interface ProfileBadgeProps {
  profile: PersuasionProfile;
  size?: "sm" | "md" | "lg";
  dimmed?: boolean;
}

export default function ProfileBadge({
  profile,
  size = "md",
  dimmed = false,
}: ProfileBadgeProps) {
  const config = PROFILE_CONFIG[profile] ?? PROFILE_CONFIG.baseline;

  const sizeClasses = {
    sm: "px-2 py-0.5 text-2xs",
    md: "px-3 py-1 text-xs",
    lg: "px-4 py-2 text-sm",
  };

  return (
    <span
      className={`
        inline-flex items-center rounded-full font-semibold uppercase tracking-wide
        transition-opacity duration-base
        ${sizeClasses[size]}
        ${dimmed ? "opacity-40" : ""}
      `}
      style={{
        backgroundColor: config.glow,
        color: config.color,
        border: `1px solid color-mix(in srgb, ${config.color} 30%, transparent)`,
      }}
    >
      {config.label}
    </span>
  );
}

export { PROFILE_CONFIG };
