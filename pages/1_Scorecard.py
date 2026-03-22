"""
Scorecard Capture Page
Flow: Upload photo → OCR → Edit grid → Map players → Save → Handicap update
"""
import os
import sys
import uuid
import datetime

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import init_db, get_session
from db.models import Course, Round, RoundPlayer, Score, Player as PlayerModel
from services.ocr_service import extract_scorecard
from services.player_service import (
    resolve_names,
    save_name_mapping,
    get_or_create_player,
    list_players,
)
from services.handicap_service import recalculate_player_handicap
from auth.session import is_logged_in
from components.styles import inject_global_css
from components.nav import render_nav

st.set_page_config(
    page_title="Scorecard · BergenBook",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()

init_db()
render_nav()

st.title("⛳ Scorecard Capture")

# ── Progress indicator ────────────────────────────────────────────────────────
STEPS = ["Upload", "Edit Scores", "Map Players", "Save"]
STEP_KEYS = ["upload", "edit", "map", "save"]

def _step_idx(key):
    return STEP_KEYS.index(key) if key in STEP_KEYS else 0

# ── Session state init ────────────────────────────────────────────────────────
for key, default in [
    ("ocr_result", None),
    ("score_df", None),
    ("player_names", []),
    ("step", "upload"),
    ("image_path", None),
    ("player_mappings", {}),
    ("new_player_names", {}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Progress bar
current = _step_idx(st.session_state.step)
st.progress((current) / (len(STEPS) - 1) if current > 0 else 0.01)
cols = st.columns(len(STEPS))
for i, (label, col) in enumerate(zip(STEPS, cols)):
    style = "color:#7bc47f;font-weight:700" if i == current else "color:#555"
    col.markdown(f"<div style='{style};text-align:center'>{i+1}. {label}</div>", unsafe_allow_html=True)
st.markdown("---")


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_empty_df(n_players: int, n_holes: int, names: list) -> pd.DataFrame:
    df = pd.DataFrame(
        {f"H{h+1}": [4] * n_players for h in range(n_holes)},
        index=names,
    )
    df.index.name = "Player"
    return df


def build_df_from_ocr(players: list, scores: list, holes: int) -> pd.DataFrame:
    data = {}
    for h in range(holes):
        data[f"H{h+1}"] = [row[h] if h < len(row) else 4 for row in scores]
    df = pd.DataFrame(data, index=players)
    df.index.name = "Player"
    return df


def save_image_bytes(file_obj, ext: str = "jpg") -> str:
    """Save an uploaded file or camera capture to disk. Returns path."""
    os.makedirs("uploads", exist_ok=True)
    # file_uploader objects have a .name; camera_input objects don't
    if hasattr(file_obj, "name") and "." in file_obj.name:
        ext = file_obj.name.rsplit(".", 1)[-1]
    path = f"uploads/{uuid.uuid4().hex}.{ext}"
    file_obj.seek(0)
    with open(path, "wb") as f:
        f.write(file_obj.read())
    return path


def _render_ai_status(ocr: dict):
    """Prominent status bar showing what the AI found."""
    error   = ocr.get("error", "")
    players = ocr.get("players", [])
    scores  = ocr.get("scores", [])
    holes   = ocr.get("holes", 0)
    raw     = ocr.get("raw_text", "")

    if error:
        if "no_api_key" in error:
            st.error("**No API key** — add `GEMINI_API_KEY` to `.streamlit/secrets.toml` and restart.")
        else:
            st.error(f"**AI error:** {error}")
        return

    if not raw:
        st.warning("AI was not called — no response received.")
        return

    if scores:
        st.success(
            f"**Gemini extracted:** {len(players)} player(s) · {holes} holes  "
            f"— players: {', '.join(players)}"
        )
    else:
        st.warning(
            "**Gemini responded but returned no scores.** "
            "The raw response is shown below — Gemini may have failed to parse the image."
        )


def _render_ocr_debug(ocr: dict):
    """Render AI analysis diagnostic."""
    raw_text = ocr.get("raw_text", "")
    error    = ocr.get("error", "")

    if error:
        st.error(f"**Error:** {error}")
        if "no_api_key" in (error or ""):
            st.info("Set the `ANTHROPIC_API_KEY` environment variable and restart the app.")
        return

    if raw_text:
        st.caption("Raw response from Claude:")
        st.code(raw_text, language="json")


def _run_ocr(image_source, manual_players: int, manual_holes: int):
    """Run OCR on a file/camera object and update session state."""
    image_source.seek(0)
    with st.spinner("Analyzing scorecard with AI…"):
        result = extract_scorecard(image_source.read())

    if result["error"]:
        st.warning(f"OCR issue: {result['error']} — edit scores manually below.")
        names = [f"Player {i+1}" for i in range(manual_players)]
        st.session_state.score_df = build_empty_df(manual_players, manual_holes, names)
        st.session_state.player_names = names
    else:
        players = result["players"] or [f"Player {i+1}" for i in range(manual_players)]
        # Use manual_holes when OCR found no scores (parse defaults to 9 on empty)
        holes_to_use = result["holes"] if result["scores"] else manual_holes
        scores = result["scores"] or [[4] * holes_to_use] * len(players)
        st.session_state.score_df = build_df_from_ocr(players, scores, holes_to_use)
        st.session_state.player_names = players
        if result["scores"]:
            st.success(f"Extracted {len(players)} players × {holes_to_use} holes.")
        else:
            st.warning(f"OCR ran but found no scores — check the Raw OCR output below and edit manually.")

    image_source.seek(0)
    st.session_state.image_path = save_image_bytes(image_source)
    st.session_state.ocr_result = result
    st.session_state.step = "edit"
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Get scorecard image
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.step == "upload":
    st.subheader("Add a Round")

    if not is_logged_in():
        st.info("You can capture and edit scores without an account. Sign in to save rounds and track your handicap.", icon="ℹ️")

    # ── Resume from previous upload ────────────────────────────────────────
    prev_path = st.session_state.get("image_path")
    if prev_path and os.path.exists(prev_path):
        st.info("You have a previous upload. Resume from where you left off or upload a new image below.")
        prev_col1, prev_col2 = st.columns([2, 1])
        prev_col1.image(prev_path, caption="Previous upload", use_container_width=True)
        with prev_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("↩ Back to Edit Scores", use_container_width=True, type="primary", key="resume_edit"):
                st.session_state.step = "edit"
                st.rerun()
            if st.button("🔍 Re-run OCR", use_container_width=True, key="rerun_ocr"):
                with open(prev_path, "rb") as f:
                    import io
                    img_bytes = io.BytesIO(f.read())
                cfg_col1_val = st.session_state.get("manual_players", 4)
                cfg_col2_val = st.session_state.get("manual_holes", 18)
                img_bytes.seek(0)
                with st.spinner("Analyzing scorecard with AI…"):
                    result = extract_scorecard(img_bytes.read())
                if result["error"]:
                    st.warning(f"OCR issue: {result['error']} — edit scores manually.")
                    names = [f"Player {i+1}" for i in range(cfg_col1_val)]
                    st.session_state.score_df = build_empty_df(cfg_col1_val, cfg_col2_val, names)
                    st.session_state.player_names = names
                else:
                    players = result["players"] or [f"Player {i+1}" for i in range(cfg_col1_val)]
                    holes_to_use = result["holes"] if result["scores"] else cfg_col2_val
                    scores = result["scores"] or [[4] * holes_to_use] * len(players)
                    st.session_state.score_df = build_df_from_ocr(players, scores, holes_to_use)
                    st.session_state.player_names = players
                st.session_state.ocr_result = result
                st.session_state.step = "edit"
                st.rerun()
        st.markdown("---")
        st.caption("Or upload a new image:")

    # Shared settings row
    cfg_col1, cfg_col2, _ = st.columns([1, 1, 2])
    manual_players = cfg_col1.number_input("Players (fallback)", 1, 4, 4, key="manual_players")
    manual_holes   = cfg_col2.selectbox("Holes (fallback)", [9, 18], index=1, key="manual_holes")

    st.markdown("<br>", unsafe_allow_html=True)

    tab_cam, tab_upload, tab_manual = st.tabs(["📷  Camera", "🖼  Upload Photo", "✏️  Enter Manually"])

    # ── Tab 1: Camera ──────────────────────────────────────────────────────
    with tab_cam:
        st.caption("Point your camera at the scorecard and snap a photo.")
        camera_img = st.camera_input("Take a photo of the scorecard", label_visibility="collapsed")

        if camera_img:
            col_a, col_b = st.columns([2, 1])
            col_a.image(camera_img, caption="Captured scorecard", use_container_width=True)
            with col_b:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔍 Extract Scores", use_container_width=True, type="primary", key="ocr_cam"):
                    _run_ocr(camera_img, manual_players, manual_holes)
                if st.button("✏️ Enter Manually", use_container_width=True, key="manual_from_cam"):
                    names = [f"Player {i+1}" for i in range(manual_players)]
                    st.session_state.score_df = build_empty_df(manual_players, manual_holes, names)
                    st.session_state.player_names = names
                    st.session_state.image_path = save_image_bytes(camera_img)
                    st.session_state.step = "edit"
                    st.rerun()

    # ── Tab 2: File upload ─────────────────────────────────────────────────
    with tab_upload:
        st.caption("Upload a photo from your device.")
        uploaded = st.file_uploader(
            "Choose a scorecard image",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
        )
        if uploaded:
            col_a, col_b = st.columns([2, 1])
            uploaded.seek(0)
            col_a.image(uploaded, caption="Uploaded scorecard", use_container_width=True)
            with col_b:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔍 Extract Scores", use_container_width=True, type="primary", key="ocr_file"):
                    _run_ocr(uploaded, manual_players, manual_holes)
                if st.button("✏️ Enter Manually", use_container_width=True, key="manual_from_file"):
                    names = [f"Player {i+1}" for i in range(manual_players)]
                    st.session_state.score_df = build_empty_df(manual_players, manual_holes, names)
                    st.session_state.player_names = names
                    st.session_state.image_path = save_image_bytes(uploaded)
                    st.session_state.step = "edit"
                    st.rerun()

    # ── Tab 3: Manual ──────────────────────────────────────────────────────
    with tab_manual:
        st.caption("No photo? Enter scores directly into the grid.")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Open Score Grid →", use_container_width=True, type="primary", key="open_manual"):
            names = [f"Player {i+1}" for i in range(manual_players)]
            st.session_state.score_df = build_empty_df(manual_players, manual_holes, names)
            st.session_state.player_names = names
            st.session_state.image_path = None
            st.session_state.step = "edit"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Edit score grid
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == "edit":
    st.subheader("Review & Edit Scores")

    if st.session_state.image_path and os.path.exists(st.session_state.image_path):
        with st.expander("View uploaded photo"):
            st.image(st.session_state.image_path, use_container_width=True)

    ocr = st.session_state.get("ocr_result")
    if ocr:
        _render_ai_status(ocr)
        if ocr.get("raw_text") or ocr.get("error"):
            with st.expander("🤖 AI Raw Response"):
                _render_ocr_debug(ocr)

    df = st.session_state.score_df

    st.caption("Click any cell to edit. Values must be 1–15 per hole.")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        key="score_editor",
    )

    # Totals
    totals = edited_df.sum(axis=1).rename("Total")
    st.dataframe(totals.to_frame().T, use_container_width=True, hide_index=False)

    # Validation
    errors = []
    for player in edited_df.index:
        for col in edited_df.columns:
            val = edited_df.loc[player, col]
            try:
                v = int(val)
                if not (1 <= v <= 15):
                    errors.append(f"{player} – {col}: {v} (must be 1–15)")
            except (ValueError, TypeError):
                errors.append(f"{player} – {col}: not a number")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back"):
            st.session_state.step = "upload"
            st.rerun()
    with col2:
        if errors:
            with st.expander(f"⚠️ {len(errors)} validation error(s) — fix before continuing"):
                for e in errors:
                    st.caption(f"• {e}")
        else:
            if st.button("Next: Map Players →", type="primary", use_container_width=True):
                st.session_state.score_df = edited_df
                st.session_state.step = "map"
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Map players
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == "map":
    st.subheader("Map Players")
    st.caption("Match each detected name to an existing player, or add a new one.")

    db = get_session()
    existing_players = list_players(db)
    options = ["— Add new player —"] + [p.name for p in existing_players]
    raw_names = list(st.session_state.score_df.index)
    suggestions = resolve_names(raw_names, db)
    db.close()

    mappings: dict[str, str] = {}
    new_names: dict[str, str] = {}

    # Column headers
    hc1, hc2, hc3 = st.columns([1, 2, 2])
    hc1.markdown("<p style='color:#6ee7b7;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:0'>Detected name</p>", unsafe_allow_html=True)
    hc2.markdown("<p style='color:#6ee7b7;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:0'>Map to player</p>", unsafe_allow_html=True)
    hc3.markdown("<p style='color:#6ee7b7;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:0'>New name (if adding)</p>", unsafe_allow_html=True)
    st.divider()

    for raw in raw_names:
        suggested_id = suggestions.get(raw)
        suggested_name = next(
            (p.name for p in existing_players if p.id == suggested_id), None
        )
        default_idx = (options.index(suggested_name) if suggested_name in options else 0)

        col1, col2, col3 = st.columns([1, 2, 2])
        col1.markdown(
            f"<div style='padding:0.6rem 0;font-weight:600;color:#f0f9f1'>{raw}</div>",
            unsafe_allow_html=True,
        )
        choice = col2.selectbox(
            f"map_{raw}",
            options,
            index=default_idx,
            key=f"map_{raw}",
            label_visibility="collapsed",
        )
        mappings[raw] = choice

        if choice == "— Add new player —":
            new_name = col3.text_input(
                f"new_{raw}",
                value=raw,
                key=f"new_{raw}",
                label_visibility="collapsed",
                placeholder="Enter player name",
            )
            new_names[raw] = new_name.strip()
        else:
            col3.markdown(
                "<div style='padding:0.6rem 0;color:#6ee7b7;font-size:0.85rem'>✓ existing player</div>",
                unsafe_allow_html=True,
            )

    st.divider()
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back"):
            st.session_state.step = "edit"
            st.rerun()
    with col2:
        all_valid = all(
            mappings.get(r, "") != "— Add new player —" or bool(new_names.get(r, "").strip())
            for r in raw_names
        )
        if not all_valid:
            st.warning("Provide a name for every new player.")
        else:
            if st.button("Next: Round Details →", type="primary", use_container_width=True):
                st.session_state.player_mappings = mappings
                st.session_state.new_player_names = new_names
                st.session_state.step = "save"
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Round details + Save
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == "save":
    st.subheader("Round Details")

    if not is_logged_in():
        st.warning(
            "You need an account to save rounds and track handicaps. "
            "Your scores are ready — sign in or create a free account to save them.",
            icon="🔐",
        )
        c1, c2 = st.columns(2)
        if c1.button("Sign In / Sign Up", type="primary", use_container_width=True):
            st.switch_page("pages/0_Login.py")
        if c2.button("← Back to scores", use_container_width=True):
            st.session_state.step = "edit"
            st.rerun()
        st.stop()

    db = get_session()
    courses = db.query(Course).order_by(Course.name).all()
    course_names = [c.name for c in courses] + ["+ Add new course"]

    col1, col2 = st.columns(2)
    play_date = col1.date_input("Date played", value=datetime.date.today())
    course_choice = col2.selectbox("Course", course_names)

    new_course_name, new_slope, new_rating, new_par = "", 113.0, 72.0, 72
    if course_choice == "+ Add new course":
        with st.expander("New course details", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            new_course_name = c1.text_input("Course name")
            new_slope = c2.number_input("Slope rating", 55.0, 155.0, 113.0)
            new_rating = c3.number_input("Course rating", 60.0, 82.0, 72.0)
            new_par = int(c4.number_input("Par", 54, 74, 72))

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back"):
            st.session_state.step = "map"
            st.rerun()

    with col2:
        if st.button("💾 Save Round", type="primary", use_container_width=True):
            save_error = None

            # Validate new course name
            if course_choice == "+ Add new course" and not new_course_name.strip():
                st.error("Course name is required.")
                st.stop()

            try:
                # ── Course ──────────────────────────────────────────────────
                if course_choice == "+ Add new course":
                    course = Course(
                        name=new_course_name.strip(),
                        slope_rating=new_slope,
                        course_rating=new_rating,
                        par=new_par,
                    )
                    db.add(course)
                    db.flush()
                else:
                    course = next(c for c in courses if c.name == course_choice)

                # ── Players ─────────────────────────────────────────────────
                mappings = st.session_state.player_mappings
                new_player_names_map = st.session_state.new_player_names
                raw_to_player: dict[str, PlayerModel] = {}

                for raw, choice in mappings.items():
                    if choice == "— Add new player —":
                        final_name = new_player_names_map.get(raw, raw)
                        player = get_or_create_player(final_name, db)
                        save_name_mapping(raw, player.id, db)
                    else:
                        player = db.query(PlayerModel).filter_by(name=choice).first()
                        if player is None:
                            player = get_or_create_player(choice, db)
                        save_name_mapping(raw, player.id, db, confidence=0.9)
                    raw_to_player[raw] = player

                # ── Round ────────────────────────────────────────────────────
                round_obj = Round(
                    course_id=course.id,
                    date=play_date,
                    image_url=st.session_state.image_path,
                )
                db.add(round_obj)
                db.flush()

                # ── Scores ───────────────────────────────────────────────────
                score_df = st.session_state.score_df

                for raw_name, player in raw_to_player.items():
                    total = 0
                    for h_idx, col_name in enumerate(score_df.columns):
                        strokes = int(score_df.loc[raw_name, col_name])
                        db.add(Score(
                            round_id=round_obj.id,
                            player_id=player.id,
                            hole_number=h_idx + 1,
                            strokes=strokes,
                        ))
                        total += strokes

                    db.add(RoundPlayer(
                        round_id=round_obj.id,
                        player_id=player.id,
                        total_score=total,
                    ))

                db.commit()

                # ── Handicaps ────────────────────────────────────────────────
                for player in raw_to_player.values():
                    recalculate_player_handicap(player.id, db)

                st.success("Round saved! Handicaps updated.")
                st.balloons()

                # Reset state
                for k in ["ocr_result", "score_df", "player_names", "image_path",
                          "player_mappings", "new_player_names"]:
                    st.session_state[k] = None
                st.session_state.step = "done"
                st.rerun()

            except Exception as exc:
                db.rollback()
                st.error(f"Failed to save round: {exc}")
            finally:
                db.close()

elif st.session_state.step == "done":
    st.success("Round saved successfully!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add another round"):
            st.session_state.step = "upload"
            st.rerun()
    with col2:
        if st.button("View Leaderboard →"):
            st.switch_page("pages/2_Leaderboard.py")
