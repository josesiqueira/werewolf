# Accessibility Requirements

Project: Werewolf AI Agents
Date: 2026-04-03

## Minimum standards

- WCAG 2.1 AA compliance across all pages
- All text meets 4.5:1 contrast ratio against its background (3:1 for large text, defined as 18px+ or 14px+ bold)
- All interactive elements are keyboard-navigable in logical tab order
- Focus indicators are visible and styled -- use a 2px outline in `--color-night-eerie` with 2px offset, not browser defaults
- Images have descriptive alt text; decorative images (portraits in non-interactive contexts, atmospheric backgrounds) use `alt=""`
- Form inputs have associated `<label>` elements
- Error messages are descriptive and programmatically linked to their fields via `aria-describedby`

## Dark theme contrast considerations

The dark background palette requires careful contrast management:

| Token | Value | Min contrast with `--color-text-primary` (#e2dfd8) |
|-------|-------|-----------------------------------------------------|
| `--color-bg-void` | #07070b | 14.2:1 -- passes AAA |
| `--color-bg-primary` | #0c0c14 | 12.8:1 -- passes AAA |
| `--color-bg-secondary` | #111119 | 11.5:1 -- passes AAA |
| `--color-bg-surface` | #181824 | 9.8:1 -- passes AAA |
| `--color-bg-elevated` | #1f1f2e | 8.1:1 -- passes AAA |

Secondary text (`--color-text-secondary`, #a09d95) on `--color-bg-surface` (#181824): 5.2:1 -- passes AA.

Muted text (`--color-text-muted`, #605e58) should only be used for non-essential decorative labels, never for information the user needs to read. Contrast against surface: 2.8:1 -- fails AA. Use only with `--font-size-lg` or larger where 3:1 is acceptable for decorative purposes.

## Profile color accessibility

Each profile color must be readable as text on the surface background. Minimum 4.5:1 ratio on `--color-bg-surface`:

| Profile | Color | Approx ratio on #181824 | Status |
|---------|-------|-------------------------|--------|
| Ethos | #6ea4d4 | 5.8:1 | Passes AA |
| Pathos | #c74b4b | 4.6:1 | Passes AA |
| Logos | #3a9e7e | 4.8:1 | Passes AA |
| Authority | #c9a227 | 6.1:1 | Passes AA |
| Reciprocity | #9b59b6 | 4.5:1 | Passes AA (borderline -- use light variant for small text) |
| Scarcity | #d4712a | 5.3:1 | Passes AA |
| Baseline | #7a7a7a | 3.8:1 | Use `--color-baseline-light` (#a0a0a0, 5.4:1) for text |

For ProfileBadge components using profile colors as background fills, use `--color-text-inverse` (#0c0c14) or white depending on which provides better contrast.

## Keyboard navigation

### Global shortcuts
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Move focus forward/backward |
| `Escape` | Close modal, dismiss overlay, deselect |
| `?` | Show keyboard shortcuts help (when not in text input) |

### Game replay page
| Key | Action |
|-----|--------|
| `Space` | Play / pause replay |
| `Left Arrow` | Previous phase |
| `Right Arrow` | Next phase |
| `Home` | Jump to game start |
| `End` | Jump to game end |
| `1-7` | Select player 1-7 for inspection |
| `Enter` | Open inspector for selected player |

### Timeline scrubber
- Arrow keys move between phases
- `Tab` moves to playback controls
- Playhead position announced via `aria-valuenow` and `aria-valuetext`
- Role: `slider` with `aria-label="Game timeline"`

### Data tables
- Arrow keys navigate between cells
- `Enter` activates the cell (opens game, selects filter)
- Column headers are `<th>` with `scope="col"`
- Sortable columns use `aria-sort` attribute

## Motion and animation

### `prefers-reduced-motion` handling

All animations must respect the user's motion preference. The `tokens.css` file sets all transition durations to `0ms` when `prefers-reduced-motion: reduce` is active.

Additional requirements:
- Aurora background: replaced with a static gradient
- Particles: hidden entirely
- TiltedCard: tilt effect disabled, hover shows flat highlight instead
- AnimatedList: items appear instantly without slide-in
- CountUp: shows final value immediately without counting animation
- BlurText: shows text immediately without blur-to-clear transition
- SplitText: shows text immediately without split animation
- VotingArrows: appear instantly without draw animation
- RotatingText: shows static text without rotation
- Beams: disabled, elimination shown with static color change

### Auto-playing content
- Chat replay does NOT auto-play; user must press Play
- No looping animations that cannot be paused
- Background atmospherics (Aurora, Particles) are subtle and non-distracting; they are purely decorative and hidden with reduced motion

### Animation duration limits
- UI feedback transitions (hover, focus, active): under 250ms
- Content transitions (panel swap, tab change): under 400ms
- Dramatic effects (elimination, phase change): under 1200ms
- No animation should block user interaction

## Screen readers

### Semantic HTML
- Use `<nav>` for navigation (dock, turn navigation, tab bars)
- Use `<main>` for primary content area
- Use `<section>` with `aria-labelledby` for major page sections
- Use `<article>` for individual game cards, chat messages
- Use `<aside>` for inspector panels
- Use `<header>` and `<footer>` for page-level landmarks
- Use `<table>`, `<thead>`, `<tbody>`, `<th>`, `<td>` for all tabular data (game list, heatmaps)

### ARIA usage
- Use `aria-label` on icon-only buttons (play, pause, next, previous)
- Use `aria-live="polite"` on:
  - Chat message feed (new messages announced)
  - Phase indicator (phase changes announced)
  - Status updates (elimination, vote results)
- Use `aria-live="assertive"` only for error messages
- Use `aria-expanded` on collapsible panels
- Use `aria-selected` on active tab in tab bars
- Use `aria-current="page"` on active navigation item in dock
- Player cards: `role="button"` with `aria-label` including player name, role (if revealed), profile, and alive/dead status

### Data visualization accessibility
- Heatmap cells: include `aria-label` with full description (e.g., "Ethos profile, werewolf role: 62% win rate, 45 games")
- Charts: provide a text summary or data table alternative accessible via a "View as table" toggle
- Voting arrows: provide an accessible text list of votes as an alternative (e.g., "Player 1 voted for Player 3")
- Color-coded elements must also use a secondary indicator (icon, pattern, or text label) so information is not conveyed by color alone

### Profile identification
Never rely solely on color to identify a persuasion profile. Every profile-colored element must also include:
- A text label (the profile name), OR
- An icon or pattern unique to that profile, OR
- Both

The ProfileBadge component always includes the text label. In compact views (heatmap cells, small charts), abbreviations are acceptable: ETH, PAT, LOG, AUT, REC, SCA, BAS.

## Testing requirements

- Run axe-core automated checks on all pages
- Test all pages with keyboard-only navigation
- Test game replay with screen reader (VoiceOver or NVDA) to verify:
  - Phase changes are announced
  - Player selection is announced with full context
  - Chat messages are readable in sequence
  - Vote results are announced
- Verify all profile colors pass contrast requirements using a contrast checker tool
- Test with `prefers-reduced-motion: reduce` enabled to verify all animations are suppressed
