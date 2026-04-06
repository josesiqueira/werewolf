'use client';

import React from 'react';
import TurnNav from './TurnNav';
import PrivatePanel from './PrivatePanel';
import PublicPanel from './PublicPanel';
import MetadataBar from './MetadataBar';

interface InspectorLayoutProps {
  agentName: string;
  currentTurnIndex: number;
  totalTurns: number;
  roundNumber: number | null;
  phase: string | null;
  privateReasoning: string;
  publicStatement: string;
  isPrivateRevealed: boolean;
  techniqueLabel: string;
  deceptionLabel: string;
  confidence: number;
  bidLevel: number;
  profile: string;
  role: string;
  onPrevTurn: () => void;
  onNextTurn: () => void;
  onToggleReveal: () => void;
}

export default function InspectorLayout({
  agentName,
  currentTurnIndex,
  totalTurns,
  roundNumber,
  phase,
  privateReasoning,
  publicStatement,
  isPrivateRevealed,
  techniqueLabel,
  deceptionLabel,
  confidence,
  bidLevel,
  profile,
  role,
  onPrevTurn,
  onNextTurn,
  onToggleReveal,
}: InspectorLayoutProps) {
  return (
    <div className="ww-inspector">
      <TurnNav
        agentName={agentName}
        currentIndex={currentTurnIndex}
        totalTurns={totalTurns}
        roundNumber={roundNumber}
        phase={phase}
        onPrev={onPrevTurn}
        onNext={onNextTurn}
      />

      <div className="ww-inspector__panels">
        <PrivatePanel
          reasoning={privateReasoning}
          isRevealed={isPrivateRevealed}
          onToggleReveal={onToggleReveal}
        />
        <PublicPanel statement={publicStatement} />
      </div>

      <MetadataBar
        techniqueLabel={techniqueLabel}
        deceptionLabel={deceptionLabel}
        confidence={confidence}
        bidLevel={bidLevel}
        profile={profile}
        role={role}
      />
    </div>
  );
}
