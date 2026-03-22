"""
Players Management Page
- View all players + current handicap
- Add / rename players
- View per-player round history
- Edit or delete name mappings
"""
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import init_db, get_session
from db.models import Player, NameMapping, RoundPlayer, Round, Course, HandicapHistory
from services.handicap_service import get_current_handicap
from auth.session import require_auth
from components.styles import inject_global_css
from components.nav import render_nav

st.set_page_config(
    page_title="Players · BergenBook",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()

init_db()
require_auth()
render_nav()

st.title("👤 Players")

db = get_session()

tab_all, tab_add, tab_detail = st.tabs(["All Players", "Add Player", "Player Detail"])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — All Players
# ─────────────────────────────────────────────────────────────────────────────
with tab_all:
    players = db.query(Player).order_by(Player.name).all()

    if not players:
        st.info("No players yet. Add one using the 'Add Player' tab.")
    else:
        rows = []
        for p in players:
            hcp = get_current_handicap(p.id, db)
            rp_count = db.query(RoundPlayer).filter(RoundPlayer.player_id == p.id).count()
            rows.append({
                "Name": p.name,
                "Handicap Index": round(hcp, 1) if hcp is not None else "—",
                "Rounds Played": rp_count,
                "ID": p.id,
            })

        df = pd.DataFrame(rows)
        st.dataframe(df.drop(columns="ID"), use_container_width=True, hide_index=True)

        st.markdown("#### Rename Player")
        player_names = [p.name for p in players]
        rename_target = st.selectbox("Select player to rename", player_names, key="rename_target")
        new_name = st.text_input("New name", key="rename_new_name")

        if st.button("Rename") and new_name.strip():
            player_obj = next((p for p in players if p.name == rename_target), None)
            if player_obj:
                existing = db.query(Player).filter(Player.name == new_name.strip()).first()
                if existing and existing.id != player_obj.id:
                    st.error("A player with that name already exists.")
                else:
                    player_obj.name = new_name.strip()
                    db.commit()
                    st.success(f"Renamed to '{new_name.strip()}'.")
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Add Player
# ─────────────────────────────────────────────────────────────────────────────
with tab_add:
    st.subheader("Add New Player")
    new_player_name = st.text_input("Player name", key="new_player_name")

    if st.button("Add Player", type="primary") and new_player_name.strip():
        existing = db.query(Player).filter(Player.name == new_player_name.strip()).first()
        if existing:
            st.warning(f"'{new_player_name.strip()}' already exists.")
        else:
            player = Player(name=new_player_name.strip())
            db.add(player)
            db.commit()
            st.success(f"Added player '{new_player_name.strip()}'.")
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Player Detail
# ─────────────────────────────────────────────────────────────────────────────
with tab_detail:
    players_fresh = db.query(Player).order_by(Player.name).all()

    if not players_fresh:
        st.info("No players yet.")
    else:
        selected_name = st.selectbox(
            "Select player", [p.name for p in players_fresh], key="detail_player"
        )
        player = next((p for p in players_fresh if p.name == selected_name), None)

        if player:
            hcp = get_current_handicap(player.id, db)
            col1, col2, col3 = st.columns(3)
            col1.metric("Handicap Index", round(hcp, 1) if hcp is not None else "—")

            rp_rows = (
                db.query(RoundPlayer)
                .filter(RoundPlayer.player_id == player.id)
                .join(Round)
                .order_by(Round.date.desc())
                .all()
            )
            scores = [r.total_score for r in rp_rows if r.total_score is not None]
            col2.metric("Rounds Played", len(rp_rows))
            col3.metric("Best Score", min(scores) if scores else "—")

            # Round history for this player
            st.markdown("#### Round History")
            if rp_rows:
                hist_rows = []
                for rp in rp_rows:
                    r = rp.round
                    course_name = r.course.name if r.course else "—"
                    hist_rows.append({
                        "Date": str(r.date),
                        "Course": course_name,
                        "Score": rp.total_score or "—",
                        "Handicap at Time": round(rp.handicap_at_time, 1) if rp.handicap_at_time else "—",
                    })
                st.dataframe(pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)

                # Score chart
                if len(scores) >= 2:
                    dates = [str(rp.round.date) for rp in rp_rows if rp.total_score is not None]
                    chart_df = pd.DataFrame({"Score": scores}, index=dates[::-1])
                    st.line_chart(chart_df)
            else:
                st.caption("No rounds played yet.")

            # Handicap history
            st.markdown("#### Handicap History")
            hcp_history = (
                db.query(HandicapHistory)
                .filter(HandicapHistory.player_id == player.id)
                .order_by(HandicapHistory.calculated_at.desc())
                .limit(20)
                .all()
            )
            if hcp_history:
                hcp_rows = [
                    {
                        "Date": str(h.calculated_at)[:16],
                        "Handicap Index": h.handicap_index,
                        "Rounds Used": h.rounds_used,
                    }
                    for h in hcp_history
                ]
                st.dataframe(pd.DataFrame(hcp_rows), use_container_width=True, hide_index=True)
            else:
                st.caption("No handicap history yet.")

            # Name mappings
            st.markdown("#### OCR Name Mappings")
            st.caption("These are the aliases the system has learned for this player.")
            mappings = (
                db.query(NameMapping)
                .filter(NameMapping.player_id == player.id)
                .order_by(NameMapping.last_used.desc())
                .all()
            )
            if mappings:
                map_rows = [
                    {
                        "Raw OCR Name": m.raw_name,
                        "Confidence": round(m.confidence_score, 2),
                        "Last Used": str(m.last_used)[:16],
                        "_id": m.id,
                    }
                    for m in mappings
                ]
                map_df = pd.DataFrame(map_rows)
                st.dataframe(map_df.drop(columns="_id"), use_container_width=True, hide_index=True)

                # Delete a mapping
                with st.expander("Delete a mapping"):
                    del_raw = st.selectbox(
                        "Select mapping to delete",
                        [m["Raw OCR Name"] for m in map_rows],
                        key="del_mapping",
                    )
                    if st.button("Delete mapping", type="secondary"):
                        target_id = next(
                            m["_id"] for m in map_rows if m["Raw OCR Name"] == del_raw
                        )
                        db.query(NameMapping).filter(NameMapping.id == target_id).delete()
                        db.commit()
                        st.success(f"Deleted mapping '{del_raw}'.")
                        st.rerun()
            else:
                st.caption("No mappings saved yet.")

db.close()
