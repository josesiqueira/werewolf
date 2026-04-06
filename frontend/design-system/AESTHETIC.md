# Design Aesthetic

Project: Werewolf AI Agents
Date: 2026-04-03

## Direction

A dark, atmospheric interface evoking a gothic village shrouded in fog and moonlight. The UI should feel like peering through a window into a tense midnight gathering -- shadowy, layered, and quietly unsettling. Information is revealed through glass-like surfaces that float over deep, near-black backgrounds, with each persuasion profile carrying its own distinct color signature like colored lanterns in the dark.

## Rationale

This is a research observation tool for watching AI agents manipulate each other in a social deduction game. The gothic village aesthetic reinforces the game's themes: hidden identities, deception, suspicion, and elimination. The dark palette keeps the focus on data and game events while the atmospheric effects (glows, particles, aurora) create a sense that something lurks beneath the surface. Researchers will spend long sessions reviewing games, so the dark theme reduces eye strain while the distinctive profile colors make pattern recognition across hundreds of games immediate and intuitive.

## Key choices

- **Theme**: Dark, with day/night phase variations
- **Mood**: Gothic atmospheric -- a midnight village square, fog-shrouded, lit by firelight and moonlight
- **Color strategy**: Near-black base with 7 distinct profile colors as the primary differentiators. Day phases shift toward muted warm tones (misty morning); night phases deepen into midnight blues with eerie edge lighting.
- **Typography pairing**: Cinzel (display) + Nunito Sans (body) -- Cinzel's serif letterforms evoke old-world village proclamations and court proceedings, while Nunito Sans provides clean readability for data-dense panels. JetBrains Mono for code and raw data.
- **Layout approach**: Dense information design with glass-morphism panels. Game replay uses a central circular player arrangement surrounded by contextual panels. Analytics uses grid-based heatmaps and charts.
- **Signature element**: Profile-colored atmospheric glows. Each persuasion profile has a unique color that appears as subtle glows on player cards, name highlights, badges, and heatmap cells. When viewing a game, the distribution of colored light across the interface tells a story at a glance.

## Day/Night visual modes

### Day mode (misty morning)
- Background shifts from pure black to a dark warm gray (#14120f)
- Subtle warm particle effects (dust motes, soft light rays)
- Borders gain a faint warm tint
- Text warms slightly toward parchment tones
- Muted, diffused feeling -- information is "public" but still shadowed

### Night mode (deep midnight)
- Background deepens to blue-black (#080818)
- Aurora component provides slow-moving northern-lights effect in background
- Borders cool to blue-gray
- Moon glow effect on elevated surfaces
- Eerie, watchful atmosphere -- secrets are being exchanged

### Transitions between modes
- Crossfade over 1.2 seconds using `--transition-phase`
- Background color, border tints, and atmospheric effects all transition together
- Player cards subtly shift their shadow colors

## Glass morphism treatment

Cards and panels use a layered glass effect:
- Background: `rgba(18, 18, 30, 0.60)` with `backdrop-filter: blur(16px)`
- Border: `1px solid rgba(255, 255, 255, 0.06)`
- On hover, background opacity increases to 0.70
- Profile-colored cards add a faint profile-colored border glow on the bottom or left edge
- Dead players' cards reduce opacity and desaturate

## React Bits components

The following React Bits components define the interaction and motion language:

| Component | Usage |
|-----------|-------|
| **Aurora** | Night phase background atmosphere |
| **Particles** | Day phase floating dust motes |
| **TiltedCard** | Player cards with 3D perspective hover |
| **Magnet** | Cursor attraction on player cards |
| **AnimatedList** | Chat message feed during replay |
| **AnimatedContent** | Phase transition content swaps |
| **GradientText** | Player names colored by profile |
| **SplitText** | Role reveal on elimination |
| **BlurText** | Private reasoning reveal in inspector |
| **RotatingText** | Phase headers (Night / Day / Vote) |
| **CountUp** | Dashboard statistics |
| **SpotlightCard** | Selected agent highlight in inspector |
| **StackedCards** | Alternative game browse mode |
| **Dock** | Main navigation bar |
| **FollowCursor** | Voting arrow animation style |
| **Beams** | Elimination dramatic effect |

## References

- The Witch's House (RPG Maker) -- dark forest village atmosphere, muted palette
- Darkest Dungeon UI -- gothic typography, stress/status indicators, dark panels
- Bloodborne menu design -- ornate but readable, dark with warm accent lighting
- Notion's dark mode -- clean data presentation on dark surfaces (for the analytics side)
- D3 observable notebooks -- dense analytical layouts with clear color coding

## Anti-patterns (DO NOT use)

- White or light backgrounds anywhere in the application
- Purple-to-blue gradient hero sections
- Rounded-corner cards on white with drop shadows (the "SaaS look")
- Inter, Roboto, or Arial as primary fonts
- Generic wave dividers or blob decorations
- Bright neon colors at full saturation (all profile colors are slightly muted/desaturated)
- Gratuitous parallax scrolling
- Loading spinners without context -- always show what is loading
- Generic placeholder illustrations
- Rainbow gradients or pride-flag-style color bars for profile visualization -- each profile has its own specific, intentional color pair
