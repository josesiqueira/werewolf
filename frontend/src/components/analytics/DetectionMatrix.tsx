"use client";

import { useMemo } from "react";
import type { DetectionEntry } from "@/types/analytics";

interface DetectionMatrixProps {
  data: DetectionEntry[];
}

function rateToColor(rate: number): string {
  // Gradient from deep blue (low suspicion) to red (high suspicion)
  if (rate < 0.2) return "rgba(59, 105, 152, 0.7)";
  if (rate < 0.4) return "rgba(74, 138, 110, 0.7)";
  if (rate < 0.6) return "rgba(184, 160, 54, 0.7)";
  if (rate < 0.8) return "rgba(212, 122, 42, 0.7)";
  return "rgba(201, 48, 48, 0.7)";
}

function rateToTextColor(rate: number): string {
  return rate > 0.6 ? "#0c0c14" : "#e2dfd8";
}

export default function DetectionMatrix({ data }: DetectionMatrixProps) {
  const { techniques, deceptionTypes, lookup } = useMemo(() => {
    const techs = Array.from(new Set(data.map((d) => d.technique)));
    const types = Array.from(new Set(data.map((d) => d.deception_type)));
    const map = new Map<string, DetectionEntry>();
    for (const entry of data) {
      map.set(`${entry.technique}::${entry.deception_type}`, entry);
    }
    return { techniques: techs, deceptionTypes: types, lookup: map };
  }, [data]);

  if (!techniques.length || !deceptionTypes.length) {
    return (
      <p className="text-center text-sm text-text-muted py-8">
        Not enough data to build detection matrix.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="p-3 text-left text-xs font-semibold uppercase tracking-wide text-text-muted font-display">
              Technique
            </th>
            {deceptionTypes.map((dt) => (
              <th
                key={dt}
                className="p-3 text-center text-xs font-semibold uppercase tracking-wide text-text-muted"
              >
                {dt}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {techniques.map((technique) => (
            <tr key={technique}>
              <td className="p-3 text-sm font-semibold capitalize text-text-secondary font-display whitespace-nowrap">
                {technique.replace(/_/g, " ")}
              </td>
              {deceptionTypes.map((dt) => {
                const entry = lookup.get(`${technique}::${dt}`);
                const rate = entry?.suspicion_rate ?? 0;
                return (
                  <td key={dt} className="p-1">
                    <div
                      className="flex flex-col items-center justify-center rounded-md p-3 transition-all duration-fast"
                      style={{ backgroundColor: rateToColor(rate) }}
                      title={
                        entry
                          ? `Suspicion rate: ${(rate * 100).toFixed(1)}% (n=${entry.count})`
                          : "No data"
                      }
                    >
                      <span
                        className="text-sm font-bold tabular-nums"
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
