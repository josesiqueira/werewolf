'use client';

import React from 'react';

interface MetadataBarProps {
  techniqueLabel: string;
  deceptionLabel: string;
  confidence: number;
  bidLevel: number;
  profile: string;
  role: string;
}

const profileDisplayNames: Record<string, string> = {
  ethos: 'Ethos',
  pathos: 'Pathos',
  logos: 'Logos',
  authority_socialproof: 'Authority',
  reciprocity_liking: 'Reciprocity',
  scarcity_commitment: 'Scarcity',
  baseline: 'Baseline',
};

const deceptionColors: Record<string, string> = {
  truthful: 'var(--color-success)',
  omission: 'var(--color-warning)',
  distortion: 'var(--color-scarcity)',
  fabrication: 'var(--color-error)',
  misdirection: 'var(--color-reciprocity)',
};

const bidLabels: string[] = ['Silent', 'Low', 'Medium', 'High', 'Urgent'];

const bidColorVars: string[] = [
  'var(--color-bid-0)',
  'var(--color-bid-1)',
  'var(--color-bid-2)',
  'var(--color-bid-3)',
  'var(--color-bid-4)',
];

function ConfidenceStars({ level }: { level: number }) {
  const clamped = Math.max(0, Math.min(5, Math.round(level)));
  return (
    <span className="ww-metadata__stars" aria-label={`Confidence: ${clamped} out of 5`}>
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          className={`ww-metadata__star ${
            i < clamped ? 'ww-metadata__star--filled' : 'ww-metadata__star--empty'
          }`}
        >
          &#9733;
        </span>
      ))}
    </span>
  );
}

function BidIndicator({ level }: { level: number }) {
  const clamped = Math.max(0, Math.min(4, level));
  return (
    <span className="ww-metadata__bid">
      <span className="ww-metadata__bid-bar">
        {Array.from({ length: 5 }, (_, i) => (
          <span
            key={i}
            className="ww-metadata__bid-segment"
            style={{
              backgroundColor: i <= clamped ? bidColorVars[i] : 'var(--color-border-subtle)',
            }}
          />
        ))}
      </span>
      <span className="ww-metadata__bid-label">{bidLabels[clamped]}</span>
    </span>
  );
}

function ProfileBadgeInline({ profile }: { profile: string }) {
  const displayName = profileDisplayNames[profile] || profile;
  return (
    <span className={`ww-profile-badge ww-profile-badge--${profile.replace(/_/g, '-')}`}>
      {displayName}
    </span>
  );
}

export default function MetadataBar({
  techniqueLabel,
  deceptionLabel,
  confidence,
  bidLevel,
  profile,
  role,
}: MetadataBarProps) {
  const deceptionColor = deceptionColors[deceptionLabel] || 'var(--color-text-secondary)';

  return (
    <div className="ww-metadata-bar">
      <div className="ww-metadata-bar__item">
        <span className="ww-metadata-bar__label">Profile</span>
        <ProfileBadgeInline profile={profile} />
      </div>

      <div className="ww-metadata-bar__item">
        <span className="ww-metadata-bar__label">Technique</span>
        <span className="ww-metadata-bar__value">{techniqueLabel || 'none'}</span>
      </div>

      <div className="ww-metadata-bar__item">
        <span className="ww-metadata-bar__label">Deception</span>
        <span
          className="ww-metadata-bar__value ww-metadata-bar__deception"
          style={{ color: deceptionColor }}
        >
          {deceptionLabel || 'unknown'}
        </span>
      </div>

      <div className="ww-metadata-bar__item">
        <span className="ww-metadata-bar__label">Confidence</span>
        <ConfidenceStars level={confidence} />
      </div>

      <div className="ww-metadata-bar__item">
        <span className="ww-metadata-bar__label">Bid</span>
        <BidIndicator level={bidLevel} />
      </div>

      <div className="ww-metadata-bar__item">
        <span className="ww-metadata-bar__label">Role</span>
        <span className={`ww-metadata-bar__role ww-metadata-bar__role--${role?.toLowerCase()}`}>
          {role || 'Unknown'}
        </span>
      </div>
    </div>
  );
}
