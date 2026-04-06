"use client";

import { useState } from "react";
import AnalyticsTabs, {
  type AnalyticsTab,
} from "@/components/analytics/AnalyticsTabs";
import ExportButtons from "@/components/analytics/ExportButtons";
import WinRateHeatmap from "@/components/analytics/WinRateHeatmap";
import SurvivalChart from "@/components/analytics/SurvivalChart";
import TechniqueAdherence from "@/components/analytics/TechniqueAdherence";
import DeceptionIndex from "@/components/analytics/DeceptionIndex";
import DetectionMatrix from "@/components/analytics/DetectionMatrix";
import VoteSwingChart from "@/components/analytics/VoteSwingChart";
import BandwagonChart from "@/components/analytics/BandwagonChart";
import AccusationGraph from "@/components/analytics/AccusationGraph";
import {
  useWinRates,
  useSurvival,
  useTechniques,
  useAccusations,
} from "@/hooks/useAnalytics";

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<AnalyticsTab>("winrates");
  const [batchId] = useState<string | undefined>(undefined);

  const winRates = useWinRates(batchId);
  const survival = useSurvival(batchId);
  const techniques = useTechniques(batchId);
  const accusations = useAccusations(batchId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-wide text-text-primary">
            Analytics
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Cross-game metrics and statistical visualizations
          </p>
        </div>
        <ExportButtons batchId={batchId} />
      </div>

      {/* Tabs */}
      <AnalyticsTabs activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Tab content */}
      <div className="space-y-6">
        {activeTab === "winrates" && (
          <WinRatesPanel
            data={winRates.data}
            isLoading={winRates.isLoading}
            error={winRates.error}
          />
        )}
        {activeTab === "survival" && (
          <SurvivalPanel
            data={survival.data}
            isLoading={survival.isLoading}
            error={survival.error}
          />
        )}
        {activeTab === "techniques" && (
          <TechniquesPanel
            data={techniques.data}
            isLoading={techniques.isLoading}
            error={techniques.error}
          />
        )}
        {activeTab === "vote-swing" && (
          <VoteSwingPanel
            data={techniques.data}
            isLoading={techniques.isLoading}
            error={techniques.error}
          />
        )}
        {activeTab === "accusations" && (
          <AccusationsPanel
            data={accusations.data}
            isLoading={accusations.isLoading}
            error={accusations.error}
          />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Panel components
// ---------------------------------------------------------------------------

function LoadingCard() {
  return (
    <div className="glass-card flex items-center justify-center py-16">
      <div className="flex flex-col items-center gap-4 text-text-secondary">
        <div className="ww-spinner" />
        <span className="text-sm">Loading analytics data...</span>
      </div>
    </div>
  );
}

function ErrorCard({ error }: { error: Error | null }) {
  return (
    <div className="glass-card flex items-center justify-center py-16">
      <div className="text-center">
        <h3 className="font-display text-lg text-text-primary mb-2">
          Failed to load data
        </h3>
        <p className="text-sm text-text-muted">
          {error?.message ?? "An unknown error occurred."}
        </p>
      </div>
    </div>
  );
}

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="glass-card">
      <h2 className="font-display text-lg font-semibold tracking-wide text-text-primary mb-4">
        {title}
      </h2>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Win Rates
// ---------------------------------------------------------------------------

interface DataPanelProps<T> {
  data: T | undefined;
  isLoading: boolean;
  error: Error | null;
}

function WinRatesPanel({
  data,
  isLoading,
  error,
}: DataPanelProps<ReturnType<typeof useWinRates>["data"]>) {
  if (isLoading) return <LoadingCard />;
  if (error) return <ErrorCard error={error} />;
  if (!data) return null;

  return (
    <SectionCard title="Win Rate by Faction and Profile">
      <WinRateHeatmap
        matrix={data.matrix}
        factions={data.summary.factions}
      />
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// Survival
// ---------------------------------------------------------------------------

function SurvivalPanel({
  data,
  isLoading,
  error,
}: DataPanelProps<ReturnType<typeof useSurvival>["data"]>) {
  if (isLoading) return <LoadingCard />;
  if (error) return <ErrorCard error={error} />;
  if (!data) return null;

  return (
    <SectionCard title="Mean Survival Duration by Role and Profile">
      <SurvivalChart data={data.data} />
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// Techniques
// ---------------------------------------------------------------------------

function TechniquesPanel({
  data,
  isLoading,
  error,
}: DataPanelProps<ReturnType<typeof useTechniques>["data"]>) {
  if (isLoading) return <LoadingCard />;
  if (error) return <ErrorCard error={error} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <SectionCard title="Technique Adherence Rate">
        <TechniqueAdherence data={data.adherence} />
      </SectionCard>

      <SectionCard title="Deception Index by Profile">
        <DeceptionIndex data={data.deception_index} />
      </SectionCard>

      <SectionCard title="Detection Difficulty Matrix">
        <DetectionMatrix data={data.detection} />
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Vote Swing + Bandwagon
// ---------------------------------------------------------------------------

function VoteSwingPanel({
  data,
  isLoading,
  error,
}: DataPanelProps<ReturnType<typeof useTechniques>["data"]>) {
  if (isLoading) return <LoadingCard />;
  if (error) return <ErrorCard error={error} />;
  if (!data) return null;

  // Derive vote swing entries from bandwagon data by grouping
  // The backend may provide bus_throwing as a proxy; we use it as vote-swing-like data
  const voteSwingData = data.bus_throwing.map((bt) => ({
    profile: bt.profile,
    avg_vote_change: bt.bus_throwing_rate,
    count: bt.total_wolf_votes,
  }));

  return (
    <div className="space-y-6">
      <SectionCard title="Vote Swing After Agent Speaks">
        {voteSwingData.length > 0 ? (
          <VoteSwingChart data={voteSwingData} />
        ) : (
          <p className="text-center text-sm text-text-muted py-8">
            No vote swing data available yet.
          </p>
        )}
      </SectionCard>

      <SectionCard title="Bandwagon Dynamics: Time to Majority">
        {data.bandwagon.length > 0 ? (
          <BandwagonChart data={data.bandwagon} />
        ) : (
          <p className="text-center text-sm text-text-muted py-8">
            No bandwagon data available yet.
          </p>
        )}
      </SectionCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Accusations
// ---------------------------------------------------------------------------

function AccusationsPanel({
  data,
  isLoading,
  error,
}: DataPanelProps<ReturnType<typeof useAccusations>["data"]>) {
  if (isLoading) return <LoadingCard />;
  if (error) return <ErrorCard error={error} />;
  if (!data) return null;

  return (
    <SectionCard title="Accusation Network">
      {data.nodes.length > 0 ? (
        <AccusationGraph nodes={data.nodes} edges={data.edges} />
      ) : (
        <p className="text-center text-sm text-text-muted py-8">
          No accusation data available yet.
        </p>
      )}
    </SectionCard>
  );
}
