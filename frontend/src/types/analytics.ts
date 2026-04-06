import type { PersuasionProfile } from "./player";

// ---------------------------------------------------------------------------
// Win Rates
// ---------------------------------------------------------------------------

export interface WinRateEntry {
  faction: string;
  profile: PersuasionProfile;
  count: number;
  wins: number;
  rate: number;
  sem: number;
  ci_lower: number;
  ci_upper: number;
}

export interface WinRateSummary {
  total_games: number;
  profiles: PersuasionProfile[];
  factions: string[];
}

export interface WinRateData {
  matrix: WinRateEntry[];
  summary: WinRateSummary;
}

// ---------------------------------------------------------------------------
// Survival
// ---------------------------------------------------------------------------

export interface SurvivalEntry {
  role: string;
  profile: PersuasionProfile;
  mean_rounds: number;
  count: number;
}

export interface SurvivalData {
  data: SurvivalEntry[];
}

// ---------------------------------------------------------------------------
// Techniques
// ---------------------------------------------------------------------------

export interface AdherenceEntry {
  profile: PersuasionProfile;
  adherence_rate: number;
  count: number;
}

export interface DeceptionIndexEntry {
  profile: PersuasionProfile;
  deception_index: number;
  count: number;
}

export interface DetectionEntry {
  technique: string;
  deception_type: string;
  suspicion_rate: number;
  count: number;
}

export interface BusThrowingEntry {
  profile: PersuasionProfile;
  bus_throwing_rate: number;
  total_wolf_votes: number;
}

export interface BandwagonEntry {
  game_id: string;
  time_to_majority: number;
  round_number: number;
}

export interface TechniquesData {
  adherence: AdherenceEntry[];
  deception_index: DeceptionIndexEntry[];
  detection: DetectionEntry[];
  bus_throwing: BusThrowingEntry[];
  bandwagon: BandwagonEntry[];
}

// ---------------------------------------------------------------------------
// Accusations
// ---------------------------------------------------------------------------

export interface AccusationNode {
  id: string;
  profile: PersuasionProfile;
  count: number;
}

export interface AccusationEdge {
  source: string;
  target: string;
  weight: number;
}

export interface AccusationsData {
  nodes: AccusationNode[];
  edges: AccusationEdge[];
}

// ---------------------------------------------------------------------------
// Vote Swing (derived from techniques.bandwagon or separate)
// ---------------------------------------------------------------------------

export interface VoteSwingEntry {
  profile: PersuasionProfile;
  avg_vote_change: number;
  count: number;
}
