from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd

from backend.db import Base, engine, get_db
from backend.models import MLA, SocialPost, Alert
from ml.analytics import pulse_score, detect_anomalies

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Karnataka MLA Social Intelligence API",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow()}


@app.get("/api/mlas")
def get_mlas(db: Session = Depends(get_db)):
    mlas = db.query(MLA).order_by(MLA.name).all()
    result = []
    for mla in mlas:
        posts = db.query(SocialPost).filter(SocialPost.mla_id == mla.id).all()
        df = pd.DataFrame([{
            "engagement_rate": p.engagement_rate or 0,
            "views": p.views or 0,
            "sentiment": p.sentiment or "Neutral",
            "topic": p.topic or "Other"
        } for p in posts])
        result.append({
            "id": mla.id,
            "name": mla.name,
            "constituency": mla.constituency,
            "party": mla.party,
            "pulse_score": pulse_score(df)
        })
    return result


@app.get("/api/summary")
def summary(db: Session = Depends(get_db)):
    total_mlas = db.query(MLA).count()
    total_posts = db.query(SocialPost).count()
    total_views = db.query(func.coalesce(func.sum(SocialPost.views), 0)).scalar() or 0
    total_engagement = db.query(
        func.coalesce(
            func.sum(SocialPost.likes + SocialPost.comments + SocialPost.shares), 0
        )
    ).scalar() or 0

    avg_er = db.query(func.coalesce(func.avg(SocialPost.engagement_rate), 0)).scalar() or 0
    alerts = db.query(Alert).filter(Alert.resolved == "NO").count()

    return {
        "mlas": total_mlas,
        "posts": total_posts,
        "views": int(total_views),
        "engagement": int(total_engagement),
        "avg_engagement_rate": round(float(avg_er), 2),
        "open_alerts": alerts,
        "updated_at": datetime.utcnow(),
    }


@app.get("/api/posts")
def get_posts(
    limit: int = Query(100, ge=1, le=1000),
    mla_id: int | None = None,
    platform: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(SocialPost, MLA.name).join(MLA, SocialPost.mla_id == MLA.id)
    if mla_id:
        q = q.filter(SocialPost.mla_id == mla_id)
    if platform:
        q = q.filter(SocialPost.platform == platform)
    rows = q.order_by(SocialPost.posted_at.desc()).limit(limit).all()

    return [{
        "id": p.id,
        "mla": name,
        "platform": p.platform,
        "text": p.post_text,
        "posted_at": p.posted_at,
        "likes": int(p.likes or 0),
        "comments": int(p.comments or 0),
        "shares": int(p.shares or 0),
        "views": int(p.views or 0),
        "engagement_rate": float(p.engagement_rate or 0),
        "sentiment": p.sentiment or "Neutral",
        "topic": p.topic or "Other",
        "data_source": p.data_source or "unknown",
    } for p, name in rows]


@app.get("/api/sentiment")
def sentiment(db: Session = Depends(get_db)):
    rows = db.query(SocialPost.sentiment, func.count(SocialPost.id)).group_by(SocialPost.sentiment).all()
    return [{"sentiment": s or "Unknown", "count": int(c)} for s, c in rows]


@app.get("/api/issues")
def issues(db: Session = Depends(get_db)):
    rows = db.query(SocialPost.topic, func.count(SocialPost.id)).group_by(SocialPost.topic).all()
    return [{"topic": t or "Other", "mentions": int(c)} for t, c in rows]


@app.get("/api/alerts")
def get_alerts(db: Session = Depends(get_db)):
    rows = db.query(Alert, MLA.name).join(MLA, Alert.mla_id == MLA.id).order_by(Alert.created_at.desc()).limit(50).all()
    return [{
        "id": a.id,
        "mla": name,
        "type": a.alert_type,
        "severity": a.severity,
        "message": a.message,
        "created_at": a.created_at,
        "resolved": a.resolved,
    } for a, name in rows]
