"use client";

export type AnalyticsTab =
  | "winrates"
  | "survival"
  | "techniques"
  | "accusations"
  | "vote-swing";

interface AnalyticsTabsProps {
  activeTab: AnalyticsTab;
  onTabChange: (tab: AnalyticsTab) => void;
}

const TABS: { key: AnalyticsTab; label: string }[] = [
  { key: "winrates", label: "Win Rates" },
  { key: "survival", label: "Survival" },
  { key: "techniques", label: "Techniques" },
  { key: "vote-swing", label: "Vote Swing" },
  { key: "accusations", label: "Accusations" },
];

export default function AnalyticsTabs({
  activeTab,
  onTabChange,
}: AnalyticsTabsProps) {
  return (
    <nav className="flex items-center gap-1 rounded-lg p-1 glass" role="tablist">
      {TABS.map(({ key, label }) => {
        const isActive = activeTab === key;
        return (
          <button
            key={key}
            role="tab"
            aria-selected={isActive}
            onClick={() => onTabChange(key)}
            className={`
              relative rounded-md px-4 py-2 text-sm font-semibold tracking-wide
              transition-all duration-fast whitespace-nowrap
              ${
                isActive
                  ? "bg-bg-elevated text-text-primary shadow-sm"
                  : "text-text-muted hover:text-text-secondary hover:bg-bg-surface/50"
              }
            `}
          >
            {label}
          </button>
        );
      })}
    </nav>
  );
}
