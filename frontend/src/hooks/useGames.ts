import { useQuery } from "@tanstack/react-query";
import { fetchGames, fetchGame, fetchGameTurns } from "@/lib/api";
import type { GameListFilters } from "@/types/game";

export function useGames(filters?: GameListFilters) {
  return useQuery({
    queryKey: ["games", filters],
    queryFn: () => fetchGames(filters),
    staleTime: 15_000,
  });
}

export function useGame(gameId: string) {
  return useQuery({
    queryKey: ["game", gameId],
    queryFn: () => fetchGame(gameId),
    enabled: !!gameId,
  });
}

export function useGameTurns(gameId: string) {
  return useQuery({
    queryKey: ["game-turns", gameId],
    queryFn: () => fetchGameTurns(gameId),
    enabled: !!gameId,
  });
}
