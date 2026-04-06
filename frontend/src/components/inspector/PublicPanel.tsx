'use client';

import React from 'react';

interface PublicPanelProps {
  statement: string;
}

export default function PublicPanel({ statement }: PublicPanelProps) {
  return (
    <div className="ww-public-panel">
      <div className="ww-public-panel__header">
        <h3 className="ww-public-panel__title">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" className="ww-public-panel__icon">
            <path d="M2 4h12M2 8h8M2 12h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          Public Statement
        </h3>
      </div>

      <div className="ww-public-panel__content">
        <p className="ww-public-panel__text">
          {statement || 'No public statement recorded for this turn.'}
        </p>
      </div>
    </div>
  );
}
