import type { PersuasionProfile } from "@/types/player";

/**
 * Maps persuasion profile keys to their hex color values from design tokens.
 * These are used for Recharts / D3 fills where CSS vars are not directly usable.
 */
export const PROFILE_COLORS: Record<PersuasionProfile, string> = {
  ethos: "#6ea4d4",
  pathos: "#c74b4b",
  logos: "#3a9e7e",
  authority_socialproof: "#c9a227",
  reciprocity_liking: "#9b59b6",
  scarcity_commitment: "#d4712a",
  baseline: "#7a7a7a",
};

export const PROFILE_COLORS_LIGHT: Record<PersuasionProfile, string> = {
  ethos: "#a3c7e8",
  pathos: "#e07a7a",
  logos: "#6cc4a5",
  authority_socialproof: "#e0c45a",
  reciprocity_liking: "#c084d4",
  scarcity_commitment: "#e89a5a",
  baseline: "#a0a0a0",
};

export const PROFILE_LABELS: Record<PersuasionProfile, string> = {
  ethos: "Ethos",
  pathos: "Pathos",
  logos: "Logos",
  authority_socialproof: "Authority",
  reciprocity_liking: "Reciprocity",
  scarcity_commitment: "Scarcity",
  baseline: "Baseline",
};

export const ALL_PROFILES: PersuasionProfile[] = [
  "ethos",
  "pathos",
  "logos",
  "authority_socialproof",
  "reciprocity_liking",
  "scarcity_commitment",
  "baseline",
];

export function getProfileColor(profile: string): string {
  return PROFILE_COLORS[profile as PersuasionProfile] ?? "#7a7a7a";
}

export function getProfileLabel(profile: string): string {
  return PROFILE_LABELS[profile as PersuasionProfile] ?? profile;
}

/** Shared dark theme for Recharts */
export const RECHARTS_DARK_THEME = {
  backgroundColor: "transparent",
  textColor: "#a09d95",
  gridColor: "#1e1e2c",
  tooltipBg: "#181824",
  tooltipBorder: "#2a2a3a",
  axisColor: "#605e58",
};
