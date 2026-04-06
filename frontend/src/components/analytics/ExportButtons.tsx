"use client";

import { getExportUrl } from "@/lib/api";

interface ExportButtonsProps {
  batchId?: string;
}

const FORMATS: { key: "csv" | "json" | "ndjson"; label: string; icon: string }[] = [
  { key: "csv", label: "CSV", icon: "table" },
  { key: "json", label: "JSON", icon: "braces" },
  { key: "ndjson", label: "NDJSON", icon: "rows" },
];

export default function ExportButtons({ batchId }: ExportButtonsProps) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs font-semibold uppercase tracking-wide text-text-muted">
        Export
      </span>
      {FORMATS.map(({ key, label }) => (
        <a
          key={key}
          href={getExportUrl(key, batchId)}
          download
          className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold uppercase tracking-wide transition-all duration-fast glass hover:text-text-primary text-text-secondary"
          style={{
            border: "1px solid var(--color-border-subtle)",
          }}
        >
          <DownloadIcon />
          {label}
        </a>
      ))}
    </div>
  );
}

function DownloadIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}
