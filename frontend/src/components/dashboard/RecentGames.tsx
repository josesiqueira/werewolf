"use client";

import Link from "next/link";
import type { Game } from "@/types/game";
import StatusBadge from "@/components/shared/StatusBadge";
import ProfileBadge from "@/components/shared/ProfileBadge";
import type { PersuasionProfile } from "@/types/player";

interface RecentGamesProps {
  games: Game[];
  limit?: number;
}

function truncateId(id: string): string {
  return id.slice(0, 8);
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function RecentGames({ games, limit = 8 }: RecentGamesProps) {
  const recent = [...games]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
    .slice(0, limit);

  if (recent.length === 0) {
    return (
      <div className="glass-card text-center py-10">
        <p className="text-text-muted">No recent games</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {recent.map((game) => {
        const profiles = Array.from(
          new Set(
            game.players
              .map((p) => p.persuasion_profile)
              .filter(Boolean) as PersuasionProfile[],
          ),
        );

        return (
          <Link
            key={game.id}
            href={`/games/${game.id}`}
            className="glass-card block hover:bg-white/[0.04] transition-colors duration-fast group"
            style={{ padding: "var(--space-4)" }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm text-info group-hover:underline">
                  {truncateId(game.id)}
                </span>
                <StatusBadge status={game.status} />
                {game.is_degraded && (
                  <StatusBadge status="degraded" showLabel={false} />
                )}
              </div>
              <span className="text-text-muted text-xs">
                {timeAgo(game.created_at)}
              </span>
            </div>

            <div className="flex items-center justify-between mt-2">
              <div className="flex flex-wrap gap-1">
                {profiles.slice(0, 4).map((profile) => (
                  <ProfileBadge key={profile} profile={profile} size="sm" />
                ))}
                {profiles.length > 4 && (
                  <span className="text-text-muted text-2xs self-center">
                    +{profiles.length - 4}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3 text-xs text-text-secondary">
                <span>{game.rounds_played} rounds</span>
                {game.winner && (
                  <span
                    className="font-medium capitalize"
                    style={{
                      color:
                        game.winner === "werewolves"
                          ? "var(--color-werewolf)"
                          : "var(--color-villager)",
                    }}
                  >
                    {game.winner}
                  </span>
                )}
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
