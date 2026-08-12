import pandas as pd
from ml.analytics import classify_topic, simple_sentiment, engagement_rate, pulse_score


def test_topic():
    assert classify_topic("New metro and road development") == "Infrastructure"


def test_sentiment():
    assert simple_sentiment("Great progress and successful development")[0] == "Positive"


def test_engagement_rate():
    assert engagement_rate(100, 20, 10, 10000) == 1.3


def test_pulse():
    df = pd.DataFrame([{
        "engagement_rate": 4.0,
        "views": 100000,
        "sentiment": "Positive",
        "topic": "Infrastructure",
    }] * 10)
    assert pulse_score(df) > 0
