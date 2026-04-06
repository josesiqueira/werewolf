import type { Game, GameListFilters } from "@/types/game";
import type { Turn } from "@/types/turn";
import type { Batch, BatchProgress } from "@/types/batch";
import type {
  WinRateData,
  SurvivalData,
  TechniquesData,
  AccusationsData,
} from "@/types/analytics";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Generic fetch wrapper
// ---------------------------------------------------------------------------

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, `${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Games
// ---------------------------------------------------------------------------

export async function fetchGames(filters?: GameListFilters): Promise<Game[]> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.winner) params.set("winner", filters.winner);
  if (filters?.is_degraded !== undefined)
    params.set("is_degraded", String(filters.is_degraded));

  const qs = params.toString();
  return apiFetch<Game[]>(`/api/games${qs ? `?${qs}` : ""}`);
}

export async function fetchGame(gameId: string): Promise<Game> {
  return apiFetch<Game>(`/api/games/${gameId}`);
}

export async function fetchGameTurns(gameId: string): Promise<Turn[]> {
  return apiFetch<Turn[]>(`/api/games/${gameId}/turns`);
}

export async function fetchGamePlayers(gameId: string): Promise<Game["players"]> {
  const game = await apiFetch<Game>(`/api/games/${gameId}`);
  return game.players;
}

export async function fetchGameReplay(gameId: string) {
  return apiFetch<{
    game: Game;
    players: Game["players"];
    turns: Turn[];
    events: Array<{
      id: string;
      round_number: number;
      event_type: string;
      details: Record<string, unknown> | null;
      created_at: string | null;
    }>;
  }>(`/api/games/${gameId}/replay`);
}

// ---------------------------------------------------------------------------
// Batches
// ---------------------------------------------------------------------------

export async function fetchBatches(): Promise<Batch[]> {
  return apiFetch<Batch[]>("/api/batch");
}

export async function fetchBatchStatus(batchId: string): Promise<BatchProgress> {
  return apiFetch<BatchProgress>(`/api/batch/${batchId}/status`);
}

export async function createBatch(config: {
  num_games: number;
  max_parallelism?: number;
  debate_cap?: number;
  use_llm?: boolean;
}): Promise<Batch> {
  return apiFetch<Batch>("/api/batch", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

function analyticsParams(batchId?: string): string {
  if (!batchId) return "";
  const params = new URLSearchParams();
  params.set("batch_id", batchId);
  return `?${params.toString()}`;
}

export async function fetchWinRates(batchId?: string): Promise<WinRateData> {
  return apiFetch<WinRateData>(`/api/analytics/winrates${analyticsParams(batchId)}`);
}

export async function fetchSurvival(batchId?: string): Promise<SurvivalData> {
  return apiFetch<SurvivalData>(`/api/analytics/survival${analyticsParams(batchId)}`);
}

export async function fetchTechniques(batchId?: string): Promise<TechniquesData> {
  return apiFetch<TechniquesData>(`/api/analytics/techniques${analyticsParams(batchId)}`);
}

export async function fetchAccusations(batchId?: string): Promise<AccusationsData> {
  return apiFetch<AccusationsData>(`/api/analytics/accusations${analyticsParams(batchId)}`);
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export function getExportUrl(format: "csv" | "json" | "ndjson", batchId?: string): string {
  const params = new URLSearchParams();
  if (batchId) params.set("batch_id", batchId);
  const qs = params.toString();
  return `${API_BASE}/api/export/${format}${qs ? `?${qs}` : ""}`;
}

export { ApiError };
