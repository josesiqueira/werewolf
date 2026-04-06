# Component Conventions

Project: Werewolf AI Agents
Date: 2026-04-03

## Naming

- Components: PascalCase (e.g., `PlayerCard`, `ChatMessage`, `VotingArrow`)
- CSS classes: kebab-case with `ww-` prefix (e.g., `ww-player-card`, `ww-chat-message`)
- Tokens: always use CSS custom properties from `tokens.css`, never raw color/spacing values
- Files: PascalCase matching component name (e.g., `PlayerCard.tsx`)

## Composition rules

- Every component gets its own file in the appropriate directory under `src/components/`
- Components reference `tokens.css` -- no inline colors, no hardcoded spacing
- Interactive elements must have hover, focus, active, and disabled states defined
- Loading states are required for any component that fetches data
- Empty states are required for any list, table, or data display
- Dead/eliminated states must be handled for all player-related components
- Profile colors must always be derived from the profile token, never hardcoded per-instance

## Profile color mapping

Components that display profile-colored elements must use this mapping:

| Profile | CSS variable prefix | Gradient direction |
|---------|--------------------|--------------------|
| ethos | `--color-ethos-*` | Blue to silver |
| pathos | `--color-pathos-*` | Red to warm peach |
| logos | `--color-logos-*` | Green to teal |
| authority_socialproof | `--color-authority-*` | Gold to amber |
| reciprocity_liking | `--color-reciprocity-*` | Purple to pink |
| scarcity_commitment | `--color-scarcity-*` | Orange to fire-red |
| baseline | `--color-baseline-*` | Neutral gray to light gray |

Helper utility: create a `getProfileColor(profile: string)` function that returns the token variable names for any profile string.

---

## Component catalog

### PlayerCard

**File**: `src/components/replay/PlayerCard.tsx`
**Status**: Planned (Phase 4)
**React Bits**: TiltedCard, Magnet

**Description**: Displays a single player in the game replay circle. Shows character portrait, name, role (when revealed), persuasion profile badge, and alive/dead status.

**Structure**:
```
<TiltedCard>
  <Magnet>
    <div class="ww-player-card">
      <div class="ww-player-card__portrait">
        <img /> (character portrait, circular crop)
        <ProfileBadge /> (bottom-right overlay)
      </div>
      <div class="ww-player-card__name">
        <GradientText> (profile-colored)
      </div>
      <div class="ww-player-card__role"> (hidden until revealed)
      <StatusBadge /> (mayor, speaking, etc.)
    </div>
  </Magnet>
</TiltedCard>
```

**States**:
- **Alive**: Full opacity, active glow on hover, portrait fully rendered
- **Dead**: Opacity 0.4, desaturated portrait, red slash overlay, role text revealed, profile badge dimmed
- **Speaking**: Pulsing profile-colored border glow, slightly elevated (scale 1.05)
- **Selected** (inspector): SpotlightCard highlight, persistent glow
- **Mayor**: Small crown icon overlay on portrait

**Sizing**:
- Circle layout: 120px x 160px (portrait 80px diameter)
- Compact/mobile: 80px x 110px (portrait 56px diameter)

---

### ChatMessage

**File**: `src/components/replay/ChatMessage.tsx`
**Status**: Planned (Phase 4)
**React Bits**: AnimatedList

**Description**: A single message in the chat log panel. Shows the speaker's name (profile-colored), their public statement, and metadata (bid level, phase).

**Structure**:
```
<div class="ww-chat-message">
  <div class="ww-chat-message__header">
    <img class="ww-chat-message__avatar" /> (small portrait, 32px)
    <GradientText class="ww-chat-message__name"> (profile gradient)
    <span class="ww-chat-message__phase-tag"> (Day 3, Night 2, etc.)
  </div>
  <div class="ww-chat-message__body">
    <p> (public_statement text)
  </div>
  <div class="ww-chat-message__meta">
    <BiddingBar level={bid} /> (inline mini version)
    <span class="ww-chat-message__confidence"> (confidence dots)
  </div>
</div>
```

**States**:
- **Default**: Standard glass-morphism card
- **Current** (replay active): Left border in profile color, slight elevation
- **Werewolf message** (post-game reveal mode): Faint red tint on background
- **Default response** (API fallback): Italic text, muted color, warning icon

**Spacing**: Messages separated by `--space-2`. Internal padding `--space-4`.

---

### VotingArrow

**File**: `src/components/replay/VotingArrow.tsx`
**Status**: Planned (Phase 4)
**React Bits**: FollowCursor-style animation

**Description**: An animated SVG arrow connecting a voter's PlayerCard to their target's PlayerCard. Appears during vote visualization phase.

**Behavior**:
- Arrows draw from voter to target over 400ms with ease-out
- Arrow color matches the voter's profile color
- Arrow thickness: 2px default, 3px for mayor's vote
- On hover over an arrow: tooltip shows voter name and target name
- Mayor's tiebreak arrow has a dashed style and gold color
- All arrows for a single voter highlight on hover over that voter's PlayerCard

**Animation sequence**:
1. All arrows draw simultaneously from voter positions to target positions
2. Target with most arrows gets a pulsing red glow (elimination pending)
3. After 1.5s, eliminated player's card transitions to dead state

---

### BiddingBar

**File**: `src/components/replay/BiddingBar.tsx`
**Status**: Planned (Phase 4)

**Description**: A horizontal heat indicator showing a player's bid level (0-4). Used both inline in chat messages (mini) and as an overlay on player cards.

**Structure**:
```
<div class="ww-bidding-bar">
  <div class="ww-bidding-bar__segment" /> (x5 segments, filled up to bid level)
  <span class="ww-bidding-bar__label">Bid: {level}</span>
</div>
```

**Visual mapping**:
| Bid | Color | Label |
|-----|-------|-------|
| 0 | `--color-bid-0` (cool blue) | Silent |
| 1 | `--color-bid-1` (green) | Low |
| 2 | `--color-bid-2` (yellow) | Medium |
| 3 | `--color-bid-3` (orange) | High |
| 4 | `--color-bid-4` (red) | Urgent |

**Sizes**:
- Full: 120px wide, 8px tall segments, label visible
- Mini (inline): 60px wide, 4px tall segments, no label
- Card overlay: 80px wide, 6px tall, positioned at card bottom

**Animation**: Segments fill left-to-right with 100ms stagger per segment.

---

### ProfileBadge

**File**: `src/components/shared/ProfileBadge.tsx`
**Status**: Planned (Phase 4)

**Description**: A colored pill displaying the persuasion profile name. Used on player cards, in the inspector, on game list rows, and in analytics.

**Structure**:
```
<span class="ww-profile-badge ww-profile-badge--{profile}">
  {profileDisplayName}
</span>
```

**Display names**:
| Profile key | Display name |
|-------------|-------------|
| ethos | Ethos |
| pathos | Pathos |
| logos | Logos |
| authority_socialproof | Authority |
| reciprocity_liking | Reciprocity |
| scarcity_commitment | Scarcity |
| baseline | Baseline |

**Styling**:
- Background: profile glow color (e.g., `--color-ethos-glow`)
- Text: profile base color (e.g., `--color-ethos`)
- Border: 1px solid profile base color at 30% opacity
- Border radius: `--radius-full`
- Font: `--font-body`, `--font-size-xs`, `--font-weight-semibold`
- Letter spacing: `--letter-spacing-wide`
- Text transform: uppercase

**Sizes**:
- Default: padding `--space-1` x `--space-3`
- Small: padding `--space-0-5` x `--space-2`, `--font-size-2xs`
- Large: padding `--space-2` x `--space-4`, `--font-size-sm`

**States**:
- Default: as described
- Dimmed (dead player): opacity 0.4
- Active (inspector selected): box-shadow using `--glow-profile-sm`

---

### StatusBadge

**File**: `src/components/shared/StatusBadge.tsx`
**Status**: Planned (Phase 4)

**Description**: A small indicator for game and player status. Used in game list, player cards, and dashboard.

**Variants**:

| Status | Color | Icon |
|--------|-------|------|
| pending | `--color-text-muted` | Clock |
| running | `--color-info` | Spinning dot |
| completed | `--color-success` | Checkmark |
| discarded | `--color-warning` | X mark |
| degraded | `--color-warning` | Warning triangle |
| alive | `--color-alive` | Heart |
| dead | `--color-dead` | Skull |
| mayor | `--color-mayor` | Crown |

**Structure**:
```
<span class="ww-status-badge ww-status-badge--{status}">
  <Icon />
  <span>{label}</span>
</span>
```

---

### InspectorPanel

**File**: `src/components/inspector/InspectorLayout.tsx`
**Status**: Planned (Phase 4)
**React Bits**: SpotlightCard, BlurText

**Description**: The agent inspector view showing private reasoning alongside public behavior for a selected agent at a specific turn.

**Layout**:
```
+--------------------------------------------------+
|  [< Prev Turn]   Agent Name   [Next Turn >]      |  (TurnNav)
+--------------------------------------------------+
|                    |                               |
|  PRIVATE           |  PUBLIC                       |
|  REASONING         |  STATEMENT                    |
|                    |                               |
|  (BlurText reveal) |  (normal text)                |
|                    |                               |
|                    |                               |
+--------------------------------------------------+
|  Profile: [badge]  |  Deception: [label]          |  (MetadataBar)
|  Technique: [tag]  |  Confidence: [stars]         |
|  Bid: [bar]        |  Role: [role]                |
+--------------------------------------------------+
```

**Panels**:
- **PrivatePanel** (`src/components/inspector/PrivatePanel.tsx`): Left side. Shows `private_reasoning` text. Uses BlurText -- content starts blurred and reveals on click or hover, reinforcing the "hidden information" theme. Background has a slightly warmer/redder tint than the public side.
- **PublicPanel** (`src/components/inspector/PublicPanel.tsx`): Right side. Shows `public_statement` text. Standard readable text. Background is the default glass surface.
- **MetadataBar** (`src/components/inspector/MetadataBar.tsx`): Bottom strip. Shows technique_self_label, deception_self_label, confidence (1-5 as filled/unfilled dots), bid_level (BiddingBar mini), assigned profile (ProfileBadge), and player role.
- **TurnNav** (`src/components/inspector/TurnNav.tsx`): Top bar with previous/next turn buttons for the same agent. Shows current turn number and phase.

**Responsive**:
- Desktop: side-by-side panels, minimum 480px per panel
- Tablet: stacked vertically, private above public
- Mobile: tabbed view (Private | Public toggle)

---

### TimelineScrubber

**File**: `src/components/replay/Timeline.tsx`
**Status**: Planned (Phase 4)

**Description**: Horizontal timeline at the bottom of the game replay page. Allows scrubbing between phases and rounds.

**Structure**:
```
<div class="ww-timeline">
  <div class="ww-timeline__track">
    <div class="ww-timeline__segment" /> (one per phase)
  </div>
  <div class="ww-timeline__playhead" /> (current position indicator)
  <div class="ww-timeline__controls">
    <button>|<</button> (start)
    <button><</button>  (previous phase)
    <button>Play/Pause</button>
    <button>></button>  (next phase)
    <button>>|</button> (end)
  </div>
</div>
```

**Visual design**:
- Track: horizontal bar, full width minus padding
- Segments: alternating day (warm tint) and night (cool tint) sections
- Mayor election: gold-tinted segment at the start
- Vote phases: marked with small red tick marks
- Eliminations: skull icon at the relevant position
- Playhead: vertical line with profile-colored dot, draggable
- Current phase label above playhead

**Behavior**:
- Click any segment to jump to that phase
- Drag playhead to scrub
- Play button auto-advances through phases at configurable speed
- Keyboard: left/right arrows for prev/next phase, space for play/pause

---

### StatCard

**File**: `src/components/dashboard/StatsCards.tsx`
**Status**: Planned (Phase 4)
**React Bits**: CountUp

**Description**: An animated statistics card for the dashboard. Shows a large number with label and optional trend indicator.

**Structure**:
```
<div class="ww-stat-card">
  <div class="ww-stat-card__value">
    <CountUp end={value} />
  </div>
  <div class="ww-stat-card__label">{label}</div>
  <div class="ww-stat-card__trend"> (optional: up/down arrow with percentage)
</div>
```

**Styling**:
- Glass-morphism card background
- Value: `--font-display`, `--font-size-3xl`, `--color-text-primary`
- Label: `--font-body`, `--font-size-sm`, `--color-text-secondary`
- Trend up: `--color-success`, trend down: `--color-error`
- Card padding: `--space-6`
- Min width: 200px

---

### HeatmapCell

**File**: `src/components/analytics/HeatmapCell.tsx`
**Status**: Planned (Phase 5)

**Description**: A single cell in the analytics heatmap grids (win rate, detection difficulty, etc.). Color intensity maps to the metric value.

**Structure**:
```
<td class="ww-heatmap-cell" style="--cell-intensity: {0-1}">
  <span class="ww-heatmap-cell__value">{formattedValue}</span>
  <span class="ww-heatmap-cell__count">n={count}</span> (on hover)
</td>
```

**Color scale**:
- Win rate heatmap: interpolate from `--color-bid-0` (low/blue) through `--color-bid-2` (mid/yellow) to `--color-bid-4` (high/red)
- Detection difficulty: interpolate from `--color-success` (easy to detect) to `--color-error` (hard to detect)
- Custom scales can be passed as props

**Behavior**:
- Hover: show tooltip with exact value, sample count, confidence interval
- Cell size: minimum 64px x 48px
- Value text: `--font-mono`, `--font-size-sm`
- Count text: `--font-mono`, `--font-size-2xs`, `--color-text-muted`

---

## Shared layout components

### Shell

**File**: `src/components/layout/Shell.tsx`

The application shell wrapping all pages. Provides:
- Navigation dock at the bottom (Dock component)
- Background atmosphere layer (Aurora or Particles based on context)
- Content area with max-width constraint
- Day/night phase context provider

### Dock (navigation)

**File**: `src/components/layout/Dock.tsx`
**React Bits**: Dock

Navigation items:
| Label | Icon | Route |
|-------|------|-------|
| Dashboard | Home | `/` |
| Games | List | `/games` |
| Analytics | Chart | `/analytics` |

Dock styling: glass-morphism background, positioned at bottom center, magnification effect on hover.

---

## Utility components

### GradientName

Wrapper around React Bits GradientText. Accepts a `profile` prop and automatically applies the correct gradient colors from tokens.

### PhaseIndicator

Displays current game phase with RotatingText animation during transitions. Uses day/night colors based on phase type.

### ConfidenceDots

5 dots showing confidence level (1-5). Filled dots use `--color-text-primary`, unfilled use `--color-border-subtle`.

### DeceptionLabel

Styled label for deception_self_label values. Color-coded:
- truthful: `--color-success`
- omission: `--color-warning`
- distortion: `--color-scarcity`
- fabrication: `--color-error`
- misdirection: `--color-reciprocity`
