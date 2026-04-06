"""Derived metric computation engine.

Phase 5, Task 1 — Compute all cross-game metrics after a batch completes
or on demand.
"""

from __future__ import annotations

import math
import re
import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.game import Game
from app.models.player import Player
from app.models.turn import Turn
from app.models.vote import Vote


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FACTIONS = ("villagers", "werewolves")

_PROFILES = [
    "ethos",
    "pathos",
    "logos",
    "authority_socialproof",
    "reciprocity_liking",
    "scarcity_commitment",
    "baseline",
]

_WOLF_ROLES = {"werewolf"}
_VILLAGER_ROLES = {"villager", "seer", "doctor"}


def _faction_for_role(role: str) -> str:
    return "werewolves" if role in _WOLF_ROLES else "villagers"


def _sem(values: list[float]) -> float:
    """Standard error of the mean."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return math.sqrt(variance / n)


def _ci95(mean: float, sem: float) -> tuple[float, float]:
    """95% confidence interval (z=1.96)."""
    margin = 1.96 * sem
    return (mean - margin, mean + margin)


def _keyword_set(text: str) -> set[str]:
    """Extract lowercase keyword set from text, stripping punctuation."""
    if not text:
        return set()
    return set(re.findall(r"[a-z]+", text.lower()))


# ---------------------------------------------------------------------------
# Batch-scoped game query helper
# ---------------------------------------------------------------------------

async def _game_ids_for_batch(
    db: AsyncSession, batch_id: uuid.UUID | None
) -> list[uuid.UUID]:
    """Return completed game IDs, optionally filtered by batch."""
    stmt = select(Game.id).where(Game.status == "completed")
    if batch_id is not None:
        stmt = stmt.where(Game.batch_id == batch_id)
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def _load_players_by_game(
    db: AsyncSession, game_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[Player]]:
    """Load players grouped by game_id."""
    if not game_ids:
        return {}
    result = await db.execute(
        select(Player).where(Player.game_id.in_(game_ids))
    )
    players = result.scalars().all()
    grouped: dict[uuid.UUID, list[Player]] = defaultdict(list)
    for p in players:
        grouped[p.game_id].append(p)
    return dict(grouped)


# ---------------------------------------------------------------------------
# 1. Win rate by faction x profile
# ---------------------------------------------------------------------------

async def win_rate_by_faction_profile(
    db: AsyncSession, batch_id: uuid.UUID | None = None
) -> dict[str, Any]:
    """Win rate matrix: faction (villagers/werewolves) x profile.

    Returns dict with structure:
        {
            "matrix": {
                "<faction>": {
                    "<profile>": {
                        "count": int,
                        "wins": int,
                        "mean": float,
                        "sem": float,
                        "ci_lower": float,
                        "ci_upper": float,
                    }
                }
            }
        }
    """
    game_ids = await _game_ids_for_batch(db, batch_id)
    if not game_ids:
        return {"matrix": {}}

    # Load games with winner
    result = await db.execute(
        select(Game).where(Game.id.in_(game_ids))
    )
    games = {g.id: g for g in result.scalars().all()}

    players_by_game = await _load_players_by_game(db, game_ids)

    # Collect per-player win/loss grouped by faction x profile
    # Each player in a game is either on the winning or losing faction.
    records: dict[str, dict[str, list[float]]] = {
        f: {p: [] for p in _PROFILES} for f in _FACTIONS
    }

    for gid, game in games.items():
        if game.winner is None:
            continue
        for player in players_by_game.get(gid, []):
            faction = _faction_for_role(player.role)
            profile = player.persuasion_profile or "baseline"
            if profile not in _PROFILES:
                profile = "baseline"
            won = 1.0 if game.winner == faction else 0.0
            records[faction][profile].append(won)

    matrix: dict[str, dict[str, dict[str, Any]]] = {}
    for faction in _FACTIONS:
        matrix[faction] = {}
        for profile in _PROFILES:
            vals = records[faction][profile]
            count = len(vals)
            if count == 0:
                matrix[faction][profile] = {
                    "count": 0, "wins": 0,
                    "mean": 0.0, "sem": 0.0,
                    "ci_lower": 0.0, "ci_upper": 0.0,
                }
                continue
            mean = sum(vals) / count
            sem = _sem(vals)
            ci_lo, ci_hi = _ci95(mean, sem)
            matrix[faction][profile] = {
                "count": count,
                "wins": int(sum(vals)),
                "mean": round(mean, 4),
                "sem": round(sem, 4),
                "ci_lower": round(max(0.0, ci_lo), 4),
                "ci_upper": round(min(1.0, ci_hi), 4),
            }

    return {"matrix": matrix}


# ---------------------------------------------------------------------------
# 2. Survival duration by role x profile
# ---------------------------------------------------------------------------

async def survival_duration_by_role_profile(
    db: AsyncSession, batch_id: uuid.UUID | None = None
) -> dict[str, Any]:
    """Mean rounds survived per role x profile.

    A player who survived the whole game gets rounds_played as their
    survival duration. Eliminated players get eliminated_round.
    """
    game_ids = await _game_ids_for_batch(db, batch_id)
    if not game_ids:
        return {"data": {}}

    # Load games for rounds_played
    result = await db.execute(
        select(Game).where(Game.id.in_(game_ids))
    )
    games = {g.id: g for g in result.scalars().all()}

    players_by_game = await _load_players_by_game(db, game_ids)

    all_roles = ["werewolf", "villager", "seer", "doctor"]
    durations: dict[str, dict[str, list[int]]] = {
        r: {p: [] for p in _PROFILES} for r in all_roles
    }

    for gid, game in games.items():
        for player in players_by_game.get(gid, []):
            role = player.role
            profile = player.persuasion_profile or "baseline"
            if profile not in _PROFILES:
                profile = "baseline"
            if role not in all_roles:
                continue

            if player.survived:
                duration = game.rounds_played
            elif player.eliminated_round is not None:
                duration = player.eliminated_round
            else:
                duration = game.rounds_played

            durations[role][profile].append(duration)

    data: dict[str, dict[str, dict[str, Any]]] = {}
    for role in all_roles:
        data[role] = {}
        for profile in _PROFILES:
            vals = durations[role][profile]
            count = len(vals)
            if count == 0:
                data[role][profile] = {
                    "count": 0, "mean": 0.0, "sem": 0.0,
                }
                continue
            mean = sum(vals) / count
            sem = _sem([float(v) for v in vals])
            data[role][profile] = {
                "count": count,
                "mean": round(mean, 2),
                "sem": round(sem, 2),
            }

    return {"data": data}


# ---------------------------------------------------------------------------
# 3. Vote swing per message
# ---------------------------------------------------------------------------

async def vote_swing_per_message(
    db: AsyncSession, game_id: uuid.UUID
) -> dict[str, Any]:
    """For each day speech in a game, compare vote targets before vs after.

    A 'swing' occurs when a player's vote target changes between the
    speech turn and the final vote. We detect this by looking at speech
    turns and comparing the subsequent votes to the prior state.

    Returns a list of speech events with swing counts.
    """
    # Load all turns for this game
    result = await db.execute(
        select(Turn)
        .where(Turn.game_id == game_id)
        .order_by(Turn.round_number, Turn.created_at)
    )
    turns = result.scalars().all()

    # Load players
    result = await db.execute(
        select(Player).where(Player.game_id == game_id)
    )
    players = {str(p.id): p for p in result.scalars().all()}

    # Load votes
    result = await db.execute(
        select(Vote)
        .where(Vote.game_id == game_id)
        .order_by(Vote.round_number, Vote.created_at)
    )
    votes = result.scalars().all()

    # Group votes by round
    votes_by_round: dict[int, list[Vote]] = defaultdict(list)
    for v in votes:
        votes_by_round[v.round_number].append(v)

    # Group speech turns by round
    speeches_by_round: dict[int, list[Turn]] = defaultdict(list)
    for t in turns:
        if t.phase == "DAY_SPEECH" and t.public_statement:
            speeches_by_round[t.round_number].append(t)

    swings: list[dict[str, Any]] = []

    for round_num in sorted(speeches_by_round.keys()):
        round_speeches = speeches_by_round[round_num]
        round_votes = votes_by_round.get(round_num, [])

        if not round_votes:
            continue

        # Build final vote map for this round
        final_vote_targets: dict[str, str] = {}
        for v in round_votes:
            final_vote_targets[str(v.voter)] = str(v.target)

        # For each speech, look at how many voters changed targets
        # relative to the prior speech's implied state
        prev_vote_targets: dict[str, str | None] = {}

        for idx, speech in enumerate(round_speeches):
            speaker_id = str(speech.player_id)
            speaker = players.get(speaker_id)

            # Count voters who mention the speaker's target in later votes
            # Simple heuristic: count how many final votes match a target
            # mentioned in this speech
            mentioned_targets = set()
            for pid, p in players.items():
                if p.agent_name and p.agent_name.lower() in (speech.public_statement or "").lower():
                    mentioned_targets.add(pid)

            # Calculate swing: how many players' vote targets changed
            # to align with what the speaker seemed to advocate
            swing_count = 0
            for voter_id, final_target in final_vote_targets.items():
                if voter_id == speaker_id:
                    continue
                prev = prev_vote_targets.get(voter_id)
                if prev != final_target and final_target in mentioned_targets:
                    swing_count += 1

            # Update prev targets with speech vote_target hints
            if speech.vote_target:
                prev_vote_targets[speaker_id] = str(speech.vote_target)

            swings.append({
                "round_number": round_num,
                "speech_index": idx,
                "speaker_id": speaker_id,
                "speaker_name": speaker.agent_name if speaker else None,
                "speaker_profile": speaker.persuasion_profile if speaker else None,
                "swing_count": swing_count,
                "total_voters": len(final_vote_targets) - 1,  # exclude speaker
            })

    return {"game_id": str(game_id), "swings": swings}


# ---------------------------------------------------------------------------
# 4. Deception index
# ---------------------------------------------------------------------------

async def deception_index(
    db: AsyncSession, batch_id: uuid.UUID | None = None
) -> dict[str, Any]:
    """Measure gap between private_reasoning and public_statement.

    Uses simple keyword overlap: 1 - |intersection| / |union|.
    Higher value = more divergence = more deceptive.
    """
    game_ids = await _game_ids_for_batch(db, batch_id)
    if not game_ids:
        return {"by_profile": {}}

    players_by_game = await _load_players_by_game(db, game_ids)

    # Build player -> profile map
    player_profile: dict[str, str] = {}
    for gid, plist in players_by_game.items():
        for p in plist:
            player_profile[str(p.id)] = p.persuasion_profile or "baseline"

    # Load turns with both private_reasoning and public_statement
    result = await db.execute(
        select(Turn)
        .where(Turn.game_id.in_(game_ids))
        .where(Turn.private_reasoning.isnot(None))
        .where(Turn.public_statement.isnot(None))
    )
    turns = result.scalars().all()

    scores_by_profile: dict[str, list[float]] = defaultdict(list)

    for t in turns:
        profile = player_profile.get(str(t.player_id), "baseline")
        if profile not in _PROFILES:
            profile = "baseline"

        priv_kw = _keyword_set(t.private_reasoning)
        pub_kw = _keyword_set(t.public_statement)

        if not priv_kw and not pub_kw:
            continue

        union = priv_kw | pub_kw
        intersection = priv_kw & pub_kw

        if len(union) == 0:
            divergence = 0.0
        else:
            divergence = 1.0 - len(intersection) / len(union)

        scores_by_profile[profile].append(divergence)

    by_profile: dict[str, dict[str, Any]] = {}
    for profile in _PROFILES:
        vals = scores_by_profile.get(profile, [])
        count = len(vals)
        if count == 0:
            by_profile[profile] = {"count": 0, "mean": 0.0, "sem": 0.0}
            continue
        mean = sum(vals) / count
        sem = _sem(vals)
        by_profile[profile] = {
            "count": count,
            "mean": round(mean, 4),
            "sem": round(sem, 4),
        }

    return {"by_profile": by_profile}


# ---------------------------------------------------------------------------
# 5. Technique adherence rate
# ---------------------------------------------------------------------------

async def technique_adherence_rate(
    db: AsyncSession, batch_id: uuid.UUID | None = None
) -> dict[str, Any]:
    """Percentage of turns where technique_self_label matches assigned profile sections.

    For each non-baseline player, check if their technique_self_label
    references one of the section headings from their assigned technique file.
    """
    from app.agent.techniques import get_technique_sections

    game_ids = await _game_ids_for_batch(db, batch_id)
    if not game_ids:
        return {"by_profile": {}}

    players_by_game = await _load_players_by_game(db, game_ids)

    # Build player -> (profile, sections) map
    player_info: dict[str, tuple[str, list[str]]] = {}
    for gid, plist in players_by_game.items():
        for p in plist:
            profile = p.persuasion_profile or "baseline"
            sections = get_technique_sections(profile)
            player_info[str(p.id)] = (profile, sections)

    # Load turns with technique_self_label
    result = await db.execute(
        select(Turn)
        .where(Turn.game_id.in_(game_ids))
        .where(Turn.technique_self_label.isnot(None))
    )
    turns = result.scalars().all()

    adherence: dict[str, dict[str, int]] = {
        p: {"match": 0, "total": 0} for p in _PROFILES
    }

    for t in turns:
        info = player_info.get(str(t.player_id))
        if info is None:
            continue
        profile, sections = info
        if profile not in _PROFILES:
            profile = "baseline"

        adherence[profile]["total"] += 1

        # Check if the self-label matches any section heading (case-insensitive)
        label = (t.technique_self_label or "").strip().lower()
        section_lower = [s.lower() for s in sections]

        if label in section_lower or any(label in s for s in section_lower):
            adherence[profile]["match"] += 1

    by_profile: dict[str, dict[str, Any]] = {}
    for profile in _PROFILES:
        total = adherence[profile]["total"]
        match = adherence[profile]["match"]
        rate = match / total if total > 0 else 0.0
        by_profile[profile] = {
            "total_turns": total,
            "matching_turns": match,
            "rate": round(rate, 4),
        }

    return {"by_profile": by_profile}


# ---------------------------------------------------------------------------
# 6. Bus-throwing rate
# ---------------------------------------------------------------------------

async def bus_throwing_rate(
    db: AsyncSession, batch_id: uuid.UUID | None = None
) -> dict[str, Any]:
    """Wolf voting against wolf teammate / total wolf votes.

    'Bus-throwing' = a werewolf voting to eliminate their own teammate.
    """
    game_ids = await _game_ids_for_batch(db, batch_id)
    if not game_ids:
        return {"by_profile": {}, "overall": {"bus_throws": 0, "total_wolf_votes": 0, "rate": 0.0}}

    players_by_game = await _load_players_by_game(db, game_ids)

    # Identify wolf players and their profiles per game
    wolf_ids_by_game: dict[uuid.UUID, set[str]] = {}
    wolf_profiles: dict[str, str] = {}
    for gid, plist in players_by_game.items():
        wolves = set()
        for p in plist:
            if p.role == "werewolf":
                wolves.add(str(p.id))
                wolf_profiles[str(p.id)] = p.persuasion_profile or "baseline"
        wolf_ids_by_game[gid] = wolves

    # Load all votes
    result = await db.execute(
        select(Vote).where(Vote.game_id.in_(game_ids))
    )
    all_votes = result.scalars().all()

    bus_by_profile: dict[str, dict[str, int]] = {
        p: {"bus": 0, "total": 0} for p in _PROFILES
    }
    total_bus = 0
    total_wolf_votes = 0

    for v in all_votes:
        voter_id = str(v.voter)
        target_id = str(v.target)
        wolves = wolf_ids_by_game.get(v.game_id, set())

        if voter_id not in wolves:
            continue

        profile = wolf_profiles.get(voter_id, "baseline")
        if profile not in _PROFILES:
            profile = "baseline"

        bus_by_profile[profile]["total"] += 1
        total_wolf_votes += 1

        if target_id in wolves:
            bus_by_profile[profile]["bus"] += 1
            total_bus += 1

    by_profile: dict[str, dict[str, Any]] = {}
    for profile in _PROFILES:
        total = bus_by_profile[profile]["total"]
        bus = bus_by_profile[profile]["bus"]
        rate = bus / total if total > 0 else 0.0
        by_profile[profile] = {
            "bus_throws": bus,
            "total_wolf_votes": total,
            "rate": round(rate, 4),
        }

    overall_rate = total_bus / total_wolf_votes if total_wolf_votes > 0 else 0.0

    return {
        "by_profile": by_profile,
        "overall": {
            "bus_throws": total_bus,
            "total_wolf_votes": total_wolf_votes,
            "rate": round(overall_rate, 4),
        },
    }


# ---------------------------------------------------------------------------
# 7. Bandwagon dynamics
# ---------------------------------------------------------------------------

async def bandwagon_dynamics(
    db: AsyncSession, batch_id: uuid.UUID | None = None
) -> dict[str, Any]:
    """Time (in debate turns) from first accusation to majority vote forming.

    For each game-round, find:
    - First speech that mentions a specific player accusingly
    - When majority of voters converge on that target
    Returns the gap in debate turn count.
    """
    game_ids = await _game_ids_for_batch(db, batch_id)
    if not game_ids:
        return {"events": [], "summary": {"mean": 0.0, "count": 0}}

    players_by_game = await _load_players_by_game(db, game_ids)

    # Accusation keywords
    accusation_words = {
        "suspect", "suspicious", "accuse", "lying", "liar", "wolf",
        "werewolf", "eliminate", "vote", "kill", "guilty", "blame",
        "untrustworthy", "dishonest", "deceiving", "shady",
    }

    all_events: list[dict[str, Any]] = []

    for gid in game_ids:
        game_players = players_by_game.get(gid, [])
        player_names = {str(p.id): p.agent_name for p in game_players}

        # Load speech turns for this game
        result = await db.execute(
            select(Turn)
            .where(Turn.game_id == gid)
            .where(Turn.phase == "DAY_SPEECH")
            .order_by(Turn.round_number, Turn.created_at)
        )
        speeches = result.scalars().all()

        # Load votes for this game
        result = await db.execute(
            select(Vote)
            .where(Vote.game_id == gid)
            .order_by(Vote.round_number)
        )
        votes = result.scalars().all()

        votes_by_round: dict[int, list[Vote]] = defaultdict(list)
        for v in votes:
            votes_by_round[v.round_number].append(v)

        speeches_by_round: dict[int, list[Turn]] = defaultdict(list)
        for s in speeches:
            speeches_by_round[s.round_number].append(s)

        for round_num in sorted(speeches_by_round.keys()):
            round_speeches = speeches_by_round[round_num]
            round_votes = votes_by_round.get(round_num, [])
            if not round_votes:
                continue

            # Find the majority vote target
            vote_counts: dict[str, int] = defaultdict(int)
            for v in round_votes:
                vote_counts[str(v.target)] += 1

            if not vote_counts:
                continue

            majority_target = max(vote_counts, key=vote_counts.get)  # type: ignore[arg-type]
            majority_count = vote_counts[majority_target]
            total_voters = len(round_votes)

            if majority_count <= total_voters / 2:
                # No clear majority
                continue

            # Find first speech that accuses the majority target
            first_accusation_idx: int | None = None
            target_name = player_names.get(majority_target, "")

            for idx, speech in enumerate(round_speeches):
                text = (speech.public_statement or "").lower()
                # Check if speech mentions the target and contains accusation words
                name_mentioned = (
                    target_name and target_name.lower() in text
                )
                has_accusation = any(w in text for w in accusation_words)

                if name_mentioned and has_accusation:
                    first_accusation_idx = idx
                    break

            if first_accusation_idx is not None:
                # The "time to majority" is the number of speeches from
                # first accusation to end of debate (all speeches)
                debate_turns_to_majority = len(round_speeches) - first_accusation_idx
                all_events.append({
                    "game_id": str(gid),
                    "round_number": round_num,
                    "target_id": majority_target,
                    "first_accusation_turn": first_accusation_idx,
                    "total_debate_turns": len(round_speeches),
                    "turns_to_majority": debate_turns_to_majority,
                })

    # Summary
    if all_events:
        vals = [e["turns_to_majority"] for e in all_events]
        mean = sum(vals) / len(vals)
    else:
        mean = 0.0

    return {
        "events": all_events,
        "summary": {
            "mean": round(mean, 2),
            "count": len(all_events),
        },
    }
