'use client';

import React from 'react';
import type { Player } from '@/types/player';
import PlayerCard from './PlayerCard';

interface PlayerCircleProps {
  players: Player[];
  /** Set of player IDs that are alive at the current point */
  alivePlayers: Set<string>;
  /** ID of the player currently speaking */
  speakerId?: string | null;
  /** ID of the current mayor */
  mayorId?: string | null;
  /** Whether to reveal all roles */
  revealRoles?: boolean;
  /** Callback when a player card is clicked */
  onPlayerClick?: (playerId: string) => void;
}

export default function PlayerCircle({
  players,
  alivePlayers,
  speakerId,
  mayorId,
  revealRoles = false,
  onPlayerClick,
}: PlayerCircleProps) {
  const count = players.length;
  // Circle radius based on player count. 7 players => ~220px radius works well.
  const radius = Math.max(180, count * 32);

  return (
    <div
      className="ww-player-circle relative mx-auto"
      style={{
        width: `${radius * 2 + 140}px`,
        height: `${radius * 2 + 140}px`,
      }}
    >
      {players.map((player, index) => {
        // Distribute evenly in a circle, starting from the top (-90 degrees)
        const angle = (index / count) * 2 * Math.PI - Math.PI / 2;
        const x = radius * Math.cos(angle);
        const y = radius * Math.sin(angle);

        const isAlive = alivePlayers.has(player.id);
        const isSpeaking = speakerId === player.id;
        const isMayor = mayorId === player.id;
        const roleRevealed = revealRoles || !isAlive;

        return (
          <div
            key={player.id}
            className="absolute transition-all duration-500 ease-out"
            style={{
              left: `calc(50% + ${x}px - 60px)`,
              top: `calc(50% + ${y}px - 80px)`,
            }}
          >
            <PlayerCard
              player={player}
              isAlive={isAlive}
              isSpeaking={isSpeaking}
              isMayor={isMayor}
              roleRevealed={roleRevealed}
              onClick={() => onPlayerClick?.(player.id)}
            />
          </div>
        );
      })}

      {/* Center phase indicator */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div
          className="w-24 h-24 rounded-full flex items-center justify-center"
          style={{
            background: 'var(--glass-bg)',
            border: '1px solid var(--glass-border)',
            backdropFilter: 'blur(var(--glass-blur))',
          }}
        >
          <span
            className="text-xs font-semibold uppercase tracking-widest"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            Village
          </span>
        </div>
      </div>
    </div>
  );
}
