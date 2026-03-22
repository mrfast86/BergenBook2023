"""
OAuth2 helpers for Google, Facebook, and KakaoTalk.

After streamlit-oauth returns a token dict, call the relevant fetch_*_userinfo()
to get a normalized {sub, email, name, avatar} dict.

Then call find_or_create_oauth_user() to get/create a User row and link it.
"""
import os
import requests
from sqlalchemy.orm import Session
from db.models import User, OAuthAccount

# ── Provider endpoints (used by streamlit-oauth OAuth2Component) ─────────────

def _secret(key: str, default: str = "") -> str:
    """Read from env var first, fall back to st.secrets."""
    val = os.environ.get(key, "")
    if not val:
        try:
            import streamlit as st
            val = st.secrets.get(key, default)
        except Exception:
            val = default
    return val


GOOGLE = {
    "authorize_url":     "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url":         "https://oauth2.googleapis.com/token",
    "revoke_url":        "https://oauth2.googleapis.com/revoke",
    "scope":             "openid email profile",
    "client_id":         _secret("GOOGLE_CLIENT_ID"),
    "client_secret":     _secret("GOOGLE_CLIENT_SECRET"),
}

FACEBOOK = {
    "authorize_url":     "https://www.facebook.com/v20.0/dialog/oauth",
    "token_url":         "https://graph.facebook.com/v20.0/oauth/access_token",
    "revoke_url":        None,
    "scope":             "email,public_profile",
    "client_id":         _secret("FACEBOOK_CLIENT_ID"),
    "client_secret":     _secret("FACEBOOK_CLIENT_SECRET"),
}

KAKAO = {
    "authorize_url":     "https://kauth.kakao.com/oauth/authorize",
    "token_url":         "https://kauth.kakao.com/oauth/token",
    "revoke_url":        None,
    "scope":             "profile_nickname profile_image account_email",
    "client_id":         _secret("KAKAO_CLIENT_ID"),
    "client_secret":     _secret("KAKAO_CLIENT_SECRET"),
}

REDIRECT_URI = _secret("REDIRECT_URI", "http://localhost:8502")


# ── Userinfo fetchers ────────────────────────────────────────────────────────

def fetch_google_userinfo(access_token: str) -> dict:
    """
    Exchange an access token for Google user info.
    Returns: {sub, email, name, avatar}
    """
    resp = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "sub":    data.get("sub", ""),
        "email":  data.get("email", ""),
        "name":   data.get("name", data.get("email", "User")),
        "avatar": data.get("picture", ""),
    }


def fetch_facebook_userinfo(access_token: str) -> dict:
    """
    Exchange an access token for Facebook user info.
    Returns: {sub, email, name, avatar}
    """
    resp = requests.get(
        "https://graph.facebook.com/me",
        params={
            "fields": "id,name,email,picture.type(large)",
            "access_token": access_token,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    avatar = ""
    try:
        avatar = data["picture"]["data"]["url"]
    except (KeyError, TypeError):
        pass
    return {
        "sub":    data.get("id", ""),
        "email":  data.get("email", ""),
        "name":   data.get("name", "User"),
        "avatar": avatar,
    }


def fetch_kakao_userinfo(access_token: str) -> dict:
    """
    Exchange an access token for KakaoTalk user info.
    Returns: {sub, email, name, avatar}
    """
    resp = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    account = data.get("kakao_account", {})
    profile = account.get("profile", {})
    return {
        "sub":    str(data.get("id", "")),
        "email":  account.get("email", ""),
        "name":   profile.get("nickname", "User"),
        "avatar": profile.get("profile_image_url", ""),
    }


# ── DB helper ────────────────────────────────────────────────────────────────

def find_or_create_oauth_user(
    provider: str,
    user_info: dict,
    db: Session,
) -> User:
    """
    Given a provider ("google" | "facebook") and normalized user_info dict,
    find or create a User + OAuthAccount row.

    Matching priority:
    1. Existing OAuthAccount with same provider + sub
    2. Existing User with same email (links the OAuth account)
    3. New User + new OAuthAccount
    """
    sub = user_info["sub"]
    email = user_info.get("email", "")
    name = user_info.get("name", email or "User")
    avatar = user_info.get("avatar", "")

    # 1. Exact provider match
    existing_oauth = (
        db.query(OAuthAccount)
        .filter_by(provider=provider, provider_user_id=sub)
        .first()
    )
    if existing_oauth:
        user = existing_oauth.user
        # Keep avatar fresh
        if avatar and not user.avatar_url:
            user.avatar_url = avatar
            db.commit()
        return user

    # 2. Email match — link new OAuth to existing user
    user = None
    if email:
        user = db.query(User).filter_by(email=email).first()

    # 3. Create user if still not found
    if user is None:
        user = User(name=name, email=email or None, avatar_url=avatar or None)
        db.add(user)
        db.flush()

    # Create OAuthAccount link
    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider=provider,
        provider_user_id=sub,
        email=email or None,
    )
    db.add(oauth_acc)
    db.commit()
    db.refresh(user)
    return user
