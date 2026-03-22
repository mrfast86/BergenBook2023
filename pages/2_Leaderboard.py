"""
Leaderboard Page
- Group leaderboard: handicap index + average score
- Round leaderboard: scores for a specific round
- Recent rounds history
"""
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import init_db, get_session
from db.models import Player, Round, RoundPlayer, Course, HandicapHistory, Score
from services.handicap_service import get_current_handicap
from auth.session import require_auth
from components.styles import inject_global_css
from components.nav import render_nav

st.set_page_config(
    page_title="Leaderboard · BergenBook",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()

init_db()
require_auth()
render_nav()

st.title("🏆 Leaderboard")

db = get_session()

# ─────────────────────────────────────────────────────────────────────────────
# TAB LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
tab_group, tab_round, tab_history = st.tabs(["Group Standings", "Round View", "Round History"])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Group Standings
# ─────────────────────────────────────────────────────────────────────────────
with tab_group:
    st.subheader("Group Standings")

    players = db.query(Player).order_by(Player.name).all()

    if not players:
        st.info("No players yet. Add a round on the Scorecard page.")
    else:
        rows = []
        for p in players:
            hcp = get_current_handicap(p.id, db)

            # All RoundPlayer rows for this player
            rp_rows = (
                db.query(RoundPlayer)
                .filter(RoundPlayer.player_id == p.id)
                .all()
            )
            rounds_played = len(rp_rows)
            scores_with_val = [r.total_score for r in rp_rows if r.total_score is not None]
            avg_score = round(sum(scores_with_val) / len(scores_with_val), 1) if scores_with_val else None
            best_score = min(scores_with_val) if scores_with_val else None

            rows.append({
                "Player": p.name,
                "Handicap Index": hcp if hcp is not None else "—",
                "Avg Score": avg_score if avg_score is not None else "—",
                "Best Score": best_score if best_score is not None else "—",
                "Rounds": rounds_played,
            })

        df = pd.DataFrame(rows)

        # Sort by handicap index (numeric only)
        def hcp_sort_key(v):
            try:
                return float(v)
            except (ValueError, TypeError):
                return 9999.0

        df["_hcp_sort"] = df["Handicap Index"].map(hcp_sort_key)
        df = df.sort_values("_hcp_sort").drop(columns="_hcp_sort").reset_index(drop=True)
        df.index += 1  # rank from 1

        st.dataframe(df, use_container_width=True)

        # Handicap trend chart
        st.markdown("#### Handicap Trend")
        trend_player = st.selectbox("Select player", [p.name for p in players], key="trend_player")

        selected_player = next((p for p in players if p.name == trend_player), None)
        if selected_player:
            history = (
                db.query(HandicapHistory)
                .filter(HandicapHistory.player_id == selected_player.id)
                .order_by(HandicapHistory.calculated_at)
                .all()
            )
            if len(history) >= 2:
                trend_df = pd.DataFrame({
                    "Date": [h.calculated_at for h in history],
                    "Handicap Index": [h.handicap_index for h in history],
                })
                trend_df = trend_df.set_index("Date")
                st.line_chart(trend_df)
            else:
                st.caption("Not enough rounds for a trend chart (need 2+).")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Round View
# ─────────────────────────────────────────────────────────────────────────────
with tab_round:
    st.subheader("Round Scorecard")

    rounds = (
        db.query(Round)
        .order_by(Round.date.desc())
        .all()
    )

    if not rounds:
        st.info("No rounds recorded yet.")
    else:
        round_labels = []
        for r in rounds:
            course_name = r.course.name if r.course else "Unknown course"
            round_labels.append(f"{r.date}  —  {course_name}")

        selected_label = st.selectbox("Select round", round_labels, key="round_select")
        selected_round = rounds[round_labels.index(selected_label)]

        # Player results for this round
        rp_rows = (
            db.query(RoundPlayer)
            .filter(RoundPlayer.round_id == selected_round.id)
            .all()
        )

        if not rp_rows:
            st.warning("No scores saved for this round.")
        else:
            course = selected_round.course
            par = course.par if course else 72

            summary_rows = []
            for rp in sorted(rp_rows, key=lambda x: x.total_score or 999):
                player_name = rp.player.name if rp.player else "Unknown"
                total = rp.total_score or "—"
                diff = (total - par) if isinstance(total, int) else "—"
                hcp = rp.handicap_at_time
                net = (total - round(hcp)) if isinstance(total, int) and hcp is not None else "—"
                summary_rows.append({
                    "Player": player_name,
                    "Total": total,
                    "vs Par": f"+{diff}" if isinstance(diff, int) and diff > 0 else str(diff),
                    "Handicap": round(hcp, 1) if hcp else "—",
                    "Net Score": net,
                })

            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            # Hole-by-hole breakdown
            with st.expander("Hole-by-hole breakdown"):
                scores = (
                    db.query(Score)
                    .filter(Score.round_id == selected_round.id)
                    .order_by(Score.player_id, Score.hole_number)
                    .all()
                )

                if scores:
                    pivot: dict[str, dict] = {}
                    for s in scores:
                        pname = s.player.name if s.player else f"P{s.player_id}"
                        if pname not in pivot:
                            pivot[pname] = {}
                        pivot[pname][f"H{s.hole_number}"] = s.strokes

                    pivot_df = pd.DataFrame(pivot).T
                    pivot_df.index.name = "Player"
                    pivot_df["Total"] = pivot_df.sum(axis=1)
                    st.dataframe(pivot_df, use_container_width=True)

            # Show scorecard image if available
            if selected_round.image_url and os.path.exists(selected_round.image_url):
                with st.expander("View original scorecard photo"):
                    st.image(selected_round.image_url, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Round History
# ─────────────────────────────────────────────────────────────────────────────
with tab_history:
    st.subheader("Recent Rounds")

    rounds_all = (
        db.query(Round)
        .order_by(Round.date.desc())
        .limit(50)
        .all()
    )

    if not rounds_all:
        st.info("No rounds yet.")
    else:
        hist_rows = []
        for r in rounds_all:
            course_name = r.course.name if r.course else "—"
            rp_list = r.round_players
            players_str = ", ".join(
                rp.player.name for rp in rp_list if rp.player
            ) if rp_list else "—"
            scores_str = ", ".join(
                str(rp.total_score) for rp in sorted(rp_list, key=lambda x: x.total_score or 999)
                if rp.total_score is not None
            ) if rp_list else "—"

            hist_rows.append({
                "Date": str(r.date),
                "Course": course_name,
                "Players": players_str,
                "Scores": scores_str,
            })

        st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)

db.close()
