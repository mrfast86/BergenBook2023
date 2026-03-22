"""
Handicap calculation service.

Formula (World Handicap System simplified):
  Differential = (AdjustedScore - CourseRating) * 113 / SlopeRating
  HandicapIndex = Average of best 8 differentials from last 20 rounds * 0.96
"""
from typing import Optional
from sqlalchemy.orm import Session
from db.models import Round, RoundPlayer, Score, Course, HandicapHistory, Player


def score_differential(
    adjusted_score: int,
    course_rating: float,
    slope_rating: float,
) -> float:
    """Calculate a single score differential."""
    return round((adjusted_score - course_rating) * 113 / slope_rating, 1)


def calculate_handicap_index(differentials: list[float]) -> float:
    """
    Given a list of score differentials (most recent first),
    return the handicap index.

    Rules (simplified WHS):
      - Use last 20 rounds
      - Pick best 8 differentials
      - Average them * 0.96
    """
    pool = sorted(differentials[:20])
    best = pool[:8]
    if not best:
        return 0.0
    return round(sum(best) / len(best) * 0.96, 1)


def recalculate_player_handicap(player_id: int, db: Session) -> Optional[float]:
    """
    Recompute handicap for a player from stored rounds and persist to history.
    Returns new handicap index or None if no rounds found.
    """
    # Fetch all RoundPlayer rows for this player, ordered newest first
    rp_rows = (
        db.query(RoundPlayer)
        .filter(RoundPlayer.player_id == player_id)
        .join(Round)
        .order_by(Round.date.desc())
        .all()
    )

    if not rp_rows:
        return None

    differentials = []
    for rp in rp_rows:
        if rp.total_score is None:
            continue
        course = db.query(Course).filter(Course.id == rp.round.course_id).first()
        if course is None:
            cr, sr = 72.0, 113.0
        else:
            cr, sr = course.course_rating, course.slope_rating

        differentials.append(score_differential(rp.total_score, cr, sr))

    if not differentials:
        return None

    new_index = calculate_handicap_index(differentials)

    # Save to history
    history = HandicapHistory(
        player_id=player_id,
        handicap_index=new_index,
        rounds_used=len(differentials),
    )
    db.add(history)

    # Update RoundPlayer handicap_at_time for latest entry
    rp_rows[0].handicap_at_time = new_index
    db.commit()

    return new_index


def get_current_handicap(player_id: int, db: Session) -> Optional[float]:
    """Return the most recent handicap index for a player."""
    latest = (
        db.query(HandicapHistory)
        .filter(HandicapHistory.player_id == player_id)
        .order_by(HandicapHistory.calculated_at.desc())
        .first()
    )
    return latest.handicap_index if latest else None


def compute_totals_for_round(round_id: int, db: Session) -> dict[int, int]:
    """Return {player_id: total_strokes} for a round."""
    scores = db.query(Score).filter(Score.round_id == round_id).all()
    totals: dict[int, int] = {}
    for s in scores:
        totals[s.player_id] = totals.get(s.player_id, 0) + s.strokes
    return totals
