import math
from collections import Counter
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import IsolationForest

TOPIC_KEYWORDS = {
    "Infrastructure": ["road", "metro", "bridge", "infrastructure", "traffic", "flyover"],
    "Water": ["water", "drinking water", "reservoir", "lake", "borewell"],
    "Education": ["school", "college", "education", "student", "university"],
    "Healthcare": ["hospital", "health", "clinic", "medicine", "doctor"],
    "Jobs": ["job", "employment", "skill", "industry", "startup", "career"],
    "Agriculture": ["farmer", "agriculture", "crop", "irrigation", "farming"],
    "Public Safety": ["safety", "police", "crime", "fire", "accident"],
    "Environment": ["environment", "pollution", "waste", "garbage", "green"],
    "Technology": ["technology", "digital", "ai", "innovation", "software"],
    "Governance": ["government", "scheme", "policy", "development", "citizen"],
}

POSITIVE = {
    "good", "great", "success", "progress", "happy", "support", "improved",
    "completed", "development", "proud", "welcome", "thank", "excellent"
}
NEGATIVE = {
    "bad", "failure", "problem", "delay", "poor", "angry", "protest",
    "shortage", "broken", "unsafe", "crisis", "corruption", "negative"
}


def classify_topic(text: str) -> str:
    t = (text or "").lower()
    scores = {
        topic: sum(1 for word in words if word in t)
        for topic, words in TOPIC_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"


def simple_sentiment(text: str):
    words = set((text or "").lower().replace(",", " ").replace(".", " ").split())
    pos = len(words & POSITIVE)
    neg = len(words & NEGATIVE)
    raw = pos - neg
    if raw > 0:
        return "Positive", min(1.0, 0.5 + raw * 0.1)
    if raw < 0:
        return "Negative", max(-1.0, -0.5 + raw * 0.1)
    return "Neutral", 0.0


def engagement_rate(likes, comments, shares, views):
    denominator = max(int(views or 0), 1)
    return round(((likes or 0) + (comments or 0) + (shares or 0)) / denominator * 100, 3)


def pulse_score(posts_df: pd.DataFrame) -> float:
    if posts_df.empty:
        return 0.0
    er = posts_df["engagement_rate"].fillna(0).clip(0, 20).mean() / 20 * 100
    reach = math.log1p(posts_df["views"].fillna(0).mean()) / math.log1p(10_000_000) * 100
    consistency = min(100, len(posts_df) * 2)
    positive = (posts_df["sentiment"] == "Positive").mean() * 100
    topic_momentum = min(100, posts_df["topic"].nunique() * 12.5)
    return round(0.30 * er + 0.20 * reach + 0.20 * consistency + 0.15 * positive + 0.15 * topic_momentum, 1)


def detect_anomalies(posts_df: pd.DataFrame) -> pd.DataFrame:
    if len(posts_df) < 10:
        return posts_df.assign(anomaly=False, anomaly_score=0.0)
    x = posts_df[["engagement_rate"]].fillna(0)
    model = IsolationForest(contamination=0.05, random_state=42)
    pred = model.fit_predict(x)
    score = model.decision_function(x)
    out = posts_df.copy()
    out["anomaly"] = pred == -1
    out["anomaly_score"] = score
    return out
