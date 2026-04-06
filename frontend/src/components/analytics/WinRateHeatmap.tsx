"use client";

import { useMemo } from "react";
import type { WinRateEntry } from "@/types/analytics";
import {
  ALL_PROFILES,
  getProfileColor,
  getProfileLabel,
} from "./profileColors";

interface WinRateHeatmapProps {
  matrix: WinRateEntry[];
  factions: string[];
}

function rateToOpacity(rate: number): number {
  // Map 0..1 win rate to 0.15..0.95 opacity for visual contrast
  return 0.15 + rate * 0.8;
}

function rateToTextColor(rate: number): string {
  return rate > 0.55 ? "#0c0c14" : "#e2dfd8";
}

export default function WinRateHeatmap({ matrix, factions }: WinRateHeatmapProps) {
  const lookup = useMemo(() => {
    const map = new Map<string, WinRateEntry>();
    for (const entry of matrix) {
      map.set(`${entry.faction}::${entry.profile}`, entry);
    }
    return map;
  }, [matrix]);

  const profiles = ALL_PROFILES.filter((p) =>
    matrix.some((e) => e.profile === p),
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="p-3 text-left text-xs font-semibold uppercase tracking-wide text-text-muted font-display">
              Faction
            </th>
            {profiles.map((profile) => (
              <th
                key={profile}
                className="p-3 text-center text-xs font-semibold uppercase tracking-wide"
                style={{ color: getProfileColor(profile) }}
              >
                {getProfileLabel(profile)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {factions.map((faction) => (
            <tr key={faction}>
              <td className="p-3 text-sm font-semibold capitalize text-text-secondary font-display whitespace-nowrap">
                {faction}
              </td>
              {profiles.map((profile) => {
                const entry = lookup.get(`${faction}::${profile}`);
                const rate = entry?.rate ?? 0;
                const color = getProfileColor(profile);
                return (
                  <td key={profile} className="p-1">
                    <div
                      className="relative flex flex-col items-center justify-center rounded-md p-3 transition-all duration-fast"
                      style={{
                        backgroundColor: color,
                        opacity: rateToOpacity(rate),
                      }}
                      title={
                        entry
                          ? `${(rate * 100).toFixed(1)}% (${entry.wins}/${entry.count}) CI: [${(entry.ci_lower * 100).toFixed(1)}%, ${(entry.ci_upper * 100).toFixed(1)}%]`
                          : "No data"
                      }
                    >
                      <span
                        className="text-lg font-bold tabular-nums"
                        style={{ color: rateToTextColor(rate) }}
                      >
                        {entry ? `${(rate * 100).toFixed(0)}%` : "--"}
                      </span>
                      {entry && (
                        <span
                          className="text-2xs tabular-nums"
                          style={{
                            color: rateToTextColor(rate),
                            opacity: 0.7,
                          }}
                        >
                          n={entry.count}
                        </span>
                      )}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
