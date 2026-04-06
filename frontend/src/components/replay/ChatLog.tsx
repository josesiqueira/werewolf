'use client';

import React, { useRef, useEffect } from 'react';
import type { Turn } from '@/types/turn';
import type { Player } from '@/types/player';
import { getProfileColors, getProfileHex } from '@/lib/profileColors';

interface ChatLogProps {
  /** Turns to display (already filtered to visible ones) */
  turns: Turn[];
  /** All players in the game for name/profile lookup */
  players: Player[];
  /** The currently active turn (highlighted) */
  activeTurnId?: string | null;
}

/** Human-readable phase labels */
const PHASE_LABELS: Record<string, string> = {
  MAYOR_CAMPAIGN: 'Mayor Campaign',
  MAYOR_VOTE: 'Mayor Vote',
  NIGHT: 'Night',
  DAY_BID: 'Day - Bidding',
  DAY_SPEECH: 'Day - Debate',
  VOTE: 'Vote',
  GAME_OVER: 'Game Over',
};

/** Phase icon indicators */
const PHASE_ICONS: Record<string, string> = {
  NIGHT: '🌙',
  DAY_BID: '☀️',
  DAY_SPEECH: '☀️',
  VOTE: '🗳️',
  MAYOR_CAMPAIGN: '📜',
  MAYOR_VOTE: '🗳️',
  GAME_OVER: '⚰️',
};

function PhaseHeader({ phase, round }: { phase: string; round: number }) {
  const isNight = phase === 'NIGHT';
  return (
    <div
      className="flex items-center gap-2 px-3 py-2 my-2 rounded-lg text-xs font-semibold uppercase tracking-wider"
      style={{
        background: isNight
          ? 'rgba(14, 21, 40, 0.6)'
          : 'rgba(30, 28, 22, 0.6)',
        color: isNight
          ? 'var(--color-night-moon)'
          : 'var(--color-day-warmth)',
        borderLeft: `3px solid ${isNight ? 'var(--color-night-eerie)' : 'var(--color-day-warmth)'}`,
      }}
    >
      <span>{PHASE_ICONS[phase] ?? '📌'}</span>
      <span>
        Round {round} &mdash; {PHASE_LABELS[phase] ?? phase}
      </span>
    </div>
  );
}

function ChatMessage({
  turn,
  player,
  isActive,
}: {
  turn: Turn;
  player: Player | undefined;
  isActive: boolean;
}) {
  const profile = getProfileColors(player?.persuasion_profile ?? 'baseline');
  const profileHex = getProfileHex(player?.persuasion_profile ?? 'baseline');

  if (!turn.public_statement) return null;

  return (
    <div
      className="ww-chat-message flex gap-3 px-4 py-3 rounded-lg transition-all duration-200"
      style={{
        background: isActive ? 'var(--glass-bg-hover)' : 'var(--glass-bg)',
        borderLeft: isActive ? `3px solid ${profile.base}` : '3px solid transparent',
        boxShadow: isActive ? `inset 0 0 0 1px ${profileHex}` : 'none',
      }}
    >
      {/* Mini avatar */}
      <div
        className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold"
        style={{
          background: `linear-gradient(135deg, ${profile.gradientFrom}, ${profile.gradientTo})`,
          color: 'var(--color-bg-primary)',
        }}
      >
        {player?.agent_name?.charAt(0)?.toUpperCase() ?? '?'}
      </div>

      <div className="flex-1 min-w-0">
        {/* Speaker name */}
        <div className="flex items-center gap-2 mb-1">
          <span
            className="text-sm font-semibold"
            style={{
              background: `linear-gradient(135deg, ${profile.gradientFrom}, ${profile.gradientTo})`,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            {player?.agent_name ?? 'Unknown'}
          </span>
          {turn.is_default_response && (
            <span
              className="text-[10px] px-1.5 py-0.5 rounded-full uppercase tracking-wide"
              style={{
                background: 'var(--color-warning)',
                color: 'var(--color-bg-primary)',
              }}
              title="This was an API fallback response"
            >
              default
            </span>
          )}
        </div>

        {/* Message body */}
        <p
          className={`text-sm leading-relaxed ${turn.is_default_response ? 'italic' : ''}`}
          style={{
            color: turn.is_default_response
              ? 'var(--color-text-muted)'
              : 'var(--color-text-primary)',
          }}
        >
          {turn.public_statement}
        </p>
      </div>
    </div>
  );
}

export default function ChatLog({ turns, players, activeTurnId }: ChatLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Build a lookup map for players
  const playerMap = React.useMemo(() => {
    const map = new Map<string, Player>();
    players.forEach((p) => map.set(p.id, p));
    return map;
  }, [players]);

  // Auto-scroll to bottom when new turns appear
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns.length]);

  // Group turns by round + phase for headers
  let lastPhaseKey = '';

  return (
    <div
      className="ww-chat-log flex flex-col h-full rounded-xl overflow-hidden"
      style={{
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border-subtle)',
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-3 flex-shrink-0"
        style={{
          borderBottom: '1px solid var(--color-border-subtle)',
        }}
      >
        <h3
          className="text-sm font-semibold uppercase tracking-wider"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          Game Log
        </h3>
      </div>

      {/* Scrollable messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-3 py-2 space-y-2"
        style={{ scrollbarWidth: 'thin', scrollbarColor: 'var(--color-border-default) transparent' }}
      >
        {turns.length === 0 && (
          <div
            className="flex items-center justify-center h-32 text-sm"
            style={{ color: 'var(--color-text-muted)' }}
          >
            No messages yet. Press play to begin the replay.
          </div>
        )}

        {turns.map((turn) => {
          const phaseKey = `${turn.round_number}-${turn.phase}`;
          const showHeader = phaseKey !== lastPhaseKey;
          lastPhaseKey = phaseKey;
          const player = playerMap.get(turn.player_id);

          return (
            <React.Fragment key={turn.id}>
              {showHeader && (
                <PhaseHeader
                  phase={turn.phase}
                  round={turn.round_number}
                />
              )}
              <ChatMessage
                turn={turn}
                player={player}
                isActive={turn.id === activeTurnId}
              />
            </React.Fragment>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
