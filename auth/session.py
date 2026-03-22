"""
Session management helpers.
Stores authenticated user in st.session_state.
"""
import hashlib
import secrets

import streamlit as st


# ── Password hashing (PBKDF2-HMAC-SHA256, stdlib only) ───────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"{salt}:{h.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, hash_hex = stored_hash.split(":", 1)
        h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
        return secrets.compare_digest(h.hex(), hash_hex)
    except Exception:
        return False


# ── Session state helpers ────────────────────────────────────────────────────

def login_user(user) -> None:
    """Persist user info in session after successful authentication."""
    st.session_state["user_id"] = user.id
    st.session_state["user_name"] = user.name
    st.session_state["user_email"] = user.email or ""
    st.session_state["user_avatar"] = user.avatar_url or ""


def logout() -> None:
    for key in ("user_id", "user_name", "user_email", "user_avatar"):
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    return bool(st.session_state.get("user_id"))


def current_user() -> dict:
    return {
        "id": st.session_state.get("user_id"),
        "name": st.session_state.get("user_name", ""),
        "email": st.session_state.get("user_email", ""),
        "avatar": st.session_state.get("user_avatar", ""),
    }


def require_auth() -> None:
    """
    Call at the top of any protected page.
    Redirects to the login page and stops execution if not authenticated.
    """
    if not is_logged_in():
        st.switch_page("pages/0_Login.py")
        st.stop()


# ── Sidebar user widget ───────────────────────────────────────────────────────

def render_user_sidebar() -> None:
    """
    Renders a compact user pill + logout button in the sidebar.
    Call this at the top of every protected page.
    """
    if not is_logged_in():
        return

    user = current_user()
    with st.sidebar:
        st.markdown("---")
        cols = st.columns([1, 3])
        if user["avatar"]:
            cols[0].image(user["avatar"], width=36)
        else:
            cols[0].markdown("👤")
        cols[1].markdown(f"**{user['name']}**\n\n{user['email']}")
        if st.button("Logout", use_container_width=True, key="_logout_btn"):
            logout()
            st.switch_page("pages/0_Login.py")
