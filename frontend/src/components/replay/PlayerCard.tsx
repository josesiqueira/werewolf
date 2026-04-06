'use client';

import React from 'react';
import type { Player } from '@/types/player';
import { getProfileColors, getRoleColor } from '@/lib/profileColors';

interface PlayerCardProps {
  player: Player;
  /** Whether this player is alive at the current point in replay */
  isAlive: boolean;
  /** Whether this player is currently speaking */
  isSpeaking?: boolean;
  /** Whether this player is the mayor */
  isMayor?: boolean;
  /** Whether the role should be revealed (dead or game over) */
  roleRevealed?: boolean;
  /** Click handler to open agent inspector */
  onClick?: () => void;
}

export default function PlayerCard({
  player,
  isAlive,
  isSpeaking = false,
  isMayor = false,
  roleRevealed = false,
  onClick,
}: PlayerCardProps) {
  const profile = getProfileColors(player.persuasion_profile ?? 'baseline');
  const roleColor = getRoleColor(player.role ?? '');

  return (
    <div
      onClick={onClick}
      className={`
        ww-player-card
        relative flex flex-col items-center gap-2 p-3 rounded-xl
        cursor-pointer select-none
        transition-all duration-300 ease-out
        ${isAlive ? 'opacity-100' : 'opacity-40 grayscale'}
        ${isSpeaking ? 'scale-105' : 'hover:scale-[1.03]'}
      `}
      style={{
        background: 'var(--glass-bg)',
        border: `1px solid ${isSpeaking ? profile.base : 'var(--glass-border)'}`,
        backdropFilter: `blur(var(--glass-blur))`,
        boxShadow: isSpeaking
          ? `0 0 24px ${profile.glow}, 0 0 48px ${profile.glow}`
          : 'var(--shadow-md)',
        width: '120px',
      }}
    >
      {/* Portrait */}
      <div className="relative">
        <div
          className="w-20 h-20 rounded-full overflow-hidden border-2"
          style={{
            borderColor: isAlive ? profile.base : 'var(--color-border-subtle)',
          }}
        >
          {player.character_image ? (
            <img
              src={player.character_image}
              alt={player.agent_name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div
              className="w-full h-full flex items-center justify-center text-2xl font-bold"
              style={{
                background: `linear-gradient(135deg, ${profile.gradientFrom}, ${profile.gradientTo})`,
                color: 'var(--color-bg-primary)',
              }}
            >
              {player.agent_name?.charAt(0)?.toUpperCase() ?? '?'}
            </div>
          )}

          {/* Dead overlay */}
          {!isAlive && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full">
              <span className="text-2xl">💀</span>
            </div>
          )}
        </div>

        {/* Mayor crown */}
        {isMayor && (
          <div
            className="absolute -top-2 -right-1 text-sm"
            title="Mayor"
          >
            👑
          </div>
        )}

        {/* Speaking indicator */}
        {isSpeaking && (
          <div
            className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full animate-pulse"
            style={{ background: profile.base }}
          />
        )}
      </div>

      {/* Name with profile gradient */}
      <span
        className="text-sm font-semibold text-center leading-tight truncate w-full"
        style={{
          background: isAlive
            ? `linear-gradient(135deg, ${profile.gradientFrom}, ${profile.gradientTo})`
            : 'var(--color-text-muted)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}
      >
        {player.agent_name}
      </span>

      {/* Role (revealed when dead or game over) */}
      {roleRevealed && player.role && (
        <span
          className="text-xs font-medium uppercase tracking-wider"
          style={{ color: roleColor }}
        >
          {player.role}
        </span>
      )}
    </div>
  );
}
