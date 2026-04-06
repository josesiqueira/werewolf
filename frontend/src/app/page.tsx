"use client";

import Link from "next/link";
import { useGames } from "@/hooks/useGames";
import StatsCards from "@/components/dashboard/StatsCards";
import RecentGames from "@/components/dashboard/RecentGames";
import BatchStatus from "@/components/dashboard/BatchStatus";

export default function DashboardPage() {
  const { data: games, isLoading, isError } = useGames();

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display text-4xl tracking-wide text-text-primary">
          Werewolf AI Agents
        </h1>
        <p className="text-text-secondary mt-2">
          Research observation dashboard for AI social deduction experiments.
        </p>
      </div>

      {/* Stats Cards */}
      <section className="mb-8">
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="glass-card min-w-[200px] animate-pulse">
                <div className="h-8 w-24 bg-bg-elevated rounded mb-2" />
                <div className="h-4 w-32 bg-bg-elevated rounded" />
              </div>
            ))}
          </div>
        ) : isError ? (
          <div className="glass-card text-center py-8">
            <p className="text-error">
              Failed to load statistics. Is the backend running?
            </p>
          </div>
        ) : (
          <StatsCards games={games ?? []} />
        )}
      </section>

      {/* Batch Status */}
      <section className="mb-8">
        <BatchStatus />
      </section>

      {/* Two-column layout: Recent Games + Quick Links */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Games */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-xl tracking-wide">
              Recent Games
            </h2>
            <Link
              href="/games"
              className="text-sm text-info hover:underline"
            >
              View all
            </Link>
          </div>

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="glass-card animate-pulse h-20" />
              ))}
            </div>
          ) : (
            <RecentGames games={games ?? []} />
          )}
        </div>

        {/* Quick Links */}
        <div>
          <h2 className="font-display text-xl tracking-wide mb-4">
            Quick Links
          </h2>
          <div className="space-y-3">
            <QuickLinkCard
              href="/games"
              title="Game Browser"
              description="Browse, filter, and inspect all game records"
              icon={"\uD83C\uDFAE"}
            />
            <QuickLinkCard
              href="/analytics"
              title="Analytics"
              description="Win rates, technique effectiveness, and more"
              icon={"\uD83D\uDCC8"}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function QuickLinkCard({
  href,
  title,
  description,
  icon,
}: {
  href: string;
  title: string;
  description: string;
  icon: string;
}) {
  return (
    <Link
      href={href}
      className="glass-card block hover:bg-white/[0.04] transition-colors duration-fast group"
      style={{ padding: "var(--space-4)" }}
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <h3 className="font-medium text-text-primary group-hover:text-info transition-colors">
            {title}
          </h3>
          <p className="text-sm text-text-muted mt-0.5">{description}</p>
        </div>
      </div>
    </Link>
  );
}
