from datetime import datetime
from pydantic import BaseModel


class MLASummary(BaseModel):
    id: int
    name: str
    constituency: str
    party: str
    pulse_score: float


class PostOut(BaseModel):
    id: int
    mla: str
    platform: str
    text: str
    posted_at: datetime
    likes: int
    comments: int
    shares: int
    views: int
    engagement_rate: float
    sentiment: str
    topic: str
    data_source: str
