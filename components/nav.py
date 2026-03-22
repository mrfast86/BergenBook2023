"""
Shared sidebar navigation rendered on every page.
"""
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth.session import is_logged_in, current_user, logout


def render_nav():
    """Render the persistent left-sidebar navigation."""
    with st.sidebar:
        # ── Logo / brand ─────────────────────────────────────────────────
        st.markdown(
            "<div style='padding:0.75rem 0.5rem 0.4rem'>"
            "<span style='font-size:1.5rem'>⛳</span>"
            "<span style='font-size:1.1rem;font-weight:700;"
            "color:#4ade80;margin-left:0.5rem;vertical-align:middle'>"
            "BergenBook</span>"
            "</div>"
            "<p style='color:#6ee7b7;font-size:0.75rem;margin:0 0 0.5rem 0.5rem'>"
            "Bergen County Golf</p>",
            unsafe_allow_html=True,
        )
        st.divider()

        # ── Navigation links ──────────────────────────────────────────────
        st.page_link("BergenBookSteamlit.py", label="Tee Time Booking", icon="📅")

        st.markdown(
            "<p style='color:#6ee7b7;font-size:0.7rem;font-weight:700;"
            "text-transform:uppercase;letter-spacing:1.2px;"
            "margin:1.1rem 0 0.3rem 0.6rem'>Scorecard</p>",
            unsafe_allow_html=True,
        )

        st.page_link("pages/1_Scorecard.py",   label="Add Round",   icon="📷")
        st.page_link("pages/2_Leaderboard.py", label="Leaderboard", icon="🏆")
        st.page_link("pages/3_Players.py",     label="Players",     icon="👤")

        # ── User widget ───────────────────────────────────────────────────
        st.divider()

        if is_logged_in():
            user = current_user()
            col_av, col_info = st.columns([1, 3])
            if user.get("avatar"):
                col_av.image(user["avatar"], width=36)
            else:
                col_av.markdown(
                    "<div style='width:34px;height:34px;border-radius:50%;"
                    "background:#166534;display:flex;align-items:center;"
                    "justify-content:center;font-size:1rem;color:#4ade80'>👤</div>",
                    unsafe_allow_html=True,
                )
            col_info.markdown(
                f"<span style='font-size:0.82rem;font-weight:600;"
                f"color:#f0f9f1'>{user['name']}</span><br>"
                f"<span style='font-size:0.72rem;color:#6ee7b7'>"
                f"{user.get('email','')}</span>",
                unsafe_allow_html=True,
            )
            if st.button("Sign Out", key="_nav_signout", use_container_width=True):
                logout()
                st.switch_page("pages/0_Login.py")
        else:
            st.markdown(
                "<p style='color:#86efac;font-size:0.78rem;margin:0 0 0.5rem 0.1rem'>"
                "Sign in to save rounds &amp; track handicap</p>",
                unsafe_allow_html=True,
            )
            if st.button("Sign In / Sign Up", key="_nav_signin", use_container_width=True):
                st.switch_page("pages/0_Login.py")
