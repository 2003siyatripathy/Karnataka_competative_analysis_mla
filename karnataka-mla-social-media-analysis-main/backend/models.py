from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.db import Base


class MLA(Base):
    __tablename__ = "mlas"
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False, index=True)
    constituency = Column(String(150), nullable=False)
    party = Column(String(50), nullable=False)
    state = Column(String(50), default="Karnataka")
    x_username = Column(String(100), nullable=True)
    x_user_id = Column(String(100), nullable=True)
    youtube_channel_id = Column(String(150), nullable=True)
    official_account_verified = Column(String(10), default="NO")
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("SocialPost", back_populates="mla", cascade="all, delete-orphan")


class SocialPost(Base):
    __tablename__ = "social_posts"
    id = Column(Integer, primary_key=True)
    mla_id = Column(Integer, ForeignKey("mlas.id"), nullable=False, index=True)
    platform = Column(String(30), nullable=False, index=True)
    platform_post_id = Column(String(150), nullable=False)
    post_text = Column(Text, nullable=False)
    post_url = Column(String(500), nullable=True)
    posted_at = Column(DateTime, nullable=False, index=True)

    likes = Column(BigInteger, default=0)
    comments = Column(BigInteger, default=0)
    shares = Column(BigInteger, default=0)
    views = Column(BigInteger, default=0)

    language = Column(String(20), nullable=True)
    sentiment = Column(String(20), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    topic = Column(String(100), nullable=True)
    engagement_rate = Column(Float, nullable=True)

    data_source = Column(String(30), default="demo")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    mla = relationship("MLA", back_populates="posts")
    snapshots = relationship("EngagementSnapshot", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("platform", "platform_post_id", name="uq_platform_post"),
    )


class EngagementSnapshot(Base):
    __tablename__ = "engagement_snapshots"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=False, index=True)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    likes = Column(BigInteger, default=0)
    comments = Column(BigInteger, default=0)
    shares = Column(BigInteger, default=0)
    views = Column(BigInteger, default=0)
    engagement_rate = Column(Float, default=0)

    post = relationship("SocialPost", back_populates="snapshots")


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    mla_id = Column(Integer, ForeignKey("mlas.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(String(10), default="NO")
