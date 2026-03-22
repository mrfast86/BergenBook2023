"""
Login / Signup Page
"""
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import init_db, get_session
from db.models import User
from auth.session import hash_password, verify_password, login_user, is_logged_in, current_user, logout
from auth.oauth import (
    GOOGLE, FACEBOOK, KAKAO, REDIRECT_URI,
    fetch_google_userinfo, fetch_facebook_userinfo, fetch_kakao_userinfo,
    find_or_create_oauth_user,
)
from components.styles import inject_global_css

init_db()

st.set_page_config(
    page_title="Sign In · BergenBook",
    page_icon="⛳",
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_global_css()

# Extra login-page styles
st.markdown("""
<style>
.login-card {
    background: #111f14;
    border: 1px solid #1e3d22;
    border-radius: 16px;
    padding: 2.2rem 2.4rem 2rem;
    margin-top: 1rem;
}
.oauth-btn > button {
    background: #1b3a1f !important;
    border: 1px solid #2d5a2d !important;
    color: #e8f5e9 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1rem !important;
}
.oauth-btn > button:hover {
    background: #2e7d32 !important;
    border-color: #7bc47f !important;
    box-shadow: 0 4px 14px rgba(46,125,50,0.35) !important;
    transform: translateY(-1px);
}
.divider-text {
    display: flex; align-items: center; gap: 0.75rem;
    color: #2d5a2d; font-size: 0.78rem; margin: 1.25rem 0;
}
.divider-text::before, .divider-text::after {
    content: ''; flex: 1; border-top: 1px solid #1e3d22;
}
</style>
""", unsafe_allow_html=True)

# ── Already logged in ─────────────────────────────────────────────────────────
if is_logged_in():
    user = current_user()
    st.markdown(
        f"<div style='text-align:center;padding:2rem'>"
        f"<div style='font-size:3rem'>⛳</div>"
        f"<h2 style='color:#7bc47f'>Welcome back, {user['name']}</h2>"
        f"<p style='color:#546e54'>You're signed in as {user.get('email','')}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    if c1.button("Go to Scorecard", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Scorecard.py")
    if c2.button("Sign Out", use_container_width=True):
        logout()
        st.rerun()
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;padding:1.5rem 0 0.5rem'>"
    "<div style='font-size:3rem;margin-bottom:0.5rem'>⛳</div>"
    "<h1 style='margin:0;font-size:1.9rem'>BergenBook</h1>"
    "<p style='color:#546e54;margin:0.3rem 0 0;font-size:0.9rem'>"
    "Bergen County Golf · Track scores &amp; handicaps</p>"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown("<div class='login-card'>", unsafe_allow_html=True)

# ── OAuth providers ───────────────────────────────────────────────────────────
google_enabled   = bool(GOOGLE["client_id"]   and GOOGLE["client_secret"])
facebook_enabled = bool(FACEBOOK["client_id"] and FACEBOOK["client_secret"])
kakao_enabled    = bool(KAKAO["client_id"]    and KAKAO["client_secret"])

if google_enabled or facebook_enabled or kakao_enabled:
    try:
        from streamlit_oauth import OAuth2Component
        has_oauth_lib = True
    except ImportError:
        has_oauth_lib = False
        st.caption("Install `streamlit-oauth` to enable social login.")
else:
    has_oauth_lib = False

if has_oauth_lib and (google_enabled or facebook_enabled or kakao_enabled):
    n_cols = sum([google_enabled, facebook_enabled, kakao_enabled])
    cols = st.columns(n_cols)
    col_idx = 0
    g_result = fb_result = k_result = None

    if google_enabled:
        with cols[col_idx]:
            with st.container():
                st.markdown("<div class='oauth-btn'>", unsafe_allow_html=True)
                g_oauth = OAuth2Component(
                    client_id=GOOGLE["client_id"],
                    client_secret=GOOGLE["client_secret"],
                    authorize_endpoint=GOOGLE["authorize_url"],
                    token_endpoint=GOOGLE["token_url"],
                    refresh_token_endpoint=GOOGLE["token_url"],
                    revoke_token_endpoint=GOOGLE["revoke_url"],
                )
                g_result = g_oauth.authorize_button(
                    name="🔵  Google",
                    redirect_uri=REDIRECT_URI,
                    scope=GOOGLE["scope"],
                    key="google_oauth",
                    extras_params={"prompt": "consent", "access_type": "offline"},
                    use_container_width=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)
        col_idx += 1

    if facebook_enabled:
        with cols[col_idx]:
            with st.container():
                st.markdown("<div class='oauth-btn'>", unsafe_allow_html=True)
                fb_oauth = OAuth2Component(
                    client_id=FACEBOOK["client_id"],
                    client_secret=FACEBOOK["client_secret"],
                    authorize_endpoint=FACEBOOK["authorize_url"],
                    token_endpoint=FACEBOOK["token_url"],
                    refresh_token_endpoint=FACEBOOK["token_url"],
                    revoke_token_endpoint=None,
                )
                fb_result = fb_oauth.authorize_button(
                    name="🔷  Facebook",
                    redirect_uri=REDIRECT_URI,
                    scope=FACEBOOK["scope"],
                    key="facebook_oauth",
                    use_container_width=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)
        col_idx += 1

    if kakao_enabled:
        with cols[col_idx]:
            with st.container():
                st.markdown("<div class='oauth-btn'>", unsafe_allow_html=True)
                k_oauth = OAuth2Component(
                    client_id=KAKAO["client_id"],
                    client_secret=KAKAO["client_secret"],
                    authorize_endpoint=KAKAO["authorize_url"],
                    token_endpoint=KAKAO["token_url"],
                    refresh_token_endpoint=KAKAO["token_url"],
                    revoke_token_endpoint=None,
                )
                k_result = k_oauth.authorize_button(
                    name="🟡  KakaoTalk",
                    redirect_uri=REDIRECT_URI,
                    scope=KAKAO["scope"],
                    key="kakao_oauth",
                    use_container_width=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

    if g_result and "token" in g_result:
        with st.spinner("Signing in with Google..."):
            try:
                token = g_result["token"].get("access_token", "")
                info  = fetch_google_userinfo(token)
                db    = get_session()
                user  = find_or_create_oauth_user("google", info, db)
                login_user(user)
                db.close()
                st.switch_page("pages/1_Scorecard.py")
            except Exception as e:
                st.error(f"Google sign-in failed: {e}")

    if fb_result and "token" in fb_result:
        with st.spinner("Signing in with Facebook..."):
            try:
                token = fb_result["token"].get("access_token", "")
                info  = fetch_facebook_userinfo(token)
                db    = get_session()
                user  = find_or_create_oauth_user("facebook", info, db)
                login_user(user)
                db.close()
                st.switch_page("pages/1_Scorecard.py")
            except Exception as e:
                st.error(f"Facebook sign-in failed: {e}")

    if k_result and "token" in k_result:
        with st.spinner("Signing in with KakaoTalk..."):
            try:
                token = k_result["token"].get("access_token", "")
                info  = fetch_kakao_userinfo(token)
                db    = get_session()
                user  = find_or_create_oauth_user("kakao", info, db)
                login_user(user)
                db.close()
                st.switch_page("pages/1_Scorecard.py")
            except Exception as e:
                st.error(f"KakaoTalk sign-in failed: {e}")

    st.markdown(
        "<div class='divider-text'>or continue with email</div>",
        unsafe_allow_html=True,
    )

# ── Email / Password tabs ─────────────────────────────────────────────────────
tab_in, tab_up = st.tabs(["Log In", "Create Account"])

with tab_in:
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        pw    = st.text_input("Password", type="password", placeholder="••••••••")
        ok    = st.form_submit_button("Log In", use_container_width=True, type="primary")

    if ok:
        if not email.strip() or not pw:
            st.error("Email and password required.")
        else:
            db   = get_session()
            user = db.query(User).filter_by(email=email.strip().lower()).first()
            db.close()
            if user is None:
                st.error("No account found with that email.")
            elif not user.password_hash:
                st.error("This account uses social login — use Google, Facebook, or KakaoTalk above.")
            elif not verify_password(pw, user.password_hash):
                st.error("Incorrect password.")
            else:
                login_user(user)
                st.switch_page("pages/1_Scorecard.py")

with tab_up:
    with st.form("signup_form", clear_on_submit=False):
        su_name  = st.text_input("Your name",        placeholder="Tiger Woods")
        su_email = st.text_input("Email",             placeholder="you@example.com")
        su_pw    = st.text_input("Password",          type="password", placeholder="Min 8 chars")
        su_pw2   = st.text_input("Confirm password",  type="password", placeholder="Repeat password")
        su_ok    = st.form_submit_button("Create Account", use_container_width=True, type="primary")

    if su_ok:
        errs = []
        if not su_name.strip():           errs.append("Name is required.")
        if not su_email.strip():          errs.append("Email is required.")
        if len(su_pw) < 8:                errs.append("Password must be at least 8 characters.")
        if su_pw != su_pw2:               errs.append("Passwords do not match.")

        if errs:
            for e in errs:
                st.error(e)
        else:
            db  = get_session()
            dup = db.query(User).filter_by(email=su_email.strip().lower()).first()
            if dup:
                st.error("An account with that email already exists.")
                db.close()
            else:
                new_user = User(
                    name=su_name.strip(),
                    email=su_email.strip().lower(),
                    password_hash=hash_password(su_pw),
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                login_user(new_user)
                db.close()
                st.success(f"Welcome, {new_user.name}! Account created.")
                st.switch_page("pages/1_Scorecard.py")

st.markdown("</div>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<p style='text-align:center;color:#2d5a2d;font-size:0.75rem;margin-top:1.5rem'>"
    "Tee time booking doesn't require an account.</p>",
    unsafe_allow_html=True,
)
