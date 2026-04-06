# Project Specification — Werewolf AI Agents

> A persuasion technique laboratory using Werewolf as its testbed. All players are LLM agents assigned academically grounded persuasion profiles. No humans play — humans observe and analyze.

## Overview

This project implements a multi-agent Werewolf social deduction game where all 7 players are LLM agents. Each agent is assigned a specific persuasion technique profile (or none for baseline). By varying assignments across 200-500 games, we study which persuasion techniques are most effective at AI-to-AI manipulation.

Part of the Manipulative AI research umbrella (repo: `josesiqueira/manipulative-ai`). The main project (SYNTHETICA) studies AI-to-human persuasion. This one studies **AI-to-AI persuasion**.

### Research Questions
- **RQ1**: Which persuasion techniques most effectively influence other AI agents' voting behavior?
- **RQ2**: Which techniques are hardest for other AI agents to detect as manipulative?
- **RQ3**: How does the interaction between game role and persuasion profile affect outcomes?
- **RQ4**: Does having a technique document produce measurably different behavior vs. baseline agents?

## Stack
- Language: Python 3.12 (backend), TypeScript (frontend)
- Framework: FastAPI + SQLAlchemy (backend), Next.js 14 (frontend)
- Styling: Tailwind CSS + reactbits.dev components
- Testing: pytest (backend), Vitest (frontend), Playwright (E2E)
- Database: PostgreSQL (via CSC Pukki)
- Hosting: CSC Rahti (OpenShift)
- LLM: OpenAI GPT 5.4

## Features

### Feature 1: Deterministic Game Master (State Machine)
**Description**: A deterministic moderator (NOT an LLM) that manages the full game loop: phase transitions, action validation, conflict resolution, death announcements, and win condition checks.
**Acceptance criteria**:
- [ ] Game initializes with 7 players: 2 werewolves, 1 seer, 1 doctor, 3 villagers
- [ ] Phases cycle correctly: Mayor Election → (Night → Day → Vote) repeat
- [ ] Night phase: werewolves choose kill target, seer investigates, doctor protects — all private
- [ ] Doctor save resolves correctly (kill_successful = false when doctor protects wolf target)
- [ ] Mayor election: all players campaign, all vote, winner gets tie-break power
- [ ] Mayor succession: if mayor dies, they name a successor
- [ ] Day phase uses bidding-based turn-taking (bid 0-4, highest speaks, ties broken by mention priority)
- [ ] Debate capped at 8-10 turns per day phase
- [ ] Vote phase: majority wins, mayor breaks ties, eliminated player's role revealed
- [ ] Win conditions: villagers win when all wolves dead; wolves win at numerical parity
- [ ] Game cap: maximum 10 day/night cycles, unresolved games marked as discarded
- [ ] All state transitions are deterministic — no LLM calls in the moderator

### Feature 2: Agent Interface & Prompt System
**Description**: System for constructing prompts, calling the LLM API, parsing structured JSON responses, validating outputs, and handling errors.
**Acceptance criteria**:
- [ ] System message (~750 tokens): game rules + role assignment + persona + output format + behavioral instructions (cached per agent per game)
- [ ] User message (~1600-3700 tokens): persuasion technique doc (if not baseline) + current game state + conversation history + turn instruction
- [ ] Memory management: last 2-3 rounds full transcript, earlier rounds summarized, total context under 80% of model window
- [ ] Response parsed as JSON with fields: private_reasoning, public_statement, vote_target, bid_level, technique_self_label, deception_self_label, confidence
- [ ] Output validation: vote target must be alive (not self), bid 0-4, deception_self_label from valid taxonomy, technique_self_label references assigned profile sections
- [ ] Werewolf public statements must not leak night-phase information
- [ ] Malformed JSON repair: strip markdown fences, fix commas; if still invalid, use defaults
- [ ] Invalid game actions corrected: dead vote target → random alive; bid outside 0-4 → clamp; missing fields → defaults
- [ ] API retry: 3 attempts with exponential backoff (1s, 3s, 9s); after 3 failures, use conservative defaults
- [ ] Timeout: 60s per API call
- [ ] Conservative defaults: bid=1, generic public statement, random valid vote target, deception_self_label="truthful", confidence=3
- [ ] If >30% of turns use defaults, flag game as degraded

### Feature 3: Persuasion Technique System
**Description**: Loading and injection of 6 persuasion technique profiles (+ baseline control) into agent prompts. Balanced randomized assignment across games.
**Acceptance criteria**:
- [ ] 6 technique files loaded from `persuasion-techniques/`: TECHNIQUE-ETHOS.md, TECHNIQUE-PATHOS.md, TECHNIQUE-LOGOS.md, TECHNIQUE-AUTHORITY-SOCIALPROOF.md, TECHNIQUE-RECIPROCITY-LIKING.md, TECHNIQUE-SCARCITY-COMMITMENT.md
- [ ] Baseline condition: no technique file injected, agent uses only role + persona + game state
- [ ] Balanced randomization: each profile appears roughly equally across all games; each profile paired with each role roughly equally
- [ ] Database records which agent received which profile in every game
- [ ] Persona assignment: 7 distinct personas (~200 tokens each) assigned per-game, constant throughout game

### Feature 4: Batch Game Runner
**Description**: Orchestration system to run N games with balanced profile assignment, quality checks, progress tracking, and resumption.
**Acceptance criteria**:
- [ ] Run N games (configurable, target 200-500) with balanced profile assignment strategy
- [ ] Profile assignment balancing: each profile × role combination appears roughly equally
- [ ] Game-level quality check: flag games where >30% turns use defaults as degraded
- [ ] Progress tracking: current game number, completion percentage, estimated time remaining
- [ ] Resumption after interruption: pick up from last incomplete game
- [ ] NDJSON export of all turn data
- [ ] Concurrent game execution (configurable parallelism)

### Feature 5: Admin Panel — Game List & Replay
**Description**: Web interface for viewing all games and replaying individual games step-by-step.
**Acceptance criteria**:
- [ ] Game list table: game ID, date, status, winner, rounds, profiles used, degraded flag
- [ ] Filterable by: status, winner faction, profiles used, degraded
- [ ] Game replay: step-through timeline, scrub between phases
- [ ] Player cards in circle layout: character portrait, name, role (if revealed), alive/dead status, persuasion profile badge
- [ ] Day/night visual toggle with atmosphere change
- [ ] Chat log panel with debate in real time or replay mode
- [ ] Voting visualization: who voted for whom
- [ ] Bidding indicator showing urgency levels

### Feature 6: Agent Inspector
**Description**: Detailed view of any agent at any turn, showing private reasoning alongside public behavior.
**Acceptance criteria**:
- [ ] Click any agent at any turn in the replay
- [ ] LEFT panel: private_reasoning
- [ ] RIGHT panel: public_statement
- [ ] BOTTOM bar: technique_self_label, deception_self_label, confidence, bid_level, assigned profile
- [ ] Navigation between turns for the same agent

### Feature 7: Cross-Game Analytics Dashboard
**Description**: Statistical visualizations across all completed games to answer research questions.
**Acceptance criteria**:
- [ ] Win rate by faction × profile (heatmap) — RQ1
- [ ] Survival duration by role × profile — RQ1, RQ3
- [ ] Vote-swing per message analysis — RQ1
- [ ] Deception index: private reasoning vs public statement gap — RQ2
- [ ] Detection difficulty matrix: technique × deception type → peer suspicion — RQ2
- [ ] Technique adherence rate: self-label vs assigned profile match — RQ4
- [ ] Baseline comparison: profile agents vs baseline on all metrics — RQ4
- [ ] Accusation graph: who accused whom, by profile — RQ3
- [ ] Bandwagon dynamics: vote cascade timing — RQ1
- [ ] Bus-throwing rate: wolf voting against teammate — RQ3
- [ ] Export for statistical analysis (CSV/JSON)

### Feature 8: Shared Design System with SYNTHETICA
**Description**: Consistent visual language shared between this project and SYNTHETICA.
**Acceptance criteria**:
- [ ] Shared: layout/nav shell, theming/color tokens, conversation viewer, data tables, Tailwind config
- [ ] ~10 stylized 2D character portraits (ChatGPT-generated), persistent identity per agent
- [ ] reactbits.dev: animated transitions, micro-interactions
- [ ] Responsive: desktop and mobile layouts

## Pages / Routes

### Frontend
- `/` — Dashboard: overview of game runs, quick stats
- `/games` — Game list with filters
- `/games/:id` — Game replay with step-through timeline
- `/games/:id/agents/:agentId` — Agent inspector
- `/analytics` — Cross-game analytics dashboard

### API
- `POST /api/games` — Start a new game or batch of games
- `GET /api/games` — List games with filters
- `GET /api/games/:id` — Get full game state
- `GET /api/games/:id/turns` — Get all turns for a game
- `GET /api/games/:id/replay` — Get replay data (phases, events, turns in order)
- `POST /api/batch` — Start batch execution
- `GET /api/batch/:id/status` — Batch progress
- `GET /api/analytics/winrates` — Win rate data
- `GET /api/analytics/survival` — Survival duration data
- `GET /api/analytics/techniques` — Technique effectiveness data
- `GET /api/export/:format` — Export data (CSV/JSON/NDJSON)

## Data model

```sql
games (
    id UUID PK, created_at TIMESTAMP, status VARCHAR, winner VARCHAR,
    rounds_played INT, total_turns INT, is_degraded BOOLEAN, config JSONB
)

players (
    id UUID PK, game_id UUID FK, agent_name VARCHAR, role VARCHAR,
    persona VARCHAR, persuasion_profile VARCHAR, is_mayor BOOLEAN,
    eliminated_round INT NULL, survived BOOLEAN, character_image VARCHAR
)

turns (
    id UUID PK, game_id UUID FK, player_id UUID FK, round_number INT,
    phase VARCHAR, prompt_sent TEXT, completion_received TEXT,
    private_reasoning TEXT, public_statement TEXT, vote_target UUID FK NULL,
    bid_level INT NULL, technique_self_label VARCHAR NULL,
    deception_self_label VARCHAR NULL, confidence INT NULL,
    is_default_response BOOLEAN, token_count_input INT, token_count_output INT,
    latency_ms INT, created_at TIMESTAMP
)

night_actions (
    id UUID PK, game_id UUID FK, round_number INT, wolf_target UUID FK,
    doctor_target UUID FK, seer_target UUID FK, seer_result VARCHAR,
    kill_successful BOOLEAN, created_at TIMESTAMP
)

votes (
    id UUID PK, game_id UUID FK, round_number INT, voter UUID FK,
    target UUID FK, is_mayor_tiebreak BOOLEAN, created_at TIMESTAMP
)

game_events (
    id UUID PK, game_id UUID FK, round_number INT, event_type VARCHAR,
    details JSONB, created_at TIMESTAMP
)
```

## Design constraints
- Moderator must be fully deterministic — no LLM calls
- Total agent context must stay under 80% of model's context window
- Game cap at 10 day/night cycles
- Statistical design: 200-500 games with balanced profile assignment
- Shared design system with SYNTHETICA project
- Must deploy on CSC Rahti (OpenShift)

## Out of scope
- Human players — all agents are LLMs
- Real-time multiplayer — games run server-side, UI is for observation/replay
- Custom persuasion technique authoring UI — technique files are .md managed in repo
- Integration with SYNTHETICA codebase — shared design system only, separate deployments
