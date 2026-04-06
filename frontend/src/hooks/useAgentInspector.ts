'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';

// Types assumed from Agent A's work
interface Turn {
  id: string;
  game_id: string;
  player_id: string;
  round_number: number;
  phase: string;
  private_reasoning: string;
  public_statement: string;
  vote_target: string | null;
  bid_level: number;
  technique_self_label: string;
  deception_self_label: string;
  confidence: number;
}

interface Player {
  id: string;
  game_id: string;
  agent_name: string;
  role: string;
  persona: string;
  persuasion_profile: string;
  is_mayor: boolean;
  eliminated_round: number | null;
  survived: boolean;
  character_image: string;
}

interface AgentInspectorState {
  player: Player | null;
  turns: Turn[];
  currentTurnIndex: number;
  currentTurn: Turn | null;
  isLoading: boolean;
  error: string | null;
  isPrivateRevealed: boolean;
}

interface AgentInspectorActions {
  goToNextTurn: () => void;
  goToPrevTurn: () => void;
  goToTurn: (index: number) => void;
  togglePrivateReveal: () => void;
  setPrivateRevealed: (revealed: boolean) => void;
}

export type UseAgentInspectorReturn = AgentInspectorState & AgentInspectorActions;

export function useAgentInspector(
  gameId: string,
  agentId: string
): UseAgentInspectorReturn {
  const [player, setPlayer] = useState<Player | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [currentTurnIndex, setCurrentTurnIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPrivateRevealed, setIsPrivateRevealed] = useState(false);

  // Fetch player data and their turns
  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setIsLoading(true);
      setError(null);

      try {
        // Attempt to use the API client from Agent A
        // Falls back to direct fetch if not available
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

        const [playerRes, turnsRes] = await Promise.all([
          fetch(`${apiBase}/api/games/${gameId}`),
          fetch(`${apiBase}/api/games/${gameId}/turns`),
        ]);

        if (!playerRes.ok || !turnsRes.ok) {
          throw new Error('Failed to fetch agent data');
        }

        const gameData = await playerRes.json();
        const allTurns: Turn[] = await turnsRes.json();

        if (cancelled) return;

        // Find the specific player
        const foundPlayer = gameData.players?.find(
          (p: Player) => p.id === agentId
        );

        if (!foundPlayer) {
          throw new Error(`Agent ${agentId} not found in game ${gameId}`);
        }

        // Filter turns for this agent, sorted by round then phase
        const phaseOrder: Record<string, number> = {
          MAYOR_CAMPAIGN: 0,
          MAYOR_VOTE: 1,
          NIGHT: 2,
          DAY_BID: 3,
          DAY_SPEECH: 4,
          VOTE: 5,
        };

        const agentTurns = allTurns
          .filter((t) => t.player_id === agentId)
          .sort((a, b) => {
            if (a.round_number !== b.round_number) {
              return a.round_number - b.round_number;
            }
            return (phaseOrder[a.phase] ?? 99) - (phaseOrder[b.phase] ?? 99);
          });

        setPlayer(foundPlayer);
        setTurns(agentTurns);
        setCurrentTurnIndex(0);
        setIsPrivateRevealed(false);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'An unknown error occurred'
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [gameId, agentId]);

  const currentTurn = useMemo(() => {
    return turns[currentTurnIndex] ?? null;
  }, [turns, currentTurnIndex]);

  const goToNextTurn = useCallback(() => {
    setCurrentTurnIndex((prev) => Math.min(prev + 1, turns.length - 1));
    setIsPrivateRevealed(false);
  }, [turns.length]);

  const goToPrevTurn = useCallback(() => {
    setCurrentTurnIndex((prev) => Math.max(prev - 1, 0));
    setIsPrivateRevealed(false);
  }, []);

  const goToTurn = useCallback(
    (index: number) => {
      if (index >= 0 && index < turns.length) {
        setCurrentTurnIndex(index);
        setIsPrivateRevealed(false);
      }
    },
    [turns.length]
  );

  const togglePrivateReveal = useCallback(() => {
    setIsPrivateRevealed((prev) => !prev);
  }, []);

  const setPrivateRevealedFn = useCallback((revealed: boolean) => {
    setIsPrivateRevealed(revealed);
  }, []);

  return {
    player,
    turns,
    currentTurnIndex,
    currentTurn,
    isLoading,
    error,
    isPrivateRevealed,
    goToNextTurn,
    goToPrevTurn,
    goToTurn,
    togglePrivateReveal,
    setPrivateRevealed: setPrivateRevealedFn,
  };
}
