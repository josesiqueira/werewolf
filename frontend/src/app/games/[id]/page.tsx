'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams } from 'next/navigation';
import PlayerCircle from '@/components/replay/PlayerCircle';
import ChatLog from '@/components/replay/ChatLog';
import VotingViz from '@/components/replay/VotingViz';
import BiddingBar from '@/components/replay/BiddingBar';
import DayNightBackground from '@/components/replay/DayNightBackground';
import { useReplayStore, type GamePhase } from '@/stores/replayStore';
import type { Game } from '@/types/game';
import type { Player } from '@/types/player';
import type { Turn } from '@/types/turn';

/**
 * Phase display labels and icons
 */
const PHASE_DISPLAY: Record<string, { label: string; icon: string }> = {
  MAYOR_CAMPAIGN: { label: 'Mayor Campaign', icon: '📜' },
  MAYOR_VOTE: { label: 'Mayor Vote', icon: '🗳️' },
  NIGHT: { label: 'Night', icon: '🌙' },
  DAY_BID: { label: 'Bidding', icon: '⚡' },
  DAY_SPEECH: { label: 'Debate', icon: '💬' },
  VOTE: { label: 'Village Vote', icon: '🗳️' },
  GAME_OVER: { label: 'Game Over', icon: '⚰️' },
};

const NIGHT_PHASES = new Set(['NIGHT']);

/**
 * Ordered phases for navigation
 */
const ALL_PHASES: GamePhase[] = [
  'MAYOR_CAMPAIGN',
  'MAYOR_VOTE',
  'NIGHT',
  'DAY_BID',
  'DAY_SPEECH',
  'VOTE',
];

export default function GameReplayPage() {
  const params = useParams();
  const gameId = params.id as string;

  const store = useReplayStore();

  const [game, setGame] = useState<Game | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Players come embedded in Game
  const players: Player[] = game?.players ?? [];

  // Fetch game data from API
  useEffect(() => {
    const fetchGameData = async () => {
      try {
        setIsLoading(true);
        const { fetchGame, fetchGameTurns } = await import('@/lib/api');
        const [gameData, turnsData] = await Promise.all([
          fetchGame(gameId),
          fetchGameTurns(gameId),
        ]);
        setGame(gameData);
        setTurns(turnsData);
        setError(null);
      } catch {
        setError('Game data could not be loaded. The API may not be running.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchGameData();
    store.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gameId]);

  // Compute alive players at current replay position.
  // A player is dead if their eliminated_round is before the current round.
  const alivePlayers = useMemo(() => {
    const alive = new Set(players.map((p) => p.id));
    players.forEach((p) => {
      if (
        p.eliminated_round !== null &&
        p.eliminated_round < store.currentRound
      ) {
        alive.delete(p.id);
      }
      // If eliminated in the current round and we are past the VOTE phase
      if (
        p.eliminated_round === store.currentRound &&
        ALL_PHASES.indexOf(store.currentPhase) > ALL_PHASES.indexOf('VOTE')
      ) {
        alive.delete(p.id);
      }
    });
    return alive;
  }, [players, store.currentRound, store.currentPhase]);

  // Current turns for this round + phase
  const currentTurns = useMemo(
    () =>
      turns.filter(
        (t) =>
          t.round_number === store.currentRound &&
          t.phase === store.currentPhase
      ),
    [turns, store.currentRound, store.currentPhase]
  );

  const activeTurn = currentTurns[store.currentTurnIndex] ?? null;
  const speakerId = activeTurn?.player_id ?? null;

  // Mayor ID -- find the player flagged as mayor
  const mayorId = useMemo(() => {
    const mayor = players.find((p) => p.is_mayor);
    return mayor?.id ?? null;
  }, [players]);

  // Visible turns for chat log (all turns up to current position)
  const visibleTurns = useMemo(() => {
    return turns.filter((t) => {
      if (t.round_number < store.currentRound) return true;
      if (t.round_number > store.currentRound) return false;
      const tPhaseIdx = ALL_PHASES.indexOf(t.phase as GamePhase);
      const curPhaseIdx = ALL_PHASES.indexOf(store.currentPhase);
      if (tPhaseIdx < curPhaseIdx) return true;
      if (tPhaseIdx > curPhaseIdx) return false;
      // Same phase: show up to currentTurnIndex
      const samePhase = turns.filter(
        (tt) => tt.round_number === t.round_number && tt.phase === t.phase
      );
      return samePhase.indexOf(t) <= store.currentTurnIndex;
    });
  }, [turns, store.currentRound, store.currentPhase, store.currentTurnIndex]);

  // Voting data for VotingViz (from turns in the current VOTE phase)
  const votingData = useMemo(() => {
    if (store.currentPhase !== 'VOTE') return [];
    return currentTurns
      .filter((t) => t.vote_target)
      .map((t) => ({ voterId: t.player_id, targetId: t.vote_target! }));
  }, [store.currentPhase, currentTurns]);

  // Find eliminated player for the current round's vote
  const eliminatedInCurrentVote = useMemo(() => {
    if (store.currentPhase !== 'VOTE') return null;
    // The player eliminated in this round
    const eliminated = players.find(
      (p) => p.eliminated_round === store.currentRound
    );
    return eliminated?.id ?? null;
  }, [store.currentPhase, store.currentRound, players]);

  // Total rounds
  const totalRounds = useMemo(
    () =>
      turns.length > 0
        ? Math.max(...turns.map((t) => t.round_number))
        : 0,
    [turns]
  );

  // Phase navigation
  const advancePhase = useCallback(() => {
    if (store.currentTurnIndex < currentTurns.length - 1) {
      store.setTurnIndex(store.currentTurnIndex + 1);
      return;
    }
    const curIdx = ALL_PHASES.indexOf(store.currentPhase);
    if (curIdx < ALL_PHASES.length - 1) {
      store.setPhase(ALL_PHASES[curIdx + 1]);
      store.setTurnIndex(0);
      return;
    }
    if (store.currentRound < totalRounds) {
      store.setRound(store.currentRound + 1);
      store.setPhase('NIGHT');
      store.setTurnIndex(0);
      return;
    }
    store.setPhase('GAME_OVER');
    store.pause();
  }, [store, currentTurns, totalRounds]);

  const retreatPhase = useCallback(() => {
    if (store.currentTurnIndex > 0) {
      store.setTurnIndex(store.currentTurnIndex - 1);
      return;
    }
    const curIdx = ALL_PHASES.indexOf(store.currentPhase);
    if (curIdx > 0) {
      store.setPhase(ALL_PHASES[curIdx - 1]);
      store.setTurnIndex(0);
      return;
    }
    if (store.currentRound > 1) {
      store.setRound(store.currentRound - 1);
      store.setPhase(ALL_PHASES[ALL_PHASES.length - 1]);
      store.setTurnIndex(0);
    }
  }, [store]);

  // Auto-play
  useEffect(() => {
    if (!store.isPlaying) return;
    const interval = setInterval(() => {
      advancePhase();
    }, 2000 / store.playbackSpeed);
    return () => clearInterval(interval);
  }, [store.isPlaying, store.playbackSpeed, advancePhase]);

  const isNight = NIGHT_PHASES.has(store.currentPhase);
  const phaseDisplay = PHASE_DISPLAY[store.currentPhase] ?? {
    label: store.currentPhase,
    icon: '📌',
  };

  // Loading state
  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center min-h-screen"
        style={{ background: 'var(--color-bg-primary)' }}
      >
        <div className="text-center space-y-4">
          <div
            className="w-8 h-8 border-2 rounded-full animate-spin mx-auto"
            style={{
              borderColor: 'var(--color-border-subtle)',
              borderTopColor: 'var(--color-text-primary)',
            }}
          />
          <p style={{ color: 'var(--color-text-secondary)' }}>
            Loading game replay...
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        className="flex items-center justify-center min-h-screen"
        style={{ background: 'var(--color-bg-primary)' }}
      >
        <div
          className="text-center space-y-4 max-w-md p-8 rounded-xl"
          style={{
            background: 'var(--glass-bg)',
            border: '1px solid var(--color-border-subtle)',
          }}
        >
          <p
            className="text-lg font-semibold"
            style={{ color: 'var(--color-error)' }}
          >
            Could not load game
          </p>
          <p
            className="text-sm"
            style={{ color: 'var(--color-text-muted)' }}
          >
            {error}
          </p>
          <p
            className="text-xs"
            style={{ color: 'var(--color-text-muted)' }}
          >
            Game ID: {gameId}
          </p>
        </div>
      </div>
    );
  }

  return (
    <DayNightBackground isNight={isNight}>
      <div className="min-h-screen flex flex-col">
        {/* Top bar: Game info + Phase indicator */}
        <header
          className="flex-shrink-0 flex items-center justify-between px-6 py-4"
          style={{
            borderBottom: '1px solid var(--color-border-subtle)',
            background: 'var(--color-bg-overlay)',
            backdropFilter: 'blur(12px)',
          }}
        >
          <div className="flex items-center gap-4">
            <h1
              className="text-lg font-bold tracking-wide"
              style={{
                fontFamily: 'var(--font-display)',
                color: 'var(--color-text-primary)',
              }}
            >
              Game Replay
            </h1>
            {game && (
              <span
                className="text-xs px-2 py-1 rounded"
                style={{
                  background: 'var(--color-bg-elevated)',
                  color: 'var(--color-text-muted)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {game.id.slice(0, 8)}
              </span>
            )}
          </div>

          {/* Phase indicator */}
          <div className="flex items-center gap-3">
            <span className="text-lg">{phaseDisplay.icon}</span>
            <div className="text-right">
              <div
                className="text-sm font-semibold"
                style={{ color: 'var(--color-text-primary)' }}
              >
                {phaseDisplay.label}
              </div>
              <div
                className="text-xs"
                style={{ color: 'var(--color-text-muted)' }}
              >
                Round {store.currentRound}
                {totalRounds > 0 ? ` / ${totalRounds}` : ''}
              </div>
            </div>
          </div>
        </header>

        {/* Main content area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Player circle + Voting */}
          <div className="flex-1 flex flex-col items-center justify-center p-6 overflow-y-auto">
            {/* Player circle */}
            <PlayerCircle
              players={players}
              alivePlayers={alivePlayers}
              speakerId={speakerId}
              mayorId={mayorId}
              revealRoles={store.currentPhase === 'GAME_OVER'}
              onPlayerClick={(playerId) => {
                window.location.href = `/games/${gameId}/agents/${playerId}`;
              }}
            />

            {/* Bidding indicators (shown during DAY_BID / DAY_SPEECH) */}
            {(store.currentPhase === 'DAY_BID' ||
              store.currentPhase === 'DAY_SPEECH') && (
              <div
                className="mt-6 p-4 rounded-xl max-w-xl w-full"
                style={{
                  background: 'var(--glass-bg)',
                  border: '1px solid var(--glass-border)',
                  backdropFilter: 'blur(var(--glass-blur))',
                }}
              >
                <h4
                  className="text-xs font-semibold uppercase tracking-wider mb-3"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  Bid Levels
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {players
                    .filter((p) => alivePlayers.has(p.id))
                    .map((player) => {
                      const turnForPlayer = currentTurns.find(
                        (t) => t.player_id === player.id
                      );
                      const bidLevel = turnForPlayer?.bid_level ?? 0;
                      const isSpeaker = player.id === speakerId;

                      return (
                        <div
                          key={player.id}
                          className="flex items-center gap-2"
                        >
                          <span
                            className="text-xs truncate w-20"
                            style={{
                              color: isSpeaker
                                ? 'var(--color-text-primary)'
                                : 'var(--color-text-secondary)',
                              fontWeight: isSpeaker ? 600 : 400,
                            }}
                          >
                            {player.agent_name}
                          </span>
                          <BiddingBar
                            level={bidLevel}
                            isSpeaker={isSpeaker}
                            size="card"
                            playerName={player.agent_name}
                          />
                        </div>
                      );
                    })}
                </div>
              </div>
            )}

            {/* Voting visualization (shown during VOTE phase) */}
            {store.currentPhase === 'VOTE' && votingData.length > 0 && (
              <div className="mt-6 max-w-xl w-full">
                <VotingViz
                  votes={votingData}
                  players={players}
                  eliminatedId={eliminatedInCurrentVote}
                  mayorId={mayorId}
                />
              </div>
            )}
          </div>

          {/* Right: Chat log */}
          <aside
            className="flex-shrink-0 flex flex-col"
            style={{
              width: 'var(--sidebar-width)',
              borderLeft: '1px solid var(--color-border-subtle)',
            }}
          >
            <ChatLog
              turns={visibleTurns.filter((t) => t.public_statement)}
              players={players}
              activeTurnId={activeTurn?.id}
            />
          </aside>
        </div>

        {/* Bottom: Timeline controls */}
        <footer
          className="flex-shrink-0 px-6 py-3 flex items-center justify-between gap-4"
          style={{
            borderTop: '1px solid var(--color-border-subtle)',
            background: 'var(--color-bg-overlay)',
            backdropFilter: 'blur(12px)',
          }}
        >
          {/* Playback controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => store.reset()}
              className="p-2 rounded-lg transition-colors hover:bg-white/5"
              style={{ color: 'var(--color-text-secondary)' }}
              title="Jump to start"
            >
              ⏮
            </button>

            <button
              onClick={retreatPhase}
              className="p-2 rounded-lg transition-colors hover:bg-white/5"
              style={{ color: 'var(--color-text-secondary)' }}
              title="Previous"
            >
              ⏪
            </button>

            <button
              onClick={() => store.togglePlayPause()}
              className="p-2 px-4 rounded-lg transition-colors hover:bg-white/5 font-semibold"
              style={{ color: 'var(--color-text-primary)' }}
              title={store.isPlaying ? 'Pause' : 'Play'}
            >
              {store.isPlaying ? '⏸' : '▶️'}
            </button>

            <button
              onClick={advancePhase}
              className="p-2 rounded-lg transition-colors hover:bg-white/5"
              style={{ color: 'var(--color-text-secondary)' }}
              title="Next"
            >
              ⏩
            </button>

            <button
              onClick={() => {
                store.setRound(totalRounds);
                store.setPhase('GAME_OVER');
                store.setTurnIndex(0);
                store.pause();
              }}
              className="p-2 rounded-lg transition-colors hover:bg-white/5"
              style={{ color: 'var(--color-text-secondary)' }}
              title="Jump to end"
            >
              ⏭
            </button>
          </div>

          {/* Phase progress */}
          <div className="flex-1 mx-4">
            <div
              className="h-1.5 rounded-full overflow-hidden"
              style={{ background: 'var(--color-bg-elevated)' }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width:
                    totalRounds > 0
                      ? `${((store.currentRound - 1) / totalRounds) * 100 + (ALL_PHASES.indexOf(store.currentPhase) / ALL_PHASES.length / totalRounds) * 100}%`
                      : '0%',
                  background: isNight
                    ? 'var(--color-night-eerie)'
                    : 'var(--color-day-warmth)',
                }}
              />
            </div>
          </div>

          {/* Speed control */}
          <div className="flex items-center gap-2">
            <span
              className="text-xs"
              style={{ color: 'var(--color-text-muted)' }}
            >
              Speed:
            </span>
            {[0.5, 1, 2].map((speed) => (
              <button
                key={speed}
                onClick={() => store.setPlaybackSpeed(speed)}
                className={`text-xs px-2 py-1 rounded transition-colors ${
                  store.playbackSpeed === speed
                    ? 'font-semibold'
                    : 'hover:bg-white/5'
                }`}
                style={{
                  color:
                    store.playbackSpeed === speed
                      ? 'var(--color-text-primary)'
                      : 'var(--color-text-muted)',
                  background:
                    store.playbackSpeed === speed
                      ? 'var(--color-bg-elevated)'
                      : 'transparent',
                }}
              >
                {speed}x
              </button>
            ))}
          </div>
        </footer>
      </div>
    </DayNightBackground>
  );
}
