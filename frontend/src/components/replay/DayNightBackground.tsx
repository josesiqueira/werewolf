'use client';

import React from 'react';

interface DayNightBackgroundProps {
  /** Whether the current phase is a night phase */
  isNight: boolean;
  /** Children to render on top of the background */
  children: React.ReactNode;
}

/**
 * Subtle background color change between day (warm) and night (cool blue) phases.
 * Renders atmospheric gradients and applies a phase transition crossfade.
 */
export default function DayNightBackground({
  isNight,
  children,
}: DayNightBackgroundProps) {
  return (
    <div className="ww-day-night-bg relative min-h-screen overflow-hidden">
      {/* Night layer */}
      <div
        className="absolute inset-0 transition-opacity pointer-events-none"
        style={{
          opacity: isNight ? 1 : 0,
          transitionDuration: '1.2s',
          transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
          background: `
            radial-gradient(ellipse at 20% 20%, rgba(74, 111, 165, 0.08) 0%, transparent 60%),
            radial-gradient(ellipse at 80% 80%, rgba(74, 111, 165, 0.05) 0%, transparent 50%),
            linear-gradient(180deg, var(--color-night-deep) 0%, #0a0f1e 50%, var(--color-night-sky) 100%)
          `,
        }}
      >
        {/* Moon glow effect */}
        <div
          className="absolute top-12 right-24 w-32 h-32 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(184, 197, 214, 0.12) 0%, transparent 70%)',
            filter: 'blur(20px)',
          }}
        />
        {/* Eerie ambient particles (CSS-only) */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `
              radial-gradient(1px 1px at 10% 30%, rgba(184, 197, 214, 0.15), transparent),
              radial-gradient(1px 1px at 30% 70%, rgba(74, 111, 165, 0.12), transparent),
              radial-gradient(1px 1px at 50% 20%, rgba(184, 197, 214, 0.08), transparent),
              radial-gradient(1px 1px at 70% 60%, rgba(74, 111, 165, 0.10), transparent),
              radial-gradient(1px 1px at 90% 40%, rgba(184, 197, 214, 0.06), transparent)
            `,
          }}
        />
      </div>

      {/* Day layer */}
      <div
        className="absolute inset-0 transition-opacity pointer-events-none"
        style={{
          opacity: isNight ? 0 : 1,
          transitionDuration: '1.2s',
          transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
          background: `
            radial-gradient(ellipse at 60% 10%, rgba(196, 164, 108, 0.10) 0%, transparent 60%),
            radial-gradient(ellipse at 30% 70%, rgba(196, 164, 108, 0.05) 0%, transparent 50%),
            linear-gradient(180deg, #14120f 0%, var(--color-bg-primary) 40%, #0f0e0c 100%)
          `,
        }}
      >
        {/* Warm light rays */}
        <div
          className="absolute top-0 left-1/3 w-64 h-96"
          style={{
            background: 'linear-gradient(180deg, rgba(196, 164, 108, 0.06) 0%, transparent 100%)',
            filter: 'blur(40px)',
            transform: 'rotate(-15deg)',
          }}
        />
        {/* Mist effect */}
        <div
          className="absolute bottom-0 inset-x-0 h-48"
          style={{
            background: 'linear-gradient(0deg, rgba(154, 165, 177, 0.04) 0%, transparent 100%)',
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
}
