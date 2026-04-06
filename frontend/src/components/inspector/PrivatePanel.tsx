'use client';

import React from 'react';

interface PrivatePanelProps {
  reasoning: string;
  isRevealed: boolean;
  onToggleReveal: () => void;
}

export default function PrivatePanel({
  reasoning,
  isRevealed,
  onToggleReveal,
}: PrivatePanelProps) {
  return (
    <div className="ww-private-panel" onClick={onToggleReveal} role="button" tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggleReveal(); } }}
      aria-label={isRevealed ? 'Click to hide private reasoning' : 'Click to reveal private reasoning'}
    >
      <div className="ww-private-panel__header">
        <h3 className="ww-private-panel__title">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" className="ww-private-panel__icon">
            <path d="M8 2C4.5 2 1.7 4.4 1 8c.7 3.6 3.5 6 7 6s6.3-2.4 7-6c-.7-3.6-3.5-6-7-6z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.5" />
          </svg>
          Private Reasoning
        </h3>
        <span className="ww-private-panel__reveal-hint">
          {isRevealed ? 'Click to hide' : 'Click to reveal'}
        </span>
      </div>

      <div className="ww-private-panel__content-wrapper">
        <p
          className={`ww-private-panel__text ${
            isRevealed
              ? 'ww-private-panel__text--revealed'
              : 'ww-private-panel__text--blurred'
          }`}
        >
          {reasoning || 'No private reasoning recorded for this turn.'}
        </p>
        {!isRevealed && (
          <div className="ww-private-panel__overlay">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" strokeWidth="2" />
              <path d="M7 11V7a5 5 0 0110 0v4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <span>Hidden Thoughts</span>
          </div>
        )}
      </div>
    </div>
  );
}
