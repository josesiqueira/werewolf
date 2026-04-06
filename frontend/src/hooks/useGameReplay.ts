'use client';

import { useEffect, useCallback, useRef } from 'react';
import { useReplayStore, type GamePhase } from '@/stores/replayStore';
import type { Game } from '@/types/game';
import type { Player } from '@/types/player';
import type { Turn } from '@/types/turn';

/** Ordered phases within a single round */
const PHASE_ORDER: GamePhase[] = [
  'NIGHT',
  'DAY_BID',
  'DAY_SPEECH',
  'VOTE',
];

/** First-round phases include mayor election */
const FIRST_ROUND_PHASES: GamePhase[] = [
  'MAYOR_CAMPAIGN',
  'MAYOR_VOTE',
  'NIGHT',
  'DAY_BID',
  'DAY_SPEECH',
  'VOTE',
];

export interface GameReplayData {
  game: Game | null;
  players: Player[];
  turns: Turn[];
  isLoading: boolean;
  error: string | null;
}

interface UseGameReplayReturn extends GameReplayData {
  /** Turns filtered to the current round and phase */
  currentTurns: Turn[];
  /** The turn currently being displayed */
  activeTurn: Turn | null;
  /** All turns up to and including the current position */
  visibleTurns: Turn[];
  /** Advance to the next phase / round */
  advancePhase: () => void;
  /** Go back to the previous phase / round */
  retreatPhase: () => void;
  /** Total number of rounds in the game */
  totalRounds: number;
}

/**
 * Hook to fetch game data and manage replay state.
 * Accepts pre-fetched data or defaults to empty state.
 */
export function useGameReplay(
  gameData?: { game: Game; players: Player[]; turns: Turn[] }
): UseGameReplayReturn {
  const store = useReplayStore();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const game = gameData?.game ?? null;
  const players = gameData?.players ?? game?.players ?? [];
  const turns = gameData?.turns ?? [];
  const isLoading = !gameData;
  const error = null;

  // Derive total rounds
  const totalRounds = turns.length > 0
    ? Math.max(...turns.map((t) => t.round_number))
    : 0;

  // Filter turns for the current round + phase
  const currentTurns = turns.filter(
    (t) =>
      t.round_number === store.currentRound &&
      t.phase === store.currentPhase
  );

  // The currently active turn
  const activeTurn = currentTurns[store.currentTurnIndex] ?? null;

  // All turns visible up to current position (for chat log)
  const visibleTurns = turns.filter((t) => {
    if (t.round_number < store.currentRound) return true;
    if (t.round_number > store.currentRound) return false;
    const phases =
      store.currentRound === 1 ? FIRST_ROUND_PHASES : PHASE_ORDER;
    const currentPhaseIdx = phases.indexOf(store.currentPhase);
    const turnPhaseIdx = phases.indexOf(t.phase as GamePhase);
    if (turnPhaseIdx < currentPhaseIdx) return true;
    if (turnPhaseIdx > currentPhaseIdx) return false;
    const turnsInPhase = turns.filter(
      (tt) =>
        tt.round_number === t.round_number && tt.phase === t.phase
    );
    const turnIdx = turnsInPhase.indexOf(t);
    return turnIdx <= store.currentTurnIndex;
  });

  // Advance phase logic
  const advancePhase = useCallback(() => {
    const phases =
      store.currentRound === 1 ? FIRST_ROUND_PHASES : PHASE_ORDER;
    const currentIdx = phases.indexOf(store.currentPhase);

    const turnsInPhase = turns.filter(
      (t) =>
        t.round_number === store.currentRound &&
        t.phase === store.currentPhase
    );
    if (store.currentTurnIndex < turnsInPhase.length - 1) {
      store.setTurnIndex(store.currentTurnIndex + 1);
      return;
    }

    if (currentIdx < phases.length - 1) {
      store.setPhase(phases[currentIdx + 1]);
      store.setTurnIndex(0);
      return;
    }

    if (store.currentRound < totalRounds) {
      store.setRound(store.currentRound + 1);
      store.setPhase(PHASE_ORDER[0]);
      store.setTurnIndex(0);
      return;
    }

    store.setPhase('GAME_OVER');
    store.pause();
  }, [store, turns, totalRounds]);

  const retreatPhase = useCallback(() => {
    if (store.currentTurnIndex > 0) {
      store.setTurnIndex(store.currentTurnIndex - 1);
      return;
    }

    const phases =
      store.currentRound === 1 ? FIRST_ROUND_PHASES : PHASE_ORDER;
    const currentIdx = phases.indexOf(store.currentPhase);

    if (currentIdx > 0) {
      const prevPhase = phases[currentIdx - 1];
      const turnsInPrev = turns.filter(
        (t) =>
          t.round_number === store.currentRound && t.phase === prevPhase
      );
      store.setPhase(prevPhase);
      store.setTurnIndex(Math.max(0, turnsInPrev.length - 1));
      return;
    }

    if (store.currentRound > 1) {
      const prevRound = store.currentRound - 1;
      const prevPhases = prevRound === 1 ? FIRST_ROUND_PHASES : PHASE_ORDER;
      const lastPhase = prevPhases[prevPhases.length - 1];
      const turnsInLast = turns.filter(
        (t) => t.round_number === prevRound && t.phase === lastPhase
      );
      store.setRound(prevRound);
      store.setPhase(lastPhase);
      store.setTurnIndex(Math.max(0, turnsInLast.length - 1));
    }
  }, [store, turns]);

  // Auto-play interval
  useEffect(() => {
    if (store.isPlaying) {
      intervalRef.current = setInterval(() => {
        advancePhase();
      }, 2000 / store.playbackSpeed);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [store.isPlaying, store.playbackSpeed, advancePhase]);

  return {
    game,
    players,
    turns,
    isLoading,
    error,
    currentTurns,
    activeTurn,
    visibleTurns,
    advancePhase,
    retreatPhase,
    totalRounds,
  };
}
