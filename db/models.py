from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, func
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)   # for email/password auth
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    players = relationship("Player", back_populates="user")
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")


class OAuthAccount(Base):
    """Links a User to a Google or Facebook identity."""
    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)           # "google" | "facebook"
    provider_user_id = Column(String, nullable=False)   # sub / fb user id
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="oauth_accounts")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="players")
    round_players = relationship("RoundPlayer", back_populates="player")
    scores = relationship("Score", back_populates="player")
    name_mappings = relationship("NameMapping", back_populates="player")
    handicap_history = relationship("HandicapHistory", back_populates="player")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slope_rating = Column(Float, default=113.0)
    course_rating = Column(Float, default=72.0)
    par = Column(Integer, default=72)

    rounds = relationship("Round", back_populates="course")


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    date = Column(Date, nullable=False)
    created_by = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    course = relationship("Course", back_populates="rounds")
    round_players = relationship("RoundPlayer", back_populates="round", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="round", cascade="all, delete-orphan")


class RoundPlayer(Base):
    __tablename__ = "round_players"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    handicap_at_time = Column(Float, nullable=True)
    total_score = Column(Integer, nullable=True)

    round = relationship("Round", back_populates="round_players")
    player = relationship("Player", back_populates="round_players")


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    hole_number = Column(Integer, nullable=False)
    strokes = Column(Integer, nullable=False)

    round = relationship("Round", back_populates="scores")
    player = relationship("Player", back_populates="scores")


class NameMapping(Base):
    __tablename__ = "name_mappings"

    id = Column(Integer, primary_key=True)
    raw_name = Column(String, nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    confidence_score = Column(Float, default=1.0)
    last_used = Column(DateTime, default=func.now())

    player = relationship("Player", back_populates="name_mappings")


class HandicapHistory(Base):
    __tablename__ = "handicap_history"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    handicap_index = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=func.now())
    rounds_used = Column(Integer, default=0)

    player = relationship("Player", back_populates="handicap_history")
