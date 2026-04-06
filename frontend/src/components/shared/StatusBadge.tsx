type StatusType =
  | "pending"
  | "running"
  | "completed"
  | "discarded"
  | "degraded"
  | "alive"
  | "dead"
  | "mayor";

const STATUS_CONFIG: Record<
  StatusType,
  { label: string; color: string; icon: string }
> = {
  pending: {
    label: "Pending",
    color: "var(--color-text-muted)",
    icon: "\u23F0", // clock
  },
  running: {
    label: "Running",
    color: "var(--color-info)",
    icon: "\u25CF", // filled circle
  },
  completed: {
    label: "Completed",
    color: "var(--color-success)",
    icon: "\u2713", // checkmark
  },
  discarded: {
    label: "Discarded",
    color: "var(--color-warning)",
    icon: "\u2717", // x mark
  },
  degraded: {
    label: "Degraded",
    color: "var(--color-warning)",
    icon: "\u26A0", // warning triangle
  },
  alive: {
    label: "Alive",
    color: "var(--color-alive)",
    icon: "\u2665", // heart
  },
  dead: {
    label: "Dead",
    color: "var(--color-dead)",
    icon: "\u2620", // skull
  },
  mayor: {
    label: "Mayor",
    color: "var(--color-mayor)",
    icon: "\u265B", // crown
  },
};

interface StatusBadgeProps {
  status: StatusType;
  showLabel?: boolean;
}

export default function StatusBadge({
  status,
  showLabel = true,
}: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  if (!config) return null;

  return (
    <span
      className="inline-flex items-center gap-1.5 text-xs font-medium"
      style={{ color: config.color }}
    >
      <span
        className={`text-[0.7em] ${status === "running" ? "animate-pulse" : ""}`}
      >
        {config.icon}
      </span>
      {showLabel && <span>{config.label}</span>}
    </span>
  );
}

export { STATUS_CONFIG };
export type { StatusType };
