# Werewolf AI Agents — Implementation Spec

> **Context**: This is a secondary project inside the Manipulative AI research umbrella (repo: `josesiqueira/manipulative-ai`). The main project (SYNTHETICA) studies AI-to-human persuasion around political orientations. This one studies **AI-to-AI manipulation and persuasion** using a Werewolf social deduction game where all players are LLM agents. No humans play — humans observe and analyze.

> **Audience for this doc**: Claude Code, which will use this to generate a phased implementation plan via the phase-runner template.

> **Supporting docs** (for research context, not implementation):
> - `WEREWOLF-RESEARCH.md` — literature review and best practices
> - `WEREWOLF-REFERENCES.md` — citations and implementation techniques from existing projects
> - `WEREWOLF-RESEARCH-GAPS.md` — novelty, research questions, positioning

---

## What Makes This Project Different

This is NOT a generic Werewolf AI benchmark. It is a **persuasion technique laboratory** that uses Werewolf as its testbed.

Each AI agent is assigned a specific, academically grounded **persuasion technique profile** (e.g., logic-based, emotion-based, authority-based) as a steerable behavioral input. By systematically varying which agents get which techniques across hundreds of games, we study:

- **RQ1**: Which persuasion techniques are most effective at influencing other AI agents' voting behavior?
- **RQ2**: Which techniques are hardest for other AI agents to detect as manipulative?
- **RQ3**: How does the interaction between game role and persuasion profile affect outcomes?
- **RQ4**: Does having a technique document produce measurably different behavior vs. baseline agents?

The persuasion technique files are the **independent variable**. Everything else is infrastructure to measure their effect.

---

## The Game

Classic Werewolf with these specific rules:

**Phases** alternate: Night → Day → Vote → repeat.

**Night**: Werewolves secretly choose a villager to kill. Seer investigates one player's role. Doctor protects one player. All via private LLM calls — no other agent sees these.

**Mayor Election** (before Day 1 only): All players may campaign. Everyone votes. Mayor gets tie-break power on day votes. If the mayor dies, they name a successor. This solves the "flat Day 1" problem identified in the literature.

**Day**: Surviving agents discuss openly using a **bidding-based turn-taking** system. Before each speaking slot, all agents bid 0-4 on urgency (0 = observe, 1 = general thoughts, 2 = critical info, 3 = urgent, 4 = must respond to direct address). Highest bidder speaks. Ties broken by mention priority (agents referenced in previous turn get priority). **Debate cap: 8-10 turns per day phase.**

**Vote**: After debate, all surviving players vote to eliminate one player. Majority wins. Mayor breaks ties. Eliminated player's role is revealed.

**Win conditions**: Villagers win when all werewolves are dead. Werewolves win when they reach numerical parity with villagers.

**Game cap**: Maximum 10 day/night cycles. Games that don't resolve are discarded.

**7 players per game:**
- 2 Werewolves — know each other, coordinate kills at night, must deceive during day
- 1 Seer — learns one player's true role each night
- 1 Doctor — protects one player from death each night
- 3 Villagers — no special ability, must deduce from discussion

**The Moderator is NOT an LLM.** It is a deterministic state machine that manages phase transitions, validates actions, resolves conflicts (e.g., doctor saves the wolf target), announces deaths, and checks win conditions.


### Game Loop (Pseudocode)

```
game = initialize_game(players=7, roles=[wolf, wolf, seer, doctor, villager, villager, villager])
assign_persuasion_profiles(game)  # each agent gets a TECHNIQUE-*.md file (or none for baseline)
assign_personas(game)             # each agent gets a distinct personality

# Mayor Election
for agent in game.alive_agents:
    speech = agent.generate(phase="mayor_campaign", game_state=game.state)
    log(speech)
for agent in game.alive_agents:
    vote = agent.generate(phase="mayor_vote", game_state=game.state)
    log(vote)
game.set_mayor(tally_votes())

while not game.is_over():
    # === NIGHT PHASE ===
    wolf_target = wolves.generate(phase="night_kill", game_state=game.wolf_state)
    seer_target = seer.generate(phase="night_investigate", game_state=game.seer_state)
    doctor_target = doctor.generate(phase="night_protect", game_state=game.doctor_state)
    
    resolve_night(wolf_target, seer_target, doctor_target)
    log_night_actions()
    announce_deaths()
    check_win_condition()

    # === DAY PHASE (bidding-based) ===
    for turn in range(MAX_DEBATE_TURNS):  # 8-10
        bids = {}
        for agent in game.alive_agents:
            bid = agent.generate(phase="bid", game_state=game.state, history=debate_history)
            bids[agent] = bid.bid_level
        
        speaker = select_speaker(bids, mention_priority=last_turn_mentions)
        statement = speaker.generate(phase="day_speech", game_state=game.state, history=debate_history)
        validate_output(statement, game.state)
        log(statement)  # logs all JSON fields including private_reasoning, technique_self_label, etc.
        debate_history.append(statement.public_statement)
    
    # === VOTE PHASE ===
    votes = {}
    for agent in game.alive_agents:
        vote = agent.generate(phase="vote", game_state=game.state, history=debate_history)
        votes[agent] = vote.vote_target
        log(vote)
    
    eliminated = tally_votes(votes, mayor_tiebreak=game.mayor)
    reveal_role(eliminated)
    check_win_condition()

save_game(game)
compute_derived_metrics(game)
```

---

## Tech Stack

- **LLM**: OpenAI GPT 5.4 (API key available)
- **Frontend**: Next.js 14 with components from [reactbits.dev](https://reactbits.dev/)
- **Backend**: FastAPI + SQLAlchemy
- **Database**: PostgreSQL (via CSC Pukki)
- **Deployment**: CSC Rahti (OpenShift), same infrastructure as SYNTHETICA
- **Repo**: Inside `josesiqueira/manipulative-ai`
- **Implementation**: Claude Code phase-runner template

---

## Agent Architecture

### Prompt Structure (per LLM API call)

```
SYSTEM MESSAGE (cached across turns for the same agent in the same game):
├── Game rules (~200 tokens)
├── Role assignment + private info ("You are a Werewolf. Player 4 is your teammate.") (~100 tokens)
├── Persona description (~200 tokens)
├── Output format instructions (JSON schema) (~150 tokens)
└── General behavioral instructions (~100 tokens)
    └── Includes: "Adapt persuasion techniques to the situation. Do not copy example phrases verbatim."
Total system message: ~750 tokens (cached after first call)

USER MESSAGE (changes every turn):
├── Persuasion technique document - the assigned TECHNIQUE-*.md file (~800-1200 tokens)
│   (ABSENT for baseline condition — this is the control)
├── Current game state - structured object (~300-500 tokens)
│   ├── alive_players: [list with roles if known]
│   ├── voting_history: {round: {voter: target}}
│   ├── eliminated_players: [{player, role, round}]
│   ├── night_results: "Player X was killed" / "Nobody died"
│   ├── mayor: player_id
│   └── current_phase: "day_speech" | "vote" | "bid" | etc.
├── Conversation history (~500-2000 tokens)
│   ├── Last 2-3 rounds: full dialogue
│   └── Earlier rounds: summarized (key accusations, vote outcomes)
└── Turn instruction: "It is your turn to speak. Produce your response as JSON."
Total user message: ~1,600-3,700 tokens
```

### Expected LLM Response (JSON)

```json
{
  "private_reasoning": "Internal chain-of-thought, never shared with other agents",
  "public_statement": "What the agent says to the group",
  "vote_target": "player_id | null",
  "bid_level": 0-4,
  "technique_self_label": "Which technique section the agent is applying (e.g., 'ethos-accusing', 'logos-defending')",
  "deception_self_label": "truthful | omission | distortion | fabrication | misdirection",
  "confidence": 1-5
}
```

The `technique_self_label` is our novel contribution — it connects the persuasion input to the deception output at the statement level.

### Personas

Each agent gets a distinct persona (~200 tokens) independent of role and technique. Examples: analytical/measured, aggressive/confrontational, quiet/observant, warm/collaborative, suspicious/paranoid, diplomatic/balanced, blunt/direct.

Assigned per-game, stays constant. Interacts with persuasion technique (warm persona + logos sounds different from blunt persona + logos).

### Memory Strategy

- **Structured game state** (always provided): alive players, voting history, revealed roles, night results, mayor
- **Last 2-3 rounds**: Full dialogue transcript
- **Earlier rounds**: Summarized (key accusations, vote outcomes, eliminations)
- **Keep total context under 80%** of model's context window

### Error Handling & Retries

- **API failures**: Retry up to 3 times with exponential backoff (1s, 3s, 9s). After 3 failures, substitute conservative default.
- **Malformed JSON**: Attempt repair (strip markdown fences, fix commas). If still invalid, use defaults.
- **Invalid game actions**: Vote for dead player → random alive player. Bid outside 0-4 → clamp. Missing fields → fill defaults.
- **Timeout**: 60s per API call. On timeout, use defaults.
- **Conservative defaults**: bid=1, generic public statement, random valid vote target, deception_self_label="truthful", confidence=3.
- **Game-level quality**: If >30% of turns use defaults, flag game as degraded.

### Output Validation

Every agent output is validated against game state:
- Vote target must be an alive player (not self)
- Bid must be 0-4
- Public statement must not reference game events that didn't occur
- Werewolf public statement must not leak night-phase information
- Deception self-label must be from valid taxonomy
- technique_self_label must reference a section from the assigned technique file (or "none" for baseline)

---

## Persuasion Technique System

### The Six Profiles + Baseline

Each profile is a `.md` file with four context-aware sections. Files in `persuasion-techniques/`:

| Profile | File | Academic Source | Core Mechanism |
|---------|------|----------------|----------------|
| Ethos | `TECHNIQUE-ETHOS.md` | Aristotle's Rhetoric | Credibility, track record, transparency |
| Pathos | `TECHNIQUE-PATHOS.md` | Aristotle's Rhetoric | Emotional stakes, bonds, fear/hope/solidarity |
| Logos | `TECHNIQUE-LOGOS.md` | Aristotle's Rhetoric | Evidence chains, contradiction detection, deduction |
| Authority + Social Proof | `TECHNIQUE-AUTHORITY-SOCIALPROOF.md` | Cialdini's Principles | Positional power, consensus pressure, majority |
| Reciprocity + Liking | `TECHNIQUE-RECIPROCITY-LIKING.md` | Cialdini's Principles | Rapport, favor exchange, social debts |
| Scarcity + Commitment | `TECHNIQUE-SCARCITY-COMMITMENT.md` | Cialdini's Principles | Urgency, consistency traps, loss aversion |
| Baseline | *No file injected* | N/A | Agent uses only role description, no technique guidance |

### Profile Assignment Strategy

Across 200-500 games, assignment uses a **balanced randomization**:
- Each profile appears roughly equally across all games
- Each profile is paired with each role roughly equally
- Within a game, agents may have different profiles (mixed) or same (homogeneous)
- Assignment randomized within balancing constraints
- Database records which agent received which profile in every game

### Baseline Condition

No technique document injected. Agent receives only: game state + conversation history + turn instruction. System prompt still includes role, persona, and output format. This is the control for RQ4.

---

## Database Schema

```sql
-- Core tables

games (
    id              UUID PRIMARY KEY,
    created_at      TIMESTAMP,
    status          VARCHAR  -- pending | running | completed | discarded
    winner          VARCHAR  -- villagers | werewolves | null
    rounds_played   INT,
    total_turns     INT,
    is_degraded     BOOLEAN,
    config          JSONB    -- player_count, debate_cap, etc.
)

players (
    id                  UUID PRIMARY KEY,
    game_id             UUID REFERENCES games,
    agent_name          VARCHAR,
    role                VARCHAR  -- werewolf | villager | seer | doctor
    persona             VARCHAR,
    persuasion_profile  VARCHAR  -- ethos | pathos | logos | authority_socialproof | reciprocity_liking | scarcity_commitment | baseline
    is_mayor            BOOLEAN,
    eliminated_round    INT NULL,
    survived            BOOLEAN,
    character_image     VARCHAR
)

turns (
    id                      UUID PRIMARY KEY,
    game_id                 UUID REFERENCES games,
    player_id               UUID REFERENCES players,
    round_number            INT,
    phase                   VARCHAR  -- mayor_campaign | mayor_vote | night_kill | night_investigate | night_protect | day_bid | day_speech | vote
    prompt_sent             TEXT,
    completion_received     TEXT,
    private_reasoning       TEXT,
    public_statement        TEXT,
    vote_target             UUID REFERENCES players NULL,
    bid_level               INT NULL,
    technique_self_label    VARCHAR NULL,
    deception_self_label    VARCHAR NULL,
    confidence              INT NULL,
    is_default_response     BOOLEAN,
    token_count_input       INT,
    token_count_output      INT,
    latency_ms              INT,
    created_at              TIMESTAMP
)

night_actions (
    id              UUID PRIMARY KEY,
    game_id         UUID REFERENCES games,
    round_number    INT,
    wolf_target     UUID REFERENCES players,
    doctor_target   UUID REFERENCES players,
    seer_target     UUID REFERENCES players,
    seer_result     VARCHAR,
    kill_successful BOOLEAN,
    created_at      TIMESTAMP
)

votes (
    id                  UUID PRIMARY KEY,
    game_id             UUID REFERENCES games,
    round_number        INT,
    voter               UUID REFERENCES players,
    target              UUID REFERENCES players,
    is_mayor_tiebreak   BOOLEAN,
    created_at          TIMESTAMP
)

game_events (
    id              UUID PRIMARY KEY,
    game_id         UUID REFERENCES games,
    round_number    INT,
    event_type      VARCHAR  -- death | elimination | role_reveal | mayor_elected | mayor_succession | game_start | game_end
    details         JSONB,
    created_at      TIMESTAMP
)
```

---

## UI / Visual Design

> **Design philosophy**: This should look and feel like a premium, cinematic game interface — NOT generic AI slop with plain tables and default styling. Use React Bits (`reactbits.dev`) components throughout for animated, polished interactions. The UI is also a presentation asset for research talks and demos.

### Shared Design System with SYNTHETICA

Both projects share: layout/nav shell, theming/color tokens, conversation viewer component, data tables, Tailwind config. Domain-specific views are unique. Consistent Tailwind + shared React components is enough.

### React Bits Components to Use

Install via: `npx shadcn@latest add @react-bits/<ComponentName>-TS-TW`

**Backgrounds (set the atmosphere):**
- **Aurora** — animated aurora borealis effect for the main game view background during night phase. Dark, moody, atmospheric.
- **Particles** — subtle floating particles for the day phase background. Lighter, airier feel.
- **Beams** — light beam effects for dramatic moments (eliminations, role reveals, game over screen).

**Text Animations (make the game feel alive):**
- **SplitText** — for agent names and role reveals. Text splits apart and reassembles with animation.
- **BlurText** — for the "private reasoning" panel in the agent inspector. Text appears with a blur-to-focus effect, reinforcing that this is hidden/secret information.
- **CountUp** — for the analytics dashboard numbers (win rates, game counts, survival stats). Numbers animate up from zero.
- **GradientText** — for player names colored by their persuasion profile. Each profile gets a signature gradient.
- **RotatingText** — for the game phase indicator cycling between "Night Phase" / "Day Phase" / "Voting".
- **TextPressure** — for the game title / landing page header. Interactive text that responds to cursor.

**Animations (interactive elements):**
- **Magnet** — for player cards in the circular table layout. Cards subtly pull toward the cursor as you hover, creating a tactile feel.
- **AnimatedList** — for the chat log / debate transcript. Messages animate in one by one as the game replays.
- **BlobCursor** — as an optional cursor effect on the game view for presentation/demo mode.
- **FollowCursor** — for the voting visualization. Vote arrows that track from voter to target with a following animation.

**Components (functional UI elements):**
- **TiltedCard** — for player cards around the table. Slight 3D tilt on hover showing character portrait, name, role, status.
- **Dock** — for the main navigation between Game View, Admin Panel, Analytics, and Settings. macOS-style dock with magnification.
- **InfiniteMenu** — for browsing the game list in a visually engaging way (alternative to a plain table for the public-facing view).
- **AnimatedContent** — for panel transitions. When switching between game replay, agent inspector, and analytics, content animates in/out rather than hard-cutting.
- **StackedCards** — for the game history / recent games overview. Games stack visually with the most recent on top.
- **SpotlightCard** — for the agent inspector. When you click an agent, their card gets a spotlight/glow effect highlighting them.
- **Lanyard** — for showing agent badges (role + persuasion profile) with a physical badge/lanyard aesthetic.

### Game Visualization

- Player cards arranged in a **circle (table seating)** using **TiltedCard** with **Magnet** hover effects: character portrait, name, role (if revealed), status (alive/dead/eliminated), persuasion profile gradient badge
- **Day/night visual toggle**: swap between **Aurora** (night) and **Particles** (day) backgrounds with smooth crossfade
- Chat log panel using **AnimatedList** — messages animate in during replay, each attributed to the speaker's character portrait
- Voting visualization — animated arrows from voter to target using **FollowCursor** style tracking
- Bidding indicator showing urgency levels as a heat bar per player (0=cool, 4=glowing red)
- Elimination moments use **Beams** + **SplitText** for dramatic role reveal animation
- Game over screen with **CountUp** showing final stats and **GradientText** for the winning faction

### Admin Panel (research interface)

**Game list** — table with: game ID, date, status, winner, rounds, profiles used, degraded flag. Filterable and sortable. Use **StackedCards** for a visual browse mode alongside the data table.

**Game replay** — step-through timeline with **AnimatedContent** transitions between phases. Player cards update status. Chat log advances with **AnimatedList**. Scrubber timeline at the bottom.

**Agent inspector** — click any agent at any turn, **SpotlightCard** highlights them:
- LEFT: private reasoning (revealed with **BlurText** animation — reinforces "this was hidden")
- RIGHT: public statement (normal text, what the group saw)
- BOTTOM: metadata badges showing technique_self_label, deception_self_label, confidence, bid_level, assigned profile

**Cross-game analytics:**
- Win rate by faction × profile (heatmap with animated transitions)
- Survival duration by role × profile (bar charts with **CountUp** on values)
- Detection difficulty matrix
- Technique adherence rates
- Vote-swing analysis
- Accusation graph visualization (force-directed graph with animated edges)

### Character Art

Generate ~10 stylized 2D character portraits using ChatGPT image generation. Each agent gets a persistent visual identity across games. Style: illustrated, slightly dark/moody aesthetic matching the Werewolf theme — NOT photorealistic, NOT cartoonish. Think: stylized card game portraits.

Each portrait displayed inside a **TiltedCard** with the player's name in **GradientText** colored by their persuasion profile:
- Ethos → blue/silver gradient
- Pathos → red/warm gradient
- Logos → green/teal gradient
- Authority + Social Proof → gold/amber gradient
- Reciprocity + Liking → purple/pink gradient
- Scarcity + Commitment → orange/fire gradient
- Baseline → neutral gray

---

## Data Capture & Metrics

### Per-Turn Logging

Every LLM interaction stored in `turns` table with full prompt/completion. Also exported as NDJSON.

### Derived Metrics

| Metric | Description | Research Question |
|--------|-------------|-------------------|
| Win rate by faction × profile | Which techniques help which faction | RQ1 |
| Survival duration by role × profile | Which techniques help survival | RQ1, RQ3 |
| Vote-swing per message | Which statements changed votes | RQ1 |
| Deception index | Private reasoning vs public statement gap | RQ2 |
| Detection difficulty matrix | Technique × deception type → peer suspicion | RQ2 |
| Technique adherence rate | Self-label vs assigned profile match | RQ4 |
| Baseline comparison | Profile agents vs baseline on all metrics | RQ4 |
| Accusation graph | Who accused whom, by profile | RQ3 |
| Bandwagon dynamics | Vote cascade timing | RQ1 |
| Bus-throwing rate | Wolf voting against teammate | RQ3 |

### Statistical Design

**200-500 games**. Balanced profile assignment. Report: Mean ± SEM, 95% CI. ANOVA or mixed-effects models for interaction effects.

---

## Previous Attempt Lessons

An earlier attempt (pre-Opus 4.6) produced "AI slop." Fixes incorporated:
- Strong differentiated personas (from SYNTHETICA)
- Structured game state management — evidence, not vibes
- Private reasoning step — forces strategizing before speaking
- Evidence-based discussion — prompts reference specific game events
- Output constraints — JSON schema prevents freeform mush
- Persuasion technique grounding — documented strategies, not generic instructions

---

## Suggested Phasing for Claude Code

**Phase 1: Core game engine**
- Deterministic game master (state machine with all phases)
- Game loop: night → mayor election → day bidding → debate → vote
- PostgreSQL schema and SQLAlchemy models
- Basic agent interface (send prompt, receive JSON, validate, store)
- NDJSON export

**Phase 2: Agent system**
- Prompt construction (system message + dynamic user message)
- Persuasion technique file loading and injection
- Persona assignment
- Output validation and repair
- Error handling, retries, timeouts
- Memory management (context windowing, round summarization)

**Phase 3: Game runner**
- Batch execution (run N games with balanced profile assignment)
- Profile assignment strategy implementation
- Game-level quality checks (degraded flag)
- Progress tracking and resumption after interruptions

**Phase 4: Admin panel + UI**
- Game list view with filters + StackedCards browse mode
- Game replay with AnimatedList chat, AnimatedContent transitions, Aurora/Particles day-night backgrounds
- Agent inspector with SpotlightCard highlight and BlurText private reasoning reveal
- Player cards using TiltedCard + Magnet hover + GradientText profile colors
- Navigation using Dock component
- Shared design system components (with SYNTHETICA)
- Character portraits inside TiltedCards with profile-colored gradients
- Install React Bits components via: `npx shadcn@latest add @react-bits/<Component>-TS-TW`

**Phase 5: Analytics and metrics**
- Derived metric computation (all metrics from table)
- Visualization components (heatmaps, accusation graphs, vote-swing)
- Export for statistical analysis (CSV/JSON)
- Cross-game analytics dashboard