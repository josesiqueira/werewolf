export type GamePhase =
  | "INIT"
  | "MAYOR_CAMPAIGN"
  | "MAYOR_VOTE"
  | "NIGHT"
  | "DAY_BID"
  | "DAY_SPEECH"
  | "VOTE"
  | "GAME_OVER";

export type DeceptionLabel =
  | "truthful"
  | "omission"
  | "distortion"
  | "fabrication"
  | "misdirection";

export interface Turn {
  id: string;
  game_id: string;
  player_id: string;
  round_number: number;
  phase: GamePhase;
  prompt_sent: string | null;
  completion_received: string | null;
  private_reasoning: string | null;
  public_statement: string | null;
  vote_target: string | null;
  bid_level: number | null;
  technique_self_label: string | null;
  deception_self_label: DeceptionLabel | null;
  confidence: number | null;
  is_default_response: boolean;
  token_count_input: number | null;
  token_count_output: number | null;
  latency_ms: number | null;
  created_at: string;
}
