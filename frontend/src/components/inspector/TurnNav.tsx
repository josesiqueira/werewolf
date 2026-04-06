'use client';

import React from 'react';

interface TurnNavProps {
  agentName: string;
  currentIndex: number;
  totalTurns: number;
  roundNumber: number | null;
  phase: string | null;
  onPrev: () => void;
  onNext: () => void;
}

const phaseDisplayNames: Record<string, string> = {
  MAYOR_CAMPAIGN: 'Mayor Campaign',
  MAYOR_VOTE: 'Mayor Vote',
  NIGHT: 'Night',
  DAY_BID: 'Day Bid',
  DAY_SPEECH: 'Day Speech',
  VOTE: 'Vote',
};

export default function TurnNav({
  agentName,
  currentIndex,
  totalTurns,
  roundNumber,
  phase,
  onPrev,
  onNext,
}: TurnNavProps) {
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex < totalTurns - 1;
  const phaseLabel = phase ? phaseDisplayNames[phase] || phase : '';
  const turnLabel =
    roundNumber !== null ? `Round ${roundNumber} — ${phaseLabel}` : '';

  return (
    <nav className="ww-turn-nav" aria-label="Turn navigation">
      <button
        className="ww-turn-nav__btn"
        onClick={onPrev}
        disabled={!hasPrev}
        aria-label="Previous turn"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M10 12L6 8L10 4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span className="ww-turn-nav__btn-label">Prev</span>
      </button>

      <div className="ww-turn-nav__center">
        <h2 className="ww-turn-nav__agent-name">{agentName}</h2>
        <span className="ww-turn-nav__turn-info">
          {turnLabel}
          {totalTurns > 0 && (
            <span className="ww-turn-nav__counter">
              {' '}
              ({currentIndex + 1}/{totalTurns})
            </span>
          )}
        </span>
      </div>

      <button
        className="ww-turn-nav__btn"
        onClick={onNext}
        disabled={!hasNext}
        aria-label="Next turn"
      >
        <span className="ww-turn-nav__btn-label">Next</span>
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M6 4L10 8L6 12"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </nav>
  );
}
