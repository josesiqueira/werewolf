"use client";

import { useBatches, useBatchStatus } from "@/hooks/useBatch";
import StatusBadge from "@/components/shared/StatusBadge";

export default function BatchStatus() {
  const { data: batches } = useBatches();

  // Find the most recent running batch, or the most recent completed one
  const activeBatch = batches?.find((b) => b.status === "running");
  const latestBatch = activeBatch ?? batches?.[0];

  if (!latestBatch) {
    return null;
  }

  return <BatchCard batchId={latestBatch.id} />;
}

function BatchCard({ batchId }: { batchId: string }) {
  const { data: progress, isLoading } = useBatchStatus(batchId);

  if (isLoading || !progress) {
    return (
      <div className="glass-card">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-info border-t-transparent rounded-full animate-spin" />
          <span className="text-text-muted text-sm">Loading batch status...</span>
        </div>
      </div>
    );
  }

  const isRunning = progress.status === "running";
  const pct = progress.completion_pct;

  return (
    <div className="glass-card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-lg tracking-wide">Batch Run</h3>
        <StatusBadge
          status={
            progress.status === "running"
              ? "running"
              : progress.status === "completed"
                ? "completed"
                : "pending"
          }
        />
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 bg-bg-elevated rounded-full overflow-hidden mb-3">
        <div
          className="h-full rounded-full transition-all duration-slow"
          style={{
            width: `${pct}%`,
            background: isRunning
              ? "linear-gradient(90deg, var(--color-info), var(--color-ethos-light))"
              : "var(--color-success)",
          }}
        />
      </div>

      {/* Stats row */}
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <div>
          <span className="text-text-muted">Progress: </span>
          <span className="text-text-primary font-medium">
            {progress.completed_games}/{progress.total_games}
          </span>
          <span className="text-text-muted ml-1">({pct.toFixed(1)}%)</span>
        </div>

        {isRunning && progress.eta_seconds > 0 && (
          <div>
            <span className="text-text-muted">ETA: </span>
            <span className="text-text-primary font-medium">
              {formatEta(progress.eta_seconds)}
            </span>
          </div>
        )}

        {progress.games_per_minute > 0 && (
          <div>
            <span className="text-text-muted">Rate: </span>
            <span className="text-text-primary font-medium">
              {progress.games_per_minute.toFixed(1)} games/min
            </span>
          </div>
        )}

        {progress.failed_games > 0 && (
          <div>
            <span className="text-error">
              {progress.failed_games} failed
            </span>
          </div>
        )}

        {progress.degraded_count > 0 && (
          <div>
            <span className="text-warning">
              {progress.degraded_count} degraded
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function formatEta(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (mins < 60) return `${mins}m ${secs}s`;
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  return `${hrs}h ${remMins}m`;
}
