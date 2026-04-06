import { create } from 'zustand';

export type GamePhase =
  | 'MAYOR_CAMPAIGN'
  | 'MAYOR_VOTE'
  | 'NIGHT'
  | 'DAY_BID'
  | 'DAY_SPEECH'
  | 'VOTE'
  | 'GAME_OVER';

interface ReplayState {
  /** Current game phase being displayed */
  currentPhase: GamePhase;
  /** Current round number (1-based) */
  currentRound: number;
  /** Index into the turn list for the current phase */
  currentTurnIndex: number;
  /** Whether the replay is auto-playing */
  isPlaying: boolean;
  /** Playback speed multiplier (1 = normal) */
  playbackSpeed: number;

  // Actions
  setPhase: (phase: GamePhase) => void;
  setRound: (round: number) => void;
  setTurnIndex: (index: number) => void;
  play: () => void;
  pause: () => void;
  togglePlayPause: () => void;
  setPlaybackSpeed: (speed: number) => void;
  nextTurn: () => void;
  prevTurn: () => void;
  reset: () => void;
  jumpTo: (round: number, phase: GamePhase, turnIndex: number) => void;
}

export const useReplayStore = create<ReplayState>((set) => ({
  currentPhase: 'MAYOR_CAMPAIGN',
  currentRound: 1,
  currentTurnIndex: 0,
  isPlaying: false,
  playbackSpeed: 1,

  setPhase: (phase) => set({ currentPhase: phase }),
  setRound: (round) => set({ currentRound: round }),
  setTurnIndex: (index) => set({ currentTurnIndex: index }),
  play: () => set({ isPlaying: true }),
  pause: () => set({ isPlaying: false }),
  togglePlayPause: () => set((s) => ({ isPlaying: !s.isPlaying })),
  setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),

  nextTurn: () =>
    set((s) => ({ currentTurnIndex: s.currentTurnIndex + 1 })),

  prevTurn: () =>
    set((s) => ({
      currentTurnIndex: Math.max(0, s.currentTurnIndex - 1),
    })),

  reset: () =>
    set({
      currentPhase: 'MAYOR_CAMPAIGN',
      currentRound: 1,
      currentTurnIndex: 0,
      isPlaying: false,
    }),

  jumpTo: (round, phase, turnIndex) =>
    set({
      currentRound: round,
      currentPhase: phase,
      currentTurnIndex: turnIndex,
      isPlaying: false,
    }),
}));
