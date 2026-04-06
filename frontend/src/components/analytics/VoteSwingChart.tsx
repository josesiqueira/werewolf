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
  ReferenceLine,
} from "recharts";
import type { VoteSwingEntry } from "@/types/analytics";
import {
  getProfileColor,
  getProfileLabel,
  RECHARTS_DARK_THEME,
} from "./profileColors";

interface VoteSwingChartProps {
  data: VoteSwingEntry[];
}

export default function VoteSwingChart({ data }: VoteSwingChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    label: getProfileLabel(d.profile),
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
          label={{
            value: "Avg Vote Change",
            angle: -90,
            position: "insideLeft",
            fill: RECHARTS_DARK_THEME.textColor,
            fontSize: 11,
            dx: -4,
          }}
        />
        <ReferenceLine
          y={0}
          stroke="#7a7a7a"
          strokeDasharray="6 4"
          strokeWidth={1.5}
          strokeOpacity={0.6}
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
          formatter={(value) => [Number(value).toFixed(2), "Avg Vote Change"]}
        />
        <Bar dataKey="avg_vote_change" radius={[4, 4, 0, 0]} maxBarSize={48}>
          {chartData.map((entry, index) => (
            <Cell key={index} fill={getProfileColor(entry.profile)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
