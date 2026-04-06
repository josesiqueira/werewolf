'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { useAgentInspector } from '@/hooks/useAgentInspector';
import InspectorLayout from '@/components/inspector/InspectorLayout';
import Link from 'next/link';

export default function AgentInspectorPage() {
  const params = useParams();
  const gameId = params.id as string;
  const agentId = params.agentId as string;

  const {
    player,
    turns,
    currentTurnIndex,
    currentTurn,
    isLoading,
    error,
    isPrivateRevealed,
    goToNextTurn,
    goToPrevTurn,
    togglePrivateReveal,
  } = useAgentInspector(gameId, agentId);

  if (isLoading) {
    return (
      <div className="ww-inspector-page ww-inspector-page--loading">
        <div className="ww-inspector-page__spinner">
          <div className="ww-spinner" />
          <p>Loading agent data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ww-inspector-page ww-inspector-page--error">
        <div className="ww-inspector-page__error-card">
          <h2>Error</h2>
          <p>{error}</p>
          <Link href={`/games/${gameId}`} className="ww-inspector-page__back-link">
            Back to Game
          </Link>
        </div>
      </div>
    );
  }

  if (!player || turns.length === 0) {
    return (
      <div className="ww-inspector-page ww-inspector-page--empty">
        <div className="ww-inspector-page__empty-card">
          <h2>No Turn Data</h2>
          <p>No turns found for this agent in this game.</p>
          <Link href={`/games/${gameId}`} className="ww-inspector-page__back-link">
            Back to Game
          </Link>
        </div>
      </div>
    );
  }

  const portraitSrc = player.character_image
    ? `/portraits/${player.character_image}`
    : '/portraits/portrait_1.svg';

  return (
    <div className="ww-inspector-page">
      <div className="ww-inspector-page__breadcrumb">
        <Link href="/games" className="ww-inspector-page__crumb">
          Games
        </Link>
        <span className="ww-inspector-page__crumb-sep">/</span>
        <Link href={`/games/${gameId}`} className="ww-inspector-page__crumb">
          {gameId.slice(0, 8)}...
        </Link>
        <span className="ww-inspector-page__crumb-sep">/</span>
        <span className="ww-inspector-page__crumb ww-inspector-page__crumb--current">
          {player.agent_name}
        </span>
      </div>

      <div className="ww-inspector-page__portrait-header">
        <div className="ww-inspector-page__portrait-wrapper">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={portraitSrc}
            alt={`Portrait of ${player.agent_name}`}
            className="ww-inspector-page__portrait"
          />
          {player.is_mayor && (
            <span className="ww-inspector-page__mayor-badge" title="Mayor">
              &#9812;
            </span>
          )}
        </div>
      </div>

      <InspectorLayout
        agentName={player.agent_name}
        currentTurnIndex={currentTurnIndex}
        totalTurns={turns.length}
        roundNumber={currentTurn?.round_number ?? null}
        phase={currentTurn?.phase ?? null}
        privateReasoning={currentTurn?.private_reasoning ?? ''}
        publicStatement={currentTurn?.public_statement ?? ''}
        isPrivateRevealed={isPrivateRevealed}
        techniqueLabel={currentTurn?.technique_self_label ?? ''}
        deceptionLabel={currentTurn?.deception_self_label ?? ''}
        confidence={currentTurn?.confidence ?? 0}
        bidLevel={currentTurn?.bid_level ?? 0}
        profile={player.persuasion_profile}
        role={player.role}
        onPrevTurn={goToPrevTurn}
        onNextTurn={goToNextTurn}
        onToggleReveal={togglePrivateReveal}
      />
    </div>
  );
}
