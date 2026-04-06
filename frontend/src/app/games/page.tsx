"use client";

import { useMemo, useState } from "react";
import { useGames } from "@/hooks/useGames";
import GameTable from "@/components/game-list/GameTable";
import GameFilters, {
  type GameFilterValues,
} from "@/components/game-list/GameFilters";
import type { Game } from "@/types/game";

const DEFAULT_FILTERS: GameFilterValues = {
  status: "",
  winner: "",
  profiles: [],
  degradedOnly: false,
};

export default function GamesPage() {
  const [filters, setFilters] = useState<GameFilterValues>(DEFAULT_FILTERS);

  // Fetch with server-side filters for status, winner, degraded
  const queryFilters = useMemo(
    () => ({
      status: filters.status || undefined,
      winner: filters.winner || undefined,
      is_degraded: filters.degradedOnly ? true : undefined,
    }),
    [filters.status, filters.winner, filters.degradedOnly],
  );

  const { data: games, isLoading, isError, error } = useGames(queryFilters);

  // Client-side profile filtering
  const filteredGames = useMemo(() => {
    if (!games) return [];
    if (filters.profiles.length === 0) return games;

    return games.filter((game: Game) => {
      const gameProfiles = new Set(
        game.players
          .map((p) => p.persuasion_profile)
          .filter(Boolean),
      );
      return filters.profiles.every((profile) => gameProfiles.has(profile));
    });
  }, [games, filters.profiles]);

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display text-3xl tracking-wide text-text-primary">
          Games
        </h1>
        <p className="text-text-secondary mt-2">
          Browse and filter all game records.
        </p>
      </div>

      {/* Filters */}
      <GameFilters filters={filters} onChange={setFilters} />

      {/* Content */}
      {isLoading ? (
        <div className="glass-card text-center py-16">
          <div className="inline-block w-6 h-6 border-2 border-info border-t-transparent rounded-full animate-spin" />
          <p className="text-text-muted mt-3">Loading games...</p>
        </div>
      ) : isError ? (
        <div className="glass-card text-center py-16">
          <p className="text-error text-lg">Failed to load games</p>
          <p className="text-text-muted text-sm mt-2">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-4">
            <p className="text-text-muted text-sm">
              {filteredGames.length} game{filteredGames.length !== 1 ? "s" : ""}
            </p>
          </div>
          <GameTable games={filteredGames} />
        </>
      )}
    </div>
  );
}
