"""
Player service — fuzzy name matching and NameMapping management.
"""
from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy.orm import Session
from db.models import Player, NameMapping


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def find_best_match(raw_name: str, players: list[Player], threshold: float = 0.5) -> Optional[Player]:
    """
    Return the best matching Player for a raw OCR name, or None if below threshold.
    Checks NameMappings first (exact), then fuzzy match against player names.
    """
    if not players:
        return None

    best_player = None
    best_score = 0.0

    for p in players:
        score = _similarity(raw_name, p.name)
        if score > best_score:
            best_score = score
            best_player = p

    if best_score >= threshold:
        return best_player
    return None


def resolve_names(raw_names: list[str], db: Session) -> dict[str, Optional[int]]:
    """
    Given a list of raw OCR names, return {raw_name: player_id or None}.
    Checks NameMappings table first for known aliases.
    """
    all_players = db.query(Player).all()
    all_mappings = db.query(NameMapping).all()

    # Build alias lookup: raw_name_lower -> player_id
    alias_map: dict[str, int] = {}
    for nm in all_mappings:
        alias_map[nm.raw_name.lower().strip()] = nm.player_id

    result: dict[str, Optional[int]] = {}
    for raw in raw_names:
        key = raw.lower().strip()

        # Check exact mapping first
        if key in alias_map:
            result[raw] = alias_map[key]
            continue

        # Fuzzy match
        match = find_best_match(raw, all_players)
        result[raw] = match.id if match else None

    return result


def save_name_mapping(raw_name: str, player_id: int, db: Session, confidence: float = 1.0):
    """Upsert a NameMapping entry."""
    existing = (
        db.query(NameMapping)
        .filter(NameMapping.raw_name == raw_name, NameMapping.player_id == player_id)
        .first()
    )
    if existing:
        existing.confidence_score = confidence
        from sqlalchemy.sql import func
        existing.last_used = func.now()
    else:
        nm = NameMapping(raw_name=raw_name, player_id=player_id, confidence_score=confidence)
        db.add(nm)
    db.commit()


def get_or_create_player(name: str, db: Session) -> Player:
    """Return existing player by exact name match or create a new one."""
    existing = db.query(Player).filter(Player.name == name).first()
    if existing:
        return existing
    player = Player(name=name)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def list_players(db: Session) -> list[Player]:
    return db.query(Player).order_by(Player.name).all()
