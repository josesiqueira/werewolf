'use client';

import React from 'react';
import type { Player } from '@/types/player';
import { getProfileColors, getProfileHex } from '@/lib/profileColors';

interface VoteEntry {
  voterId: string;
  targetId: string;
}

interface VotingVizProps {
  /** All votes cast in this voting phase */
  votes: VoteEntry[];
  /** All players */
  players: Player[];
  /** ID of the player who was eliminated (if any) */
  eliminatedId?: string | null;
  /** ID of the mayor (for tiebreak highlighting) */
  mayorId?: string | null;
}

interface VoteTally {
  targetId: string;
  targetName: string;
  count: number;
  voters: { id: string; agent_name: string; persuasion_profile: string }[];
}

export default function VotingViz({
  votes,
  players,
  eliminatedId,
  mayorId,
}: VotingVizProps) {
  const playerMap = React.useMemo(() => {
    const map = new Map<string, Player>();
    players.forEach((p) => map.set(p.id, p));
    return map;
  }, [players]);

  // Build tally
  const tally = React.useMemo(() => {
    const tallyMap = new Map<string, VoteTally>();

    votes.forEach(({ voterId, targetId }) => {
      const voter = playerMap.get(voterId);
      const target = playerMap.get(targetId);

      if (!tallyMap.has(targetId)) {
        tallyMap.set(targetId, {
          targetId,
          targetName: target?.agent_name ?? 'Unknown',
          count: 0,
          voters: [],
        });
      }

      const entry = tallyMap.get(targetId)!;
      entry.count++;
      entry.voters.push({
        id: voterId,
        agent_name: voter?.agent_name ?? 'Unknown',
        persuasion_profile: voter?.persuasion_profile ?? 'baseline',
      });
    });

    return Array.from(tallyMap.values()).sort((a, b) => b.count - a.count);
  }, [votes, playerMap]);

  if (votes.length === 0) {
    return (
      <div
        className="flex items-center justify-center h-32 text-sm rounded-xl"
        style={{
          background: 'var(--glass-bg)',
          color: 'var(--color-text-muted)',
          border: '1px solid var(--glass-border)',
        }}
      >
        No votes cast in this phase.
      </div>
    );
  }

  return (
    <div
      className="ww-voting-viz rounded-xl overflow-hidden"
      style={{
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border-subtle)',
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-3"
        style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
      >
        <h3
          className="text-sm font-semibold uppercase tracking-wider"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          Vote Results
        </h3>
      </div>

      {/* Vote tally list */}
      <div className="p-4 space-y-4">
        {tally.map((entry) => {
          const isEliminated = entry.targetId === eliminatedId;
          const target = playerMap.get(entry.targetId);
          const targetProfile = getProfileColors(target?.persuasion_profile ?? 'baseline');
          const maxVotes = tally[0]?.count ?? 1;
          const barWidth = (entry.count / maxVotes) * 100;

          return (
            <div key={entry.targetId} className="space-y-2">
              {/* Target name and vote count */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-sm font-semibold ${isEliminated ? 'line-through' : ''}`}
                    style={{
                      color: isEliminated
                        ? 'var(--color-eliminated)'
                        : 'var(--color-text-primary)',
                    }}
                  >
                    {entry.targetName}
                  </span>
                  {isEliminated && (
                    <span
                      className="text-xs px-2 py-0.5 rounded-full font-semibold uppercase tracking-wide"
                      style={{
                        background: 'rgba(153, 27, 27, 0.3)',
                        color: 'var(--color-eliminated)',
                        border: '1px solid var(--color-eliminated)',
                      }}
                    >
                      Eliminated
                    </span>
                  )}
                </div>
                <span
                  className="text-sm font-bold tabular-nums"
                  style={{ color: 'var(--color-text-primary)' }}
                >
                  {entry.count} vote{entry.count !== 1 ? 's' : ''}
                </span>
              </div>

              {/* Vote bar */}
              <div
                className="h-2 rounded-full overflow-hidden"
                style={{ background: 'var(--color-bg-elevated)' }}
              >
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${barWidth}%`,
                    background: isEliminated
                      ? 'var(--color-eliminated)'
                      : `linear-gradient(90deg, ${targetProfile.gradientFrom}, ${targetProfile.gradientTo})`,
                  }}
                />
              </div>

              {/* Voter list with arrows */}
              <div className="flex flex-wrap gap-2">
                {entry.voters.map((voter) => {
                  const voterHex = getProfileHex(voter.persuasion_profile);
                  const isMayorVote = voter.id === mayorId;

                  return (
                    <div
                      key={voter.id}
                      className="flex items-center gap-1 text-xs px-2 py-1 rounded-full"
                      style={{
                        background: 'var(--color-bg-elevated)',
                        border: isMayorVote
                          ? '1px solid var(--color-mayor)'
                          : '1px solid var(--color-border-subtle)',
                      }}
                    >
                      <span
                        className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ background: voterHex }}
                      />
                      <span style={{ color: voterHex }}>
                        {voter.agent_name}
                      </span>
                      <span style={{ color: 'var(--color-text-muted)' }}>
                        &rarr;
                      </span>
                      {isMayorVote && (
                        <span className="text-[10px]" title="Mayor vote">
                          👑
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      {eliminatedId && (
        <div
          className="px-4 py-3 text-center text-sm"
          style={{
            borderTop: '1px solid var(--color-border-subtle)',
            background: 'rgba(153, 27, 27, 0.1)',
          }}
        >
          <span style={{ color: 'var(--color-eliminated)' }}>
            {playerMap.get(eliminatedId)?.agent_name ?? 'Unknown'} was eliminated.
          </span>
          {playerMap.get(eliminatedId)?.role && (
            <span style={{ color: 'var(--color-text-muted)' }}>
              {' '}
              Role revealed:{' '}
              <span
                className="font-semibold uppercase"
                style={{
                  color: `var(--color-${playerMap.get(eliminatedId)?.role?.toLowerCase() ?? 'villager'})`,
                }}
              >
                {playerMap.get(eliminatedId)?.role}
              </span>
            </span>
          )}
        </div>
      )}
    </div>
  );
}
