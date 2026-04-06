"use client";

import type { GameStatus } from "@/types/game";
import type { PersuasionProfile } from "@/types/player";

export interface GameFilterValues {
  status: GameStatus | "";
  winner: string;
  profiles: PersuasionProfile[];
  degradedOnly: boolean;
}

interface GameFiltersProps {
  filters: GameFilterValues;
  onChange: (filters: GameFilterValues) => void;
}

const STATUS_OPTIONS: { value: GameStatus | ""; label: string }[] = [
  { value: "", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "discarded", label: "Discarded" },
];

const WINNER_OPTIONS = [
  { value: "", label: "All Winners" },
  { value: "villagers", label: "Villagers" },
  { value: "werewolves", label: "Werewolves" },
];

const PROFILE_OPTIONS: { value: PersuasionProfile; label: string; color: string }[] = [
  { value: "ethos", label: "Ethos", color: "var(--color-ethos)" },
  { value: "pathos", label: "Pathos", color: "var(--color-pathos)" },
  { value: "logos", label: "Logos", color: "var(--color-logos)" },
  { value: "authority_socialproof", label: "Authority", color: "var(--color-authority)" },
  { value: "reciprocity_liking", label: "Reciprocity", color: "var(--color-reciprocity)" },
  { value: "scarcity_commitment", label: "Scarcity", color: "var(--color-scarcity)" },
  { value: "baseline", label: "Baseline", color: "var(--color-baseline)" },
];

export default function GameFilters({ filters, onChange }: GameFiltersProps) {
  const update = (partial: Partial<GameFilterValues>) =>
    onChange({ ...filters, ...partial });

  const toggleProfile = (profile: PersuasionProfile) => {
    const current = filters.profiles;
    const next = current.includes(profile)
      ? current.filter((p) => p !== profile)
      : [...current, profile];
    update({ profiles: next });
  };

  return (
    <div className="glass-card flex flex-wrap items-center gap-4 mb-6">
      {/* Status dropdown */}
      <div className="flex flex-col gap-1">
        <label className="text-2xs uppercase tracking-wide text-text-muted">
          Status
        </label>
        <select
          value={filters.status}
          onChange={(e) =>
            update({ status: e.target.value as GameStatus | "" })
          }
          className="bg-bg-elevated border border-border-default rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-info"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Winner dropdown */}
      <div className="flex flex-col gap-1">
        <label className="text-2xs uppercase tracking-wide text-text-muted">
          Winner
        </label>
        <select
          value={filters.winner}
          onChange={(e) => update({ winner: e.target.value })}
          className="bg-bg-elevated border border-border-default rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-info"
        >
          {WINNER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Profile multiselect */}
      <div className="flex flex-col gap-1">
        <label className="text-2xs uppercase tracking-wide text-text-muted">
          Profiles
        </label>
        <div className="flex flex-wrap gap-1.5">
          {PROFILE_OPTIONS.map((opt) => {
            const active = filters.profiles.includes(opt.value);
            return (
              <button
                key={opt.value}
                onClick={() => toggleProfile(opt.value)}
                className={`
                  px-2 py-1 text-2xs uppercase tracking-wide rounded-full
                  border transition-all duration-fast font-semibold
                  ${
                    active
                      ? "opacity-100"
                      : "opacity-40 hover:opacity-70"
                  }
                `}
                style={{
                  color: opt.color,
                  borderColor: active ? opt.color : "var(--color-border-default)",
                  backgroundColor: active
                    ? `color-mix(in srgb, ${opt.color} 15%, transparent)`
                    : "transparent",
                }}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Degraded toggle */}
      <div className="flex flex-col gap-1">
        <label className="text-2xs uppercase tracking-wide text-text-muted">
          Quality
        </label>
        <button
          onClick={() => update({ degradedOnly: !filters.degradedOnly })}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md border
            transition-all duration-fast
            ${
              filters.degradedOnly
                ? "border-warning text-warning bg-warning/10"
                : "border-border-default text-text-muted hover:text-text-secondary"
            }
          `}
        >
          <span className="text-xs">{"\u26A0"}</span>
          Degraded
        </button>
      </div>
    </div>
  );
}
