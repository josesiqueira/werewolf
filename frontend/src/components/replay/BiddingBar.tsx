'use client';

import React from 'react';
import { getBidColor, getBidLabel } from '@/lib/profileColors';

interface BiddingBarProps {
  /** Bid level (0-4) */
  level: number;
  /** Whether this player is the current speaker */
  isSpeaker?: boolean;
  /** Display size variant */
  size?: 'mini' | 'default' | 'card';
  /** Optional player name for label context */
  playerName?: string;
}

const SIZE_CONFIG = {
  mini: { width: 'w-[60px]', height: 'h-1', showLabel: false, gap: 'gap-0.5' },
  default: { width: 'w-[120px]', height: 'h-2', showLabel: true, gap: 'gap-1' },
  card: { width: 'w-[80px]', height: 'h-1.5', showLabel: false, gap: 'gap-0.5' },
} as const;

export default function BiddingBar({
  level,
  isSpeaker = false,
  size = 'default',
  playerName,
}: BiddingBarProps) {
  const config = SIZE_CONFIG[size];
  const clampedLevel = Math.min(Math.max(level, 0), 4);
  const bidColor = getBidColor(clampedLevel);
  const bidLabel = getBidLabel(clampedLevel);

  return (
    <div
      className={`ww-bidding-bar inline-flex items-center ${config.gap} ${isSpeaker ? 'ring-1 ring-white/10 rounded-full px-1.5 py-0.5' : ''}`}
      title={`${playerName ? playerName + ': ' : ''}Bid ${clampedLevel} (${bidLabel})`}
    >
      {/* Segments */}
      <div className={`flex ${config.gap} ${config.width}`}>
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={`flex-1 ${config.height} rounded-full transition-all duration-300`}
            style={{
              background:
                i <= clampedLevel
                  ? getBidColor(i)
                  : 'var(--color-bg-elevated)',
              boxShadow:
                i <= clampedLevel && i === clampedLevel
                  ? `0 0 8px ${bidColor}`
                  : 'none',
              transitionDelay: `${i * 100}ms`,
            }}
          />
        ))}
      </div>

      {/* Label (only in default size) */}
      {config.showLabel && (
        <span
          className="text-[10px] font-semibold uppercase tracking-wide ml-1"
          style={{ color: bidColor }}
        >
          {bidLabel}
        </span>
      )}

      {/* Speaker indicator */}
      {isSpeaker && (
        <div
          className="w-1.5 h-1.5 rounded-full animate-pulse ml-1"
          style={{ background: bidColor }}
        />
      )}
    </div>
  );
}
