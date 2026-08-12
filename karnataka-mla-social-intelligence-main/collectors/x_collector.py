"""
X API collector.

Required:
  X_BEARER_TOKEN
  x_username or x_user_id in data/mla_profiles.csv

This collector intentionally does not scrape X web pages. It uses API endpoints.
"""

from pathlib import Path
import csv
import requests
from datetime import datetime

from backend.config import settings
from backend.db import SessionLocal, Base, engine
from backend.models import MLA, SocialPost, EngagementSnapshot
from ml.analytics import classify_topic, engagement_rate
from ml.sentiment import analyze

BASE_URL = "https://api.x.com/2"

Base.metadata.create_all(bind=engine)


def headers():
    return {"Authorization": f"Bearer {settings.x_bearer_token}"}


def get_user_id(username):
    url = f"{BASE_URL}/users/by/username/{username}"
    r = requests.get(url, headers=headers(), timeout=30)
    r.raise_for_status()
    return r.json()["data"]["id"]


def get_posts(user_id, max_results=100):
    url = f"{BASE_URL}/users/{user_id}/tweets"
    params = {
        "max_results": max(5, min(max_results, 100)),
        "tweet.fields": "created_at,lang,public_metrics",
    }
    r = requests.get(url, headers=headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("data", [])


def collect():
    if not settings.x_bearer_token:
        raise RuntimeError("X_BEARER_TOKEN is not configured.")

    db = SessionLocal()
    try:
        for mla in db.query(MLA).all():
            username = (mla.x_username or "").strip()
            if not username:
                continue

            try:
                user_id = mla.x_user_id or get_user_id(username)
                mla.x_user_id = user_id
                tweets = get_posts(user_id)

                for tweet in tweets:
                    tweet_id = tweet["id"]
                    if db.query(SocialPost).filter(
                        SocialPost.platform == "X",
                        SocialPost.platform_post_id == tweet_id
                    ).first():
                        continue

                    metrics = tweet.get("public_metrics", {})
                    likes = metrics.get("like_count", 0)
                    replies = metrics.get("reply_count", 0)
                    reposts = metrics.get("retweet_count", 0)
                    views = metrics.get("impression_count", 0)

                    text = tweet.get("text", "")
                    sentiment, sentiment_score = analyze(text)

                    post = SocialPost(
                        mla_id=mla.id,
                        platform="X",
                        platform_post_id=tweet_id,
                        post_text=text,
                        post_url=f"https://x.com/{username}/status/{tweet_id}",
                        posted_at=datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00")).replace(tzinfo=None),
                        likes=likes,
                        comments=replies,
                        shares=reposts,
                        views=views,
                        language=tweet.get("lang"),
                        sentiment=sentiment,
                        sentiment_score=sentiment_score,
                        topic=classify_topic(text),
                        engagement_rate=engagement_rate(likes, replies, reposts, views),
                        data_source="x_api",
                    )
                    db.add(post)
                    db.flush()
                    db.add(EngagementSnapshot(
                        post_id=post.id,
                        likes=likes,
                        comments=replies,
                        shares=reposts,
                        views=views,
                        engagement_rate=post.engagement_rate,
                    ))
                db.commit()
                print(f"Collected X posts for {mla.name}")
            except Exception as exc:
                db.rollback()
                print(f"X collection failed for {mla.name}: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    collect()
