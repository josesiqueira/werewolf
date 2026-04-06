"use client";

import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { SurvivalEntry } from "@/types/analytics";
import type { PersuasionProfile } from "@/types/player";
import {
  ALL_PROFILES,
  getProfileColor,
  getProfileLabel,
  RECHARTS_DARK_THEME,
} from "./profileColors";

interface SurvivalChartProps {
  data: SurvivalEntry[];
}

export default function SurvivalChart({ data }: SurvivalChartProps) {
  const { chartData, profiles } = useMemo(() => {
    const roles = Array.from(new Set(data.map((d) => d.role)));
    const profileSet = new Set(data.map((d) => d.profile));
    const activeProfiles = ALL_PROFILES.filter((p) => profileSet.has(p));

    const rows = roles.map((role) => {
      const row: Record<string, string | number> = { role };
      for (const profile of activeProfiles) {
        const entry = data.find(
          (d) => d.role === role && d.profile === profile,
        );
        row[profile] = entry?.mean_rounds ?? 0;
      }
      return row;
    });

    return { chartData: rows, profiles: activeProfiles };
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart
        data={chartData}
        margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={RECHARTS_DARK_THEME.gridColor}
          vertical={false}
        />
        <XAxis
          dataKey="role"
          tick={{ fill: RECHARTS_DARK_THEME.textColor, fontSize: 12 }}
          axisLine={{ stroke: RECHARTS_DARK_THEME.axisColor }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: RECHARTS_DARK_THEME.textColor, fontSize: 12 }}
          axisLine={{ stroke: RECHARTS_DARK_THEME.axisColor }}
          tickLine={false}
          label={{
            value: "Mean Survival (rounds)",
            angle: -90,
            position: "insideLeft",
            fill: RECHARTS_DARK_THEME.textColor,
            fontSize: 11,
            dx: -4,
          }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: RECHARTS_DARK_THEME.tooltipBg,
            border: `1px solid ${RECHARTS_DARK_THEME.tooltipBorder}`,
            borderRadius: 8,
            color: "#e2dfd8",
            fontSize: 13,
          }}
          cursor={{ fill: "rgba(255,255,255,0.03)" }}
        />
        <Legend
          wrapperStyle={{ fontSize: 12, color: RECHARTS_DARK_THEME.textColor }}
          formatter={(value: string) =>
            getProfileLabel(value as PersuasionProfile)
          }
        />
        {profiles.map((profile) => (
          <Bar
            key={profile}
            dataKey={profile}
            name={profile}
            fill={getProfileColor(profile)}
            radius={[4, 4, 0, 0]}
            maxBarSize={28}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
