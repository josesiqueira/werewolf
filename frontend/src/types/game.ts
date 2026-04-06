import type { Player } from "./player";

export type GameStatus = "pending" | "running" | "completed" | "discarded";
export type WinnerFaction = "villagers" | "werewolves" | null;

export interface Game {
  id: string;
  created_at: string;
  status: GameStatus;
  winner: string | null;
  rounds_played: number;
  total_turns: number;
  is_degraded: boolean;
  config: Record<string, unknown> | null;
  players: Player[];
}

export interface GameListFilters {
  status?: GameStatus;
  winner?: string;
  is_degraded?: boolean;
}
