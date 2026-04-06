"use client";

import { ReferenceLine } from "recharts";

interface BaselineOverlayProps {
  /** The y-axis value where the baseline reference line should be drawn */
  value: number;
  /** Optional label text */
  label?: string;
  /** Which y-axis to reference (for dual-axis charts) */
  yAxisId?: string;
}

/**
 * Reusable dashed gray baseline reference line for Recharts charts.
 * Must be used as a child of a Recharts chart component.
 */
export default function BaselineOverlay({
  value,
  label,
  yAxisId,
}: BaselineOverlayProps) {
  return (
    <ReferenceLine
      y={value}
      yAxisId={yAxisId}
      stroke="#7a7a7a"
      strokeDasharray="6 4"
      strokeWidth={1.5}
      strokeOpacity={0.6}
      label={
        label
          ? {
              value: label,
              position: "insideTopRight",
              fill: "#7a7a7a",
              fontSize: 11,
              fontFamily: "Nunito Sans, sans-serif",
            }
          : undefined
      }
    />
  );
}
