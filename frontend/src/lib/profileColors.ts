/**
 * Profile color utilities.
 * Maps persuasion profile keys to their CSS token variable names and Tailwind classes.
 */

export type ProfileKey =
  | 'ethos'
  | 'pathos'
  | 'logos'
  | 'authority_socialproof'
  | 'reciprocity_liking'
  | 'scarcity_commitment'
  | 'baseline';

export interface ProfileColors {
  base: string;
  light: string;
  dark: string;
  glow: string;
  gradientFrom: string;
  gradientTo: string;
}

const PROFILE_MAP: Record<ProfileKey, ProfileColors> = {
  ethos: {
    base: 'var(--color-ethos)',
    light: 'var(--color-ethos-light)',
    dark: 'var(--color-ethos-dark)',
    glow: 'var(--color-ethos-glow)',
    gradientFrom: 'var(--color-ethos-gradient-from)',
    gradientTo: 'var(--color-ethos-gradient-to)',
  },
  pathos: {
    base: 'var(--color-pathos)',
    light: 'var(--color-pathos-light)',
    dark: 'var(--color-pathos-dark)',
    glow: 'var(--color-pathos-glow)',
    gradientFrom: 'var(--color-pathos-gradient-from)',
    gradientTo: 'var(--color-pathos-gradient-to)',
  },
  logos: {
    base: 'var(--color-logos)',
    light: 'var(--color-logos-light)',
    dark: 'var(--color-logos-dark)',
    glow: 'var(--color-logos-glow)',
    gradientFrom: 'var(--color-logos-gradient-from)',
    gradientTo: 'var(--color-logos-gradient-to)',
  },
  authority_socialproof: {
    base: 'var(--color-authority)',
    light: 'var(--color-authority-light)',
    dark: 'var(--color-authority-dark)',
    glow: 'var(--color-authority-glow)',
    gradientFrom: 'var(--color-authority-gradient-from)',
    gradientTo: 'var(--color-authority-gradient-to)',
  },
  reciprocity_liking: {
    base: 'var(--color-reciprocity)',
    light: 'var(--color-reciprocity-light)',
    dark: 'var(--color-reciprocity-dark)',
    glow: 'var(--color-reciprocity-glow)',
    gradientFrom: 'var(--color-reciprocity-gradient-from)',
    gradientTo: 'var(--color-reciprocity-gradient-to)',
  },
  scarcity_commitment: {
    base: 'var(--color-scarcity)',
    light: 'var(--color-scarcity-light)',
    dark: 'var(--color-scarcity-dark)',
    glow: 'var(--color-scarcity-glow)',
    gradientFrom: 'var(--color-scarcity-gradient-from)',
    gradientTo: 'var(--color-scarcity-gradient-to)',
  },
  baseline: {
    base: 'var(--color-baseline)',
    light: 'var(--color-baseline-light)',
    dark: 'var(--color-baseline-dark)',
    glow: 'var(--color-baseline-glow)',
    gradientFrom: 'var(--color-baseline-gradient-from)',
    gradientTo: 'var(--color-baseline-gradient-to)',
  },
};

export function getProfileColors(profile: string): ProfileColors {
  return PROFILE_MAP[profile as ProfileKey] ?? PROFILE_MAP.baseline;
}

/** Hex fallbacks for inline styles where CSS vars may not work (e.g., SVG) */
const PROFILE_HEX: Record<ProfileKey, string> = {
  ethos: '#6ea4d4',
  pathos: '#c74b4b',
  logos: '#3a9e7e',
  authority_socialproof: '#c9a227',
  reciprocity_liking: '#9b59b6',
  scarcity_commitment: '#d4712a',
  baseline: '#7a7a7a',
};

export function getProfileHex(profile: string): string {
  return PROFILE_HEX[profile as ProfileKey] ?? PROFILE_HEX.baseline;
}

/** Role color mapping */
const ROLE_COLORS: Record<string, string> = {
  werewolf: 'var(--color-werewolf)',
  villager: 'var(--color-villager)',
  seer: 'var(--color-seer)',
  doctor: 'var(--color-doctor)',
};

export function getRoleColor(role: string): string {
  return ROLE_COLORS[role.toLowerCase()] ?? 'var(--color-text-secondary)';
}

/** Bid level color mapping */
const BID_COLORS = [
  'var(--color-bid-0)',
  'var(--color-bid-1)',
  'var(--color-bid-2)',
  'var(--color-bid-3)',
  'var(--color-bid-4)',
];

const BID_LABELS = ['Silent', 'Low', 'Medium', 'High', 'Urgent'];

export function getBidColor(level: number): string {
  return BID_COLORS[Math.min(Math.max(level, 0), 4)];
}

export function getBidLabel(level: number): string {
  return BID_LABELS[Math.min(Math.max(level, 0), 4)];
}
