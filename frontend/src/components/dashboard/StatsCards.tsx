"use client";

import { useEffect, useRef, useState } from "react";
import type { Game } from "@/types/game";

interface StatCardData {
  label: string;
  value: number;
  format?: "number" | "percent" | "decimal";
  suffix?: string;
}

function useCountUp(end: number, duration: number = 1200) {
  const [current, setCurrent] = useState(0);
  const frameRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);

  useEffect(() => {
    if (end === 0) {
      setCurrent(0);
      return;
    }

    startTimeRef.current = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(eased * end);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      }
    };

    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [end, duration]);

  return current;
}

function StatCard({
  label,
  value,
  format = "number",
  suffix,
}: StatCardData) {
  const animated = useCountUp(value);

  let displayed: string;
  switch (format) {
    case "percent":
      displayed = `${animated.toFixed(1)}%`;
      break;
    case "decimal":
      displayed = animated.toFixed(1);
      break;
    default:
      displayed = Math.round(animated).toLocaleString();
  }

  return (
    <div className="glass-card min-w-[200px] flex-1">
      <div className="font-display text-3xl text-text-primary tracking-tight">
        {displayed}
        {suffix && (
          <span className="text-lg text-text-muted ml-1">{suffix}</span>
        )}
      </div>
      <div className="text-sm text-text-secondary mt-2">{label}</div>
    </div>
  );
}

interface StatsCardsProps {
  games: Game[];
}

export default function StatsCards({ games }: StatsCardsProps) {
  const totalGames = games.length;
  const completed = games.filter((g) => g.status === "completed").length;
  const avgRounds =
    completed > 0
      ? games
          .filter((g) => g.status === "completed")
          .reduce((sum, g) => sum + g.rounds_played, 0) / completed
      : 0;

  const villagerWins = games.filter((g) => g.winner === "villagers").length;
  const werewolfWins = games.filter((g) => g.winner === "werewolves").length;
  const decidedGames = villagerWins + werewolfWins;
  const villagerWinRate =
    decidedGames > 0 ? (villagerWins / decidedGames) * 100 : 0;
  const werewolfWinRate =
    decidedGames > 0 ? (werewolfWins / decidedGames) * 100 : 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      <StatCard label="Total Games" value={totalGames} />
      <StatCard label="Completed" value={completed} />
      <StatCard
        label="Avg Rounds"
        value={avgRounds}
        format="decimal"
      />
      <StatCard
        label="Villager Win Rate"
        value={villagerWinRate}
        format="percent"
      />
      <StatCard
        label="Werewolf Win Rate"
        value={werewolfWinRate}
        format="percent"
      />
    </div>
  );
}
