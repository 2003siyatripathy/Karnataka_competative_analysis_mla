"""
Optional multilingual sentiment model.

The project works without downloading a model by using the lightweight fallback in
ml.analytics.simple_sentiment(). To enable a Transformer model, install:
    pip install transformers torch
and set SENTIMENT_MODEL in .env.
"""

from backend.config import settings
from ml.analytics import simple_sentiment

_pipeline = None


def analyze(text: str):
    global _pipeline
    if not text:
        return "Neutral", 0.0

    try:
        if _pipeline is None:
            from transformers import pipeline
            _pipeline = pipeline("sentiment-analysis", model=settings.sentiment_model)
        result = _pipeline(text[:512])[0]
        label = result["label"].lower()
        score = float(result["score"])
        if "positive" in label or label == "label_2":
            return "Positive", score
        if "negative" in label or label == "label_0":
            return "Negative", -score
        return "Neutral", 0.0
    except Exception:
        return simple_sentiment(text)
