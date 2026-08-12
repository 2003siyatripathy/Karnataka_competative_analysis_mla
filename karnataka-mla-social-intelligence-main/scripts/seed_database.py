from pathlib import Path
import csv
from datetime import datetime
from backend.db import Base, engine, SessionLocal
from backend.models import MLA, SocialPost, EngagementSnapshot
from ml.analytics import classify_topic, simple_sentiment, engagement_rate

Base.metadata.create_all(bind=engine)

ROOT = Path(__file__).resolve().parents[1]
MLA_CSV = ROOT / "data" / "mla_profiles.csv"
DEMO_CSV = ROOT / "data" / "generated" / "demo_posts.csv"

db = SessionLocal()

try:
    # Seed MLAs
    with MLA_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["name"].strip()
            existing = db.query(MLA).filter(MLA.name == name).first()
            if existing:
                continue
            db.add(MLA(
                name=name,
                constituency=row["constituency"].strip(),
                party=row["party"].strip(),
                state=row["state"].strip(),
                x_username=(row.get("x_username") or "").strip() or None,
                x_user_id=(row.get("x_user_id") or "").strip() or None,
                youtube_channel_id=(row.get("youtube_channel_id") or "").strip() or None,
                official_account_verified=(row.get("official_account_verified") or "NO").strip(),
            ))
    db.commit()

    # Seed synthetic posts
    if DEMO_CSV.exists():
        mla_map = {m.name: m for m in db.query(MLA).all()}
        count = 0
        with DEMO_CSV.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if db.query(SocialPost).filter(
                    SocialPost.platform == row["platform"],
                    SocialPost.platform_post_id == row["platform_post_id"]
                ).first():
                    continue

                likes = int(row["likes"])
                comments = int(row["comments"])
                shares = int(row["shares"])
                views = int(row["views"])
                text = row["post_text"]

                sentiment, sentiment_score = simple_sentiment(text)
                topic = classify_topic(text)

                post = SocialPost(
                    mla_id=mla_map[row["mla_name"]].id,
                    platform=row["platform"],
                    platform_post_id=row["platform_post_id"],
                    post_text=text,
                    post_url=row["post_url"],
                    posted_at=datetime.fromisoformat(row["posted_at"]),
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    views=views,
                    language=row["language"],
                    sentiment=sentiment,
                    sentiment_score=sentiment_score,
                    topic=topic,
                    engagement_rate=engagement_rate(likes, comments, shares, views),
                    data_source=row["data_source"],
                )
                db.add(post)
                db.flush()

                db.add(EngagementSnapshot(
                    post_id=post.id,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    views=views,
                    engagement_rate=post.engagement_rate,
                ))
                count += 1

        db.commit()
        print(f"Seeded {count} new demo posts.")

finally:
    db.close()
