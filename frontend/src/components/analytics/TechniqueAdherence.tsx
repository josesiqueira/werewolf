"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { AdherenceEntry } from "@/types/analytics";
import BaselineOverlay from "./BaselineOverlay";
import {
  getProfileColor,
  getProfileLabel,
  RECHARTS_DARK_THEME,
} from "./profileColors";

interface TechniqueAdherenceProps {
  data: AdherenceEntry[];
}

export default function TechniqueAdherence({ data }: TechniqueAdherenceProps) {
  const baselineEntry = data.find((d) => d.profile === "baseline");
  const baselineValue = baselineEntry?.adherence_rate ?? 0;

  const chartData = data.map((d) => ({
    ...d,
    label: getProfileLabel(d.profile),
    rate_pct: d.adherence_rate * 100,
  }));

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
          dataKey="label"
          tick={{ fill: RECHARTS_DARK_THEME.textColor, fontSize: 12 }}
          axisLine={{ stroke: RECHARTS_DARK_THEME.axisColor }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: RECHARTS_DARK_THEME.textColor, fontSize: 12 }}
          axisLine={{ stroke: RECHARTS_DARK_THEME.axisColor }}
          tickLine={false}
          domain={[0, 100]}
          label={{
            value: "Adherence Rate (%)",
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
          formatter={(value) => [`${Number(value).toFixed(1)}%`, "Adherence"]}
        />
        {baselineValue > 0 && (
          <BaselineOverlay
            value={baselineValue * 100}
            label="Baseline"
          />
        )}
        <Bar dataKey="rate_pct" radius={[4, 4, 0, 0]} maxBarSize={48}>
          {chartData.map((entry, index) => (
            <Cell key={index} fill={getProfileColor(entry.profile)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
