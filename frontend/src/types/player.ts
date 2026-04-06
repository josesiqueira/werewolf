export type Role = "werewolf" | "seer" | "doctor" | "villager";

export type PersuasionProfile =
  | "ethos"
  | "pathos"
  | "logos"
  | "authority_socialproof"
  | "reciprocity_liking"
  | "scarcity_commitment"
  | "baseline";

export interface Player {
  id: string;
  game_id: string;
  agent_name: string;
  role: Role;
  persona: string | null;
  persuasion_profile: PersuasionProfile | null;
  is_mayor: boolean;
  eliminated_round: number | null;
  survived: boolean;
  character_image: string | null;
}
