"use client";

import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { BandwagonEntry } from "@/types/analytics";
import { RECHARTS_DARK_THEME } from "./profileColors";

interface BandwagonChartProps {
  data: BandwagonEntry[];
}

export default function BandwagonChart({ data }: BandwagonChartProps) {
  const histogram = useMemo(() => {
    if (!data.length) return [];

    const maxTime = Math.max(...data.map((d) => d.time_to_majority));
    const binCount = Math.min(Math.max(Math.ceil(maxTime), 1), 10);

    const bins: { bin: string; count: number; from: number; to: number }[] = [];
    for (let i = 0; i < binCount; i++) {
      bins.push({
        bin: `${i + 1}`,
        count: 0,
        from: i + 1,
        to: i + 1,
      });
    }

    for (const entry of data) {
      const idx = Math.min(Math.floor(entry.time_to_majority) - 1, binCount - 1);
      if (idx >= 0 && idx < bins.length) {
        bins[idx].count++;
      }
    }

    return bins;
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart
        data={histogram}
        margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={RECHARTS_DARK_THEME.gridColor}
          vertical={false}
        />
        <XAxis
          dataKey="bin"
          tick={{ fill: RECHARTS_DARK_THEME.textColor, fontSize: 12 }}
          axisLine={{ stroke: RECHARTS_DARK_THEME.axisColor }}
          tickLine={false}
          label={{
            value: "Debate Turns to Majority",
            position: "insideBottom",
            fill: RECHARTS_DARK_THEME.textColor,
            fontSize: 11,
            dy: 12,
          }}
        />
        <YAxis
          tick={{ fill: RECHARTS_DARK_THEME.textColor, fontSize: 12 }}
          axisLine={{ stroke: RECHARTS_DARK_THEME.axisColor }}
          tickLine={false}
          label={{
            value: "Game Count",
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
          formatter={(value) => [`${value} games`, "Count"]}
          labelFormatter={(label) => `Turn ${label}`}
        />
        <Bar
          dataKey="count"
          fill="#4a6fa5"
          radius={[4, 4, 0, 0]}
          maxBarSize={48}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
