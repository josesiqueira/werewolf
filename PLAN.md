# Implementation Plan — Werewolf AI Agents

## Phase 1: Core Game Engine

**Description**: Build the deterministic game master (state machine), database schema, SQLAlchemy models, and a stub agent interface. This is the foundation — no LLM calls yet, just the game logic with mock agents that return random valid actions.

**Dependencies**: None (first phase)

**has_ui**: false

**Estimated complexity**: High

### Tasks

1. **Project scaffolding**: Create `backend/` directory with FastAPI app structure: `app/main.py`, `app/config.py`, `app/models/`, `app/api/`, `app/engine/`, `app/schemas/`. Set up `requirements.txt`, `.env.example`, `alembic.ini`. Create `frontend/` with `npx create-next-app@14` using TypeScript + Tailwind + App Router. Add `docker-compose.yml` with PostgreSQL service. Add `.gitignore` with `_queries.cypher`, `.env`, `__pycache__/`, `node_modules/`, `.next/`.

2. **Database models**: Implement SQLAlchemy 2.0 models for all 5 tables: `Game`, `Player`, `Turn`, `NightAction`, `Vote`, `GameEvent`. Use UUID primary keys. Add Alembic initial migration. All column types must match the schema in SPEC.md exactly (JSONB for `config` and `details`, nullable fields where specified).

3. **Pydantic schemas**: Create request/response schemas in `app/schemas/`: `GameCreate`, `GameResponse`, `PlayerResponse`, `TurnResponse`, `NightActionResponse`, `VoteResponse`, `GameEventResponse`, `GameStateResponse`. Include the agent output schema: `AgentResponse` with fields `private_reasoning`, `public_statement`, `vote_target`, `bid_level`, `technique_self_label`, `deception_self_label`, `confidence`.

4. **Game state machine**: Implement `app/engine/game_state.py` with a `GameStateMachine` class. States: `INIT`, `MAYOR_CAMPAIGN`, `MAYOR_VOTE`, `NIGHT`, `DAY_BID`, `DAY_SPEECH`, `VOTE`, `GAME_OVER`. Transitions must be deterministic. Track: alive players, current round (1-10), current phase, mayor, eliminated players with roles, debate turn count (cap at 10).

5. **Role and player setup**: Implement `app/engine/roles.py`. Fixed distribution: 2 werewolves, 1 seer, 1 doctor, 3 villagers. Random assignment. Werewolves know each other. Seer/doctor/villagers only know their own role.

6. **Night phase resolution**: Implement `app/engine/night.py`. Accept wolf_target, seer_target, doctor_target. Resolve: if doctor_target == wolf_target then kill_successful=false, else kill_successful=true and player is eliminated. Seer gets the true role of seer_target. Create `NightAction` record and `GameEvent` records (death, if any).

7. **Mayor election**: Implement `app/engine/mayor.py`. Campaign phase (collect statements from all alive agents). Vote phase (each agent votes for one other agent). Tally: plurality wins, random tiebreak. Record mayor in game state. Mayor succession: when mayor is eliminated, they designate a successor from alive players.

8. **Day phase with bidding**: Implement `app/engine/day.py`. For each debate turn (up to 10): collect bids (0-4) from all alive agents, select highest bidder (ties broken by mention priority — agents referenced in previous turn's public_statement get priority, further ties random). Selected agent delivers speech. Track debate history.

9. **Vote phase and elimination**: Implement `app/engine/vote.py`. Collect votes from all alive agents. Tally: majority eliminates. If tie, mayor breaks it. If no majority and no tie (3+ way split), re-vote once then no elimination. Record all votes. Eliminate player, reveal role, create GameEvent. Check win conditions: all wolves dead = villagers win; wolves >= villagers = wolves win.

10. **Game loop orchestrator**: Implement `app/engine/game_loop.py` with `run_game()` that ties everything together following the pseudocode in the brainstorm. Uses stub/mock agent interface (random valid actions). Writes all data to database. Enforces 10-round cap. Returns final game state.

11. **Stub agent interface**: Implement `app/engine/agent_interface.py` with `AgentInterface` base class and `MockAgent` subclass. `MockAgent` returns random valid actions: random alive target for votes/kills, random bid 0-4, placeholder public_statement. This allows testing the full game loop without LLM calls.

12. **NDJSON export**: Implement `app/engine/export.py`. Export all turns for a game (or batch) as newline-delimited JSON. Each line contains: game_id, round, phase, player_id, all turn fields.

13. **Core API endpoints**: Implement `POST /api/games` (create and run a single game with mock agents), `GET /api/games` (list with filters: status, winner, is_degraded), `GET /api/games/:id` (full game state with players), `GET /api/games/:id/turns` (all turns), `GET /api/export/:format` (NDJSON export).

### Acceptance Criteria
- [ ] `pytest` passes: game initializes with exactly 7 players in correct role distribution (2W, 1S, 1D, 3V)
- [ ] State machine transitions through all phases in correct order: INIT -> MAYOR_CAMPAIGN -> MAYOR_VOTE -> NIGHT -> DAY_BID -> DAY_SPEECH -> VOTE -> NIGHT -> ... -> GAME_OVER
- [ ] Night resolution: doctor save prevents kill (kill_successful=false when targets match)
- [ ] Night resolution: unprotected target is eliminated (kill_successful=true)
- [ ] Seer receives correct role of investigated player
- [ ] Mayor election produces exactly one mayor via plurality vote
- [ ] Mayor succession assigns new mayor when current mayor is eliminated
- [ ] Day bidding selects highest bidder; ties broken by mention priority
- [ ] Debate capped at 10 turns per day phase
- [ ] Vote elimination: majority vote eliminates target; mayor breaks ties
- [ ] Win condition: game ends when all wolves dead (villagers win)
- [ ] Win condition: game ends when wolves >= remaining villagers (wolves win)
- [ ] Game cap: game marked as discarded after 10 rounds without resolution
- [ ] Full game loop completes with mock agents and writes all records to database
- [ ] NDJSON export produces valid newline-delimited JSON with all turn data
- [ ] All 5 API endpoints return correct responses
- [ ] Database contains correct records for games, players, turns, night_actions, votes, game_events after a game run

### Files to Create/Modify
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/001_initial_schema.py`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/models/__init__.py`
- `backend/app/models/game.py`
- `backend/app/models/player.py`
- `backend/app/models/turn.py`
- `backend/app/models/night_action.py`
- `backend/app/models/vote.py`
- `backend/app/models/game_event.py`
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/game.py`
- `backend/app/schemas/player.py`
- `backend/app/schemas/turn.py`
- `backend/app/schemas/agent.py`
- `backend/app/engine/__init__.py`
- `backend/app/engine/game_state.py`
- `backend/app/engine/roles.py`
- `backend/app/engine/night.py`
- `backend/app/engine/mayor.py`
- `backend/app/engine/day.py`
- `backend/app/engine/vote.py`
- `backend/app/engine/game_loop.py`
- `backend/app/engine/agent_interface.py`
- `backend/app/engine/export.py`
- `backend/app/api/__init__.py`
- `backend/app/api/games.py`
- `backend/app/api/export.py`
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/test_game_state.py`
- `backend/tests/test_night.py`
- `backend/tests/test_mayor.py`
- `backend/tests/test_day.py`
- `backend/tests/test_vote.py`
- `backend/tests/test_game_loop.py`
- `docker-compose.yml`
- `.gitignore`
- `frontend/` (scaffolded via create-next-app, no custom code yet)

### Parallel Split (3 agents)
- **Agent A**: Tasks 1-3 (scaffolding, models, schemas)
- **Agent B**: Tasks 4-9 (game engine: state machine, night, mayor, day, vote)
- **Agent C**: Tasks 10-13 (game loop, mock agent, export, API endpoints) — starts after A+B have core structures

---

## Phase 2: Agent System

**Description**: Replace mock agents with real LLM-backed agents. Build prompt construction, persuasion technique injection, persona system, output validation/repair, error handling with retries, and memory management.

**Dependencies**: Phase 1 (game engine, models, schemas)

**has_ui**: false

**Estimated complexity**: High

### Tasks

1. **OpenAI API client wrapper**: Implement `app/agent/llm_client.py`. Async wrapper around OpenAI SDK for GPT 5.4. Configurable timeout (default 60s). Returns raw completion text. Tracks token_count_input, token_count_output, latency_ms. Uses httpx async transport.

2. **Retry and fallback logic**: Implement `app/agent/retry.py`. 3 retries with exponential backoff (1s, 3s, 9s). After all retries fail, return conservative defaults: bid=1, generic public_statement ("I need more time to think about this."), random valid vote_target, deception_self_label="truthful", confidence=3. Log all failures.

3. **System message builder**: Implement `app/agent/prompts/system_message.py`. Construct the ~750 token system message: game rules (~200 tokens), role assignment + private info (~100 tokens, e.g., "You are a Werewolf. Player 4 is your teammate."), persona description (~200 tokens), JSON output format instructions (~150 tokens), behavioral instructions (~100 tokens). System message is cached per agent per game (same across turns).

4. **Persona system**: Implement `app/agent/personas.py`. Define 7 distinct personas (~200 tokens each): analytical/measured, aggressive/confrontational, quiet/observant, warm/collaborative, suspicious/paranoid, diplomatic/balanced, blunt/direct. Random assignment per game (no duplicates within a game). Each persona includes speaking style, reasoning tendencies, and social behavior patterns.

5. **Persuasion technique loader**: Implement `app/agent/techniques.py`. Load all 6 technique files from `persuasion-techniques/` directory. Map profile names to files: ethos -> TECHNIQUE-ETHOS.md, pathos -> TECHNIQUE-PATHOS.md, logos -> TECHNIQUE-LOGOS.md, authority_socialproof -> TECHNIQUE-AUTHORITY-SOCIALPROOF.md, reciprocity_liking -> TECHNIQUE-RECIPROCITY-LIKING.md, scarcity_commitment -> TECHNIQUE-SCARCITY-COMMITMENT.md. Baseline gets no technique text. Cache loaded files in memory.

6. **User message builder**: Implement `app/agent/prompts/user_message.py`. Construct the dynamic user message per turn: persuasion technique document (if not baseline, ~800-1200 tokens), current game state as structured object (~300-500 tokens: alive_players, voting_history, eliminated_players, night_results, mayor, current_phase), conversation history (~500-2000 tokens), turn instruction. Total target: ~1600-3700 tokens.

7. **Memory manager**: Implement `app/agent/memory.py`. Last 2-3 rounds: full dialogue transcript. Earlier rounds: summarized to key events (accusations, vote outcomes, eliminations). Total context must stay under 80% of model context window. Implement `summarize_round()` that extracts: who accused whom, vote result, who was eliminated and their role.

8. **Output parser and validator**: Implement `app/agent/output_parser.py`. Parse JSON from LLM response. Repair malformed JSON: strip markdown fences (```json ... ```), fix trailing commas, fix missing quotes. If still invalid, use conservative defaults. Validate against game state: vote_target must be alive and not self, bid must be 0-4, deception_self_label must be one of [truthful, omission, distortion, fabrication, misdirection], technique_self_label must reference assigned profile sections (or "none" for baseline). Auto-correct invalid values: dead vote target -> random alive player, bid outside 0-4 -> clamp, missing fields -> defaults.

9. **Werewolf leak detection**: Implement validation in output parser: werewolf public_statement must not contain references to night-phase private information (e.g., "I targeted Player X last night", "My wolf partner and I decided..."). Use keyword pattern matching for common leaks. If detected, replace with generic statement and log the leak.

10. **LLM agent implementation**: Implement `app/agent/llm_agent.py` with `LLMAgent` class extending `AgentInterface`. Wire together: system message builder, user message builder, memory manager, LLM client, retry logic, output parser. Each method (campaign, vote, bid, speak, night_action) constructs appropriate prompts and returns validated AgentResponse.

11. **Game degradation tracking**: Update game loop to track default response percentage per game. After game completes, if >30% of turns used defaults (is_default_response=true), set game.is_degraded=true. Log warning during game if default rate is climbing.

12. **Agent system tests**: Unit tests with mocked OpenAI API responses. Test: prompt construction produces correct structure, output parser handles valid JSON / malformed JSON / invalid actions, retry logic fires correctly, memory manager summarizes old rounds, technique loader finds all 6 files, persona assignment has no duplicates, werewolf leak detection catches obvious leaks.

### Acceptance Criteria
- [ ] System message is ~750 tokens and contains: rules, role, persona, output format, behavioral instructions
- [ ] User message contains: technique doc (or absent for baseline), game state, conversation history, turn instruction
- [ ] All 6 technique files load correctly from `persuasion-techniques/`
- [ ] Baseline agents receive no technique document in their prompt
- [ ] 7 distinct personas assigned per game with no duplicates
- [ ] JSON output parsed correctly for well-formed responses
- [ ] Malformed JSON repaired: markdown fences stripped, trailing commas fixed
- [ ] Invalid vote target (dead player) auto-corrected to random alive player
- [ ] Bid outside 0-4 clamped to valid range
- [ ] Missing response fields filled with conservative defaults
- [ ] Retry fires 3 times with backoff (1s, 3s, 9s) on API failure
- [ ] After 3 failures, conservative defaults used and turn marked is_default_response=true
- [ ] API timeout set to 60s
- [ ] Memory: last 2-3 rounds full transcript, earlier rounds summarized
- [ ] Total context stays under 80% of model window
- [ ] Werewolf leak detection catches night-phase references in public_statement
- [ ] Game flagged as degraded when >30% turns use defaults

### Files to Create/Modify
- `backend/app/agent/__init__.py`
- `backend/app/agent/llm_client.py`
- `backend/app/agent/retry.py`
- `backend/app/agent/personas.py`
- `backend/app/agent/techniques.py`
- `backend/app/agent/memory.py`
- `backend/app/agent/output_parser.py`
- `backend/app/agent/llm_agent.py`
- `backend/app/agent/prompts/__init__.py`
- `backend/app/agent/prompts/system_message.py`
- `backend/app/agent/prompts/user_message.py`
- `backend/app/engine/game_loop.py` (modify — integrate LLMAgent)
- `backend/app/engine/agent_interface.py` (modify — ensure base class matches)
- `backend/app/models/game.py` (modify — degradation tracking)
- `backend/tests/test_llm_client.py`
- `backend/tests/test_output_parser.py`
- `backend/tests/test_prompts.py`
- `backend/tests/test_personas.py`
- `backend/tests/test_techniques.py`
- `backend/tests/test_memory.py`
- `backend/tests/test_retry.py`

### Parallel Split (2 agents)
- **Agent A**: Tasks 1-5 (LLM client, retry, system message, personas, technique loader)
- **Agent B**: Tasks 6-12 (user message, memory, parser, leak detection, LLM agent integration, degradation, tests)

---

## Phase 3: Game Runner

**Description**: Build the batch execution system for running 200-500 games with balanced profile assignment, quality checks, progress tracking, and resumption after interruption.

**Dependencies**: Phase 2 (working LLM agents)

**has_ui**: false

**Estimated complexity**: Medium

### Tasks

1. **Profile assignment strategy**: Implement `app/runner/assignment.py`. Balanced randomization: each of the 7 profiles (6 techniques + baseline) paired with each of the 4 roles roughly equally across N games. Use a Latin-square-inspired approach: pre-generate assignment matrix for the full batch, ensuring each profile x role cell count is within +/-1 of the mean. Store assignment plan in database.

2. **Batch runner**: Implement `app/runner/batch.py`. Accept configuration: number of games, max parallelism (concurrent games), debate cap. Create batch record. Execute games sequentially or with configurable concurrency (asyncio.gather with semaphore). Use the assignment strategy for each game's profile distribution. Track: current game number, completion count, failure count, estimated time remaining (based on rolling average of game duration).

3. **Batch database model**: Add `batches` table: id (UUID), created_at, total_games (INT), completed_games (INT), failed_games (INT), status (pending|running|completed|paused), config (JSONB), started_at, completed_at. Add batch_id FK to games table.

4. **Progress tracking**: Implement `app/runner/progress.py`. Real-time progress: current game / total games, completion percentage, estimated time remaining, games per minute rate, current game's phase. Expose via API endpoint. Log progress to stdout every 10 games.

5. **Resumption logic**: Implement resume capability in batch runner. On startup, check for batches with status=running. Find last completed game number. Resume from next game using the pre-generated assignment matrix. Mark interrupted games (status=running at recovery time) as discarded.

6. **Quality checks**: After each game completes, check degraded flag. Log warning if degraded rate exceeds 20% of completed games. Final batch summary: total games, completed, discarded (cap reached), degraded, games per profile, win rates by faction.

7. **Batch API endpoints**: Implement `POST /api/batch` (start batch with config), `GET /api/batch/:id/status` (progress, ETA, degraded count), `GET /api/batch` (list all batches).

8. **Batch runner tests**: Test profile assignment balance (over 100 mock games, each profile x role count within +/-2 of mean). Test resumption (simulate interruption, verify pickup from correct game). Test progress calculation. Test quality check thresholds.

### Acceptance Criteria
- [ ] Profile assignment: over 210 games (7 profiles x 4 roles x ~7.5 per cell), each profile x role count within +/-2 of mean
- [ ] Batch runs N games end-to-end (test with N=3 using mock agents)
- [ ] Concurrent execution works with configurable parallelism (test with 2 concurrent)
- [ ] Progress tracking shows: game X/N, Y% complete, ETA
- [ ] Resumption: interrupted batch picks up from last completed game
- [ ] Interrupted running games marked as discarded
- [ ] Degraded games flagged and counted in batch summary
- [ ] Batch API endpoints return correct status and progress data
- [ ] NDJSON export works for full batch (all games)

### Files to Create/Modify
- `backend/app/runner/__init__.py`
- `backend/app/runner/assignment.py`
- `backend/app/runner/batch.py`
- `backend/app/runner/progress.py`
- `backend/app/models/batch.py`
- `backend/app/models/game.py` (modify — add batch_id FK)
- `backend/app/schemas/batch.py`
- `backend/app/api/batch.py`
- `backend/app/main.py` (modify — add batch router)
- `backend/alembic/versions/002_add_batches.py`
- `backend/tests/test_assignment.py`
- `backend/tests/test_batch.py`
- `backend/tests/test_progress.py`

### Parallel Split (2 agents)
- **Agent A**: Tasks 1-3 (assignment strategy, batch runner core, batch model)
- **Agent B**: Tasks 4-8 (progress tracking, resumption, quality checks, API, tests)

---

## Phase 4: Admin Panel + UI

**Description**: Build the Next.js frontend with game list, game replay, agent inspector, and the shared design system. Heavy use of React Bits components for polish.

**Dependencies**: Phase 1 (API endpoints), Phase 3 (batch API)

**has_ui**: true

**Estimated complexity**: High

### Tasks

1. **Shared design system setup**: Configure Tailwind with custom theme: color tokens for day/night modes, profile gradient colors (ethos=blue/silver, pathos=red/warm, logos=green/teal, authority_socialproof=gold/amber, reciprocity_liking=purple/pink, scarcity_commitment=orange/fire, baseline=neutral gray). Set up shared layout shell with navigation. Install React Bits Dock component for main navigation (Game View, Admin Panel, Analytics).

2. **API client layer**: Create `frontend/src/lib/api.ts` with typed fetch wrappers for all backend endpoints. Use TanStack Query for data fetching with proper cache keys, stale times, and error handling. Types in `frontend/src/types/` matching backend Pydantic schemas.

3. **Game list page** (`/games`): Data table with columns: game ID (truncated UUID), date, status badge (pending/running/completed/discarded), winner faction, rounds played, profiles used (colored badges), degraded flag (warning icon). Filters: status dropdown, winner faction, profile multiselect, degraded toggle. Sorting by any column. Alternative browse mode using React Bits StackedCards component.

4. **Dashboard page** (`/`): Overview cards with CountUp animations: total games, completed games, average game duration, win rate by faction. Recent games list using StackedCards. Batch status summary if any batch is running (progress bar, ETA). Quick links to analytics and game list.

5. **Game replay page** (`/games/:id`): Full game replay interface. Player cards in circle layout using TiltedCard + Magnet hover effects. Day/night background toggle: Aurora component for night, Particles for day, smooth crossfade transitions. Timeline scrubber at bottom for navigating between phases/rounds. AnimatedContent transitions between phases.

6. **Replay chat log**: Chat log panel using AnimatedList. Messages appear one by one during replay. Each message attributed to speaker's character portrait + name in GradientText (profile color). Support play/pause/step-forward controls. Phase headers (Night, Day, Vote) with RotatingText animation.

7. **Replay voting visualization**: After vote phase, show animated arrows from each voter to their target using FollowCursor-style animation. Vote tally summary. Mayor tiebreak highlighted. Eliminated player's card dims with Beams + SplitText role reveal animation.

8. **Bidding indicator**: Visual heat bar per player showing their bid level (0=cool blue, 4=glowing red). Updates each debate turn. Current speaker highlighted.

9. **Agent inspector page** (`/games/:id/agents/:agentId`): Click any player card at any turn to open inspector. SpotlightCard highlights selected agent. LEFT panel: private_reasoning with BlurText reveal animation. RIGHT panel: public_statement (normal text). BOTTOM bar: technique_self_label, deception_self_label, confidence (1-5 stars), bid_level, assigned profile badge. Turn navigation (prev/next) for same agent.

10. **Character portraits**: Add ~10 stylized 2D character portrait images to `frontend/public/portraits/`. Display inside TiltedCard components. Each agent gets a persistent portrait assignment per game (stored in player.character_image). Portraits have dark/moody illustrated style.

11. **Responsive layout**: Ensure all pages work on desktop (1200px+) and tablet (768px+). Mobile (375px+) should show simplified layouts: stacked panels instead of side-by-side, collapsed navigation. Game replay circle layout adapts to available width.

12. **Frontend component tests**: Vitest + Testing Library tests for: GameList filtering, ReplayTimeline navigation, AgentInspector panel content, VotingVisualization data mapping, API client error handling.

### Acceptance Criteria
- [ ] Dock navigation between all main sections works with magnification effect
- [ ] Game list displays all games with correct data and filtering works for all filter types
- [ ] StackedCards browse mode shows games in visual card stack
- [ ] Dashboard shows CountUp animated statistics
- [ ] Game replay loads full game data and displays player cards in circle layout
- [ ] TiltedCard hover shows 3D tilt effect; Magnet pull toward cursor works
- [ ] Day/night background switches between Particles and Aurora with crossfade
- [ ] Chat log replays messages one by one with AnimatedList
- [ ] Player names colored with GradientText matching their profile
- [ ] Voting arrows animate from voter to target
- [ ] Elimination shows Beams + SplitText role reveal
- [ ] Agent inspector shows private reasoning with BlurText animation on left, public statement on right
- [ ] Inspector bottom bar shows all metadata badges
- [ ] Turn navigation (prev/next) works within agent inspector
- [ ] Character portraits render inside TiltedCards
- [ ] Responsive: desktop and tablet layouts work; mobile shows stacked panels
- [ ] Vitest tests pass for core components

### Files to Create/Modify
- `frontend/tailwind.config.ts` (modify — add theme tokens)
- `frontend/src/app/layout.tsx` (modify — add shared layout shell + Dock nav)
- `frontend/src/app/page.tsx` (modify — dashboard)
- `frontend/src/app/games/page.tsx`
- `frontend/src/app/games/[id]/page.tsx`
- `frontend/src/app/games/[id]/agents/[agentId]/page.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/types/game.ts`
- `frontend/src/types/player.ts`
- `frontend/src/types/turn.ts`
- `frontend/src/types/batch.ts`
- `frontend/src/components/layout/Dock.tsx`
- `frontend/src/components/layout/Shell.tsx`
- `frontend/src/components/game-list/GameTable.tsx`
- `frontend/src/components/game-list/GameFilters.tsx`
- `frontend/src/components/game-list/StackedGameCards.tsx`
- `frontend/src/components/dashboard/StatsCards.tsx`
- `frontend/src/components/dashboard/RecentGames.tsx`
- `frontend/src/components/dashboard/BatchStatus.tsx`
- `frontend/src/components/replay/PlayerCircle.tsx`
- `frontend/src/components/replay/PlayerCard.tsx`
- `frontend/src/components/replay/ChatLog.tsx`
- `frontend/src/components/replay/Timeline.tsx`
- `frontend/src/components/replay/VotingViz.tsx`
- `frontend/src/components/replay/BiddingBar.tsx`
- `frontend/src/components/replay/DayNightBackground.tsx`
- `frontend/src/components/replay/EliminationReveal.tsx`
- `frontend/src/components/inspector/InspectorLayout.tsx`
- `frontend/src/components/inspector/PrivatePanel.tsx`
- `frontend/src/components/inspector/PublicPanel.tsx`
- `frontend/src/components/inspector/MetadataBar.tsx`
- `frontend/src/components/inspector/TurnNav.tsx`
- `frontend/src/components/shared/ProfileBadge.tsx`
- `frontend/src/components/shared/StatusBadge.tsx`
- `frontend/src/hooks/useGameReplay.ts`
- `frontend/src/hooks/useAgentInspector.ts`
- `frontend/src/stores/replayStore.ts`
- `frontend/public/portraits/` (portrait images)
- `frontend/src/__tests__/GameTable.test.tsx`
- `frontend/src/__tests__/ReplayTimeline.test.tsx`
- `frontend/src/__tests__/AgentInspector.test.tsx`
- `frontend/src/__tests__/ApiClient.test.tsx`

### Parallel Split (3 agents)
- **Agent A**: Tasks 1-4 (design system, API client, game list, dashboard)
- **Agent B**: Tasks 5-8 (game replay: circle layout, chat log, voting viz, bidding)
- **Agent C**: Tasks 9-12 (agent inspector, portraits, responsive, tests)

---

## Phase 5: Analytics and Metrics

**Description**: Build the cross-game analytics dashboard with derived metric computation, statistical visualizations, and data export for external analysis tools.

**Dependencies**: Phase 3 (batch data available), Phase 4 (frontend infrastructure)

**has_ui**: true

**Estimated complexity**: Medium

### Tasks

1. **Derived metric computation engine**: Implement `app/analytics/metrics.py`. Compute all metrics from the spec after a batch completes (or on demand). Metrics: win rate by faction x profile, survival duration by role x profile, vote-swing per message (did votes change after a specific agent spoke), deception index (private reasoning vs public statement semantic gap — use simple keyword/sentiment divergence), technique adherence rate (self-label matches assigned profile), bus-throwing rate (wolf voting against wolf teammate), bandwagon dynamics (time from first vote to majority forming).

2. **Detection difficulty matrix**: Implement `app/analytics/detection.py`. For each technique x deception type combination, compute how often other agents accused or expressed suspicion of the agent. Parse public_statements for accusation keywords targeting each player. Cross-reference with the accused player's actual deception_self_label and technique profile.

3. **Accusation graph builder**: Implement `app/analytics/accusation_graph.py`. Parse all public_statements across games to extract accusation relationships (who accused whom). Aggregate by profile. Output as nodes (players/profiles) and weighted edges (accusation count). Format for D3 force-directed graph consumption.

4. **Analytics API endpoints**: Implement `GET /api/analytics/winrates` (returns win rate matrix: faction x profile with counts, mean, SEM, 95% CI), `GET /api/analytics/survival` (survival duration by role x profile), `GET /api/analytics/techniques` (technique adherence, deception index, detection difficulty, bus-throwing, bandwagon data), `GET /api/analytics/accusations` (accusation graph data).

5. **Analytics dashboard page** (`/analytics`): Main analytics view with tab navigation between metric categories. Win rate heatmap: faction (rows) x profile (columns), cells colored by win rate with CountUp values. Survival duration bar charts by role x profile. Technique adherence rates as grouped bar chart.

6. **Vote-swing and bandwagon visualizations**: Vote-swing chart: for each profile, average vote change after agent speaks. Bandwagon dynamics: time-to-majority histogram by game. Both use Recharts with animated transitions.

7. **Accusation graph visualization**: Force-directed graph using D3. Nodes = profiles (colored by profile gradient). Edges = accusation frequency (thickness = count). Interactive: hover node to highlight its edges. Filter by game subset or profile.

8. **Detection difficulty and deception visualizations**: Detection difficulty matrix as heatmap (technique x deception type -> suspicion rate). Deception index distribution by profile as box plot or violin chart. Baseline comparison overlay on all charts (gray dashed line for baseline mean).

9. **Data export**: Implement export buttons on analytics page. CSV export: one row per game-player with all metrics. JSON export: structured with metadata. NDJSON export: one line per turn (reuse from Phase 1). Add download endpoint `GET /api/export/:format` with query params for filtering by batch, profile, role.

10. **Analytics tests**: Backend: test metric computations against known game data (create fixture games with predetermined outcomes, verify metric values). Frontend: test chart components render with mock data.

### Acceptance Criteria
- [ ] Win rate heatmap displays correct values: test with 10 fixture games, verify counts match
- [ ] Survival duration chart shows mean +/- SEM per role x profile combination
- [ ] Vote-swing metric correctly identifies vote changes after each agent's speech
- [ ] Deception index computed for all agents with technique profiles
- [ ] Detection difficulty matrix populated for all technique x deception type cells with sufficient data
- [ ] Technique adherence rate: percentage of turns where self-label matches assigned profile sections
- [ ] Accusation graph renders with correct node colors and edge weights
- [ ] Bus-throwing rate computed correctly (wolf votes against wolf teammate / total wolf votes)
- [ ] Bandwagon dynamics: time-to-majority measured in debate turns
- [ ] Baseline comparison line shown on all metric charts
- [ ] CSV export contains one row per game-player with all derived metrics
- [ ] JSON export contains structured data with batch metadata
- [ ] All analytics API endpoints return data within 5 seconds for 500 games
- [ ] CountUp animations fire on initial page load
- [ ] Charts re-render with animation when filters change

### Files to Create/Modify
- `backend/app/analytics/__init__.py`
- `backend/app/analytics/metrics.py`
- `backend/app/analytics/detection.py`
- `backend/app/analytics/accusation_graph.py`
- `backend/app/api/analytics.py`
- `backend/app/api/export.py` (modify — add CSV, filtered exports)
- `backend/app/main.py` (modify — add analytics router)
- `backend/tests/test_metrics.py`
- `backend/tests/test_detection.py`
- `backend/tests/test_accusation_graph.py`
- `frontend/src/app/analytics/page.tsx`
- `frontend/src/components/analytics/WinRateHeatmap.tsx`
- `frontend/src/components/analytics/SurvivalChart.tsx`
- `frontend/src/components/analytics/VoteSwingChart.tsx`
- `frontend/src/components/analytics/BandwagonChart.tsx`
- `frontend/src/components/analytics/AccusationGraph.tsx`
- `frontend/src/components/analytics/DetectionMatrix.tsx`
- `frontend/src/components/analytics/DeceptionIndex.tsx`
- `frontend/src/components/analytics/TechniqueAdherence.tsx`
- `frontend/src/components/analytics/BaselineOverlay.tsx`
- `frontend/src/components/analytics/ExportButtons.tsx`
- `frontend/src/components/analytics/AnalyticsTabs.tsx`
- `frontend/src/hooks/useAnalytics.ts`
- `frontend/src/__tests__/WinRateHeatmap.test.tsx`
- `frontend/src/__tests__/AccusationGraph.test.tsx`
- `frontend/src/__tests__/ExportButtons.test.tsx`

### Parallel Split (2 agents)
- **Agent A**: Tasks 1-4 (backend metric computation, detection, accusation graph, API endpoints)
- **Agent B**: Tasks 5-10 (frontend visualizations, export UI, tests)

---

## Phase Dependency Graph

```
Phase 1 (Core Game Engine)
    |
    v
Phase 2 (Agent System)
    |
    v
Phase 3 (Game Runner)
    |         \
    v          v
Phase 4       Phase 5
(Admin UI)    (Analytics)
```

Phase 4 and Phase 5 can run in parallel once Phase 3 is complete. Phase 4 only strictly requires Phase 1 API endpoints to start, but benefits from Phase 3 batch data. Phase 5 requires Phase 3 (batch data to analyze) and Phase 4 (frontend infrastructure to build upon).
