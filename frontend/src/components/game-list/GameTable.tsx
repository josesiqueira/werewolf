"use client";

import { useState } from "react";
import Link from "next/link";
import type { Game } from "@/types/game";
import type { PersuasionProfile } from "@/types/player";
import ProfileBadge from "@/components/shared/ProfileBadge";
import StatusBadge from "@/components/shared/StatusBadge";

type SortKey =
  | "created_at"
  | "status"
  | "winner"
  | "rounds_played"
  | "is_degraded";
type SortDir = "asc" | "desc";

interface GameTableProps {
  games: Game[];
}

function truncateId(id: string): string {
  return id.slice(0, 8);
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getProfiles(game: Game): PersuasionProfile[] {
  const profiles = new Set<PersuasionProfile>();
  for (const p of game.players) {
    if (p.persuasion_profile) {
      profiles.add(p.persuasion_profile);
    }
  }
  return Array.from(profiles);
}

export default function GameTable({ games }: GameTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const sorted = [...games].sort((a, b) => {
    const dir = sortDir === "asc" ? 1 : -1;
    switch (sortKey) {
      case "created_at":
        return (
          dir *
          (new Date(a.created_at).getTime() -
            new Date(b.created_at).getTime())
        );
      case "status":
        return dir * a.status.localeCompare(b.status);
      case "winner":
        return dir * (a.winner ?? "").localeCompare(b.winner ?? "");
      case "rounds_played":
        return dir * (a.rounds_played - b.rounds_played);
      case "is_degraded":
        return dir * (Number(a.is_degraded) - Number(b.is_degraded));
      default:
        return 0;
    }
  });

  if (games.length === 0) {
    return (
      <div className="glass-card text-center py-16">
        <p className="text-text-muted text-lg">No games found</p>
        <p className="text-text-muted text-sm mt-2">
          Adjust your filters or run a batch to see games here.
        </p>
      </div>
    );
  }

  return (
    <div className="glass overflow-hidden rounded-lg">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-subtle">
              <SortHeader
                label="Game ID"
                sortKey="created_at"
                currentKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
              />
              <SortHeader
                label="Date"
                sortKey="created_at"
                currentKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
              />
              <SortHeader
                label="Status"
                sortKey="status"
                currentKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
              />
              <SortHeader
                label="Winner"
                sortKey="winner"
                currentKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
              />
              <SortHeader
                label="Rounds"
                sortKey="rounds_played"
                currentKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
              />
              <th className="px-4 py-3 text-left text-2xs uppercase tracking-wide text-text-muted font-semibold">
                Profiles
              </th>
              <SortHeader
                label="Degraded"
                sortKey="is_degraded"
                currentKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
              />
            </tr>
          </thead>
          <tbody>
            {sorted.map((game) => (
              <tr
                key={game.id}
                className="border-b border-border-subtle/50 hover:bg-white/[0.02] transition-colors duration-fast"
              >
                <td className="px-4 py-3">
                  <Link
                    href={`/games/${game.id}`}
                    className="font-mono text-info hover:underline"
                  >
                    {truncateId(game.id)}
                  </Link>
                </td>
                <td className="px-4 py-3 text-text-secondary whitespace-nowrap">
                  {formatDate(game.created_at)}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={game.status} />
                </td>
                <td className="px-4 py-3">
                  {game.winner ? (
                    <span
                      className="text-sm font-medium capitalize"
                      style={{
                        color:
                          game.winner === "werewolves"
                            ? "var(--color-werewolf)"
                            : "var(--color-villager)",
                      }}
                    >
                      {game.winner}
                    </span>
                  ) : (
                    <span className="text-text-muted">--</span>
                  )}
                </td>
                <td className="px-4 py-3 text-text-secondary text-center">
                  {game.rounds_played}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {getProfiles(game).map((profile) => (
                      <ProfileBadge
                        key={profile}
                        profile={profile}
                        size="sm"
                      />
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  {game.is_degraded && (
                    <span
                      className="text-warning text-base"
                      title="Degraded game"
                    >
                      {"\u26A0"}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sort header helper
// ---------------------------------------------------------------------------

function SortHeader({
  label,
  sortKey,
  currentKey,
  dir,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  currentKey: SortKey;
  dir: SortDir;
  onSort: (key: SortKey) => void;
}) {
  const active = sortKey === currentKey;
  return (
    <th
      className="px-4 py-3 text-left text-2xs uppercase tracking-wide text-text-muted font-semibold cursor-pointer hover:text-text-secondary transition-colors select-none"
      onClick={() => onSort(sortKey)}
    >
      <span className="flex items-center gap-1">
        {label}
        {active && (
          <span className="text-text-secondary">
            {dir === "asc" ? "\u2191" : "\u2193"}
          </span>
        )}
      </span>
    </th>
  );
}
