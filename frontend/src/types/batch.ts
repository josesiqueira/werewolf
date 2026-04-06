export type BatchStatus = "pending" | "running" | "completed" | "paused" | "failed";

export interface Batch {
  id: string;
  created_at: string;
  total_games: number;
  completed_games: number;
  failed_games: number;
  status: BatchStatus;
  config: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface BatchProgress {
  batch_id: string;
  status: BatchStatus;
  total_games: number;
  completed_games: number;
  failed_games: number;
  current_game: number;
  completion_pct: number;
  eta_seconds: number;
  games_per_minute: number;
  elapsed_seconds: number;
  degraded_count: number;
}
