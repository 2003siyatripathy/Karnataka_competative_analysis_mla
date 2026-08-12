from pathlib import Path
from datetime import datetime, timedelta
import csv
import random

random.seed(42)

MLAS = [
    ("Siddaramaiah", "Varuna", "INC"),
    ("D. K. Shivakumar", "Kanakapura", "INC"),
    ("Priyank Kharge", "Chittapur", "INC"),
    ("G. Parameshwara", "Koratagere", "INC"),
    ("M. B. Patil", "Babaleshwar", "INC"),
    ("R. Ashoka", "Padmanabhanagar", "BJP"),
    ("B. Y. Vijayendra", "Shikaripura", "BJP"),
    ("Basanagouda Patil Yatnal", "Vijayapura City", "BJP"),
    ("U. T. Khader", "Mangalore", "INC"),
    ("V. Sunil Kumar", "Karkal", "BJP"),
]

TOPICS = {
    "Infrastructure": [
        "road development", "metro work", "traffic improvement", "bridge project"
    ],
    "Water": ["drinking water", "lake restoration", "water supply", "reservoir"],
    "Education": ["school upgrade", "student support", "college development", "education"],
    "Healthcare": ["hospital services", "health camp", "medical support", "healthcare"],
    "Jobs": ["employment", "skill development", "startup ecosystem", "new jobs"],
    "Agriculture": ["farmer support", "irrigation", "crop support", "agriculture"],
    "Public Safety": ["road safety", "police coordination", "public safety", "emergency response"],
    "Environment": ["waste management", "garbage clearance", "green initiative", "pollution"],
    "Technology": ["digital services", "technology", "innovation", "AI initiative"],
    "Governance": ["citizen services", "government scheme", "public meeting", "development review"],
}

POS = [
    "Good progress on", "Successful review of", "We are happy to announce",
    "Important development on", "Work has improved for", "Thank you to citizens for supporting"
]
NEG = [
    "Concern raised about", "Review needed for", "Residents reported a problem with",
    "Urgent attention needed for", "Delay reported in"
]

out = Path(__file__).resolve().parents[1] / "data" / "generated"
out.mkdir(parents=True, exist_ok=True)

posts_path = out / "demo_posts.csv"

now = datetime.utcnow()
rows = []
counter = 1

for mla_idx, (name, constituency, party) in enumerate(MLAS, start=1):
    for i in range(100):
        topic = random.choice(list(TOPICS))
        issue = random.choice(TOPICS[topic])
        sentiment_type = random.choices(["positive", "neutral", "negative"], weights=[0.5, 0.32, 0.18])[0]

        if sentiment_type == "positive":
            prefix = random.choice(POS)
        elif sentiment_type == "negative":
            prefix = random.choice(NEG)
        else:
            prefix = "Update regarding"

        text = f"{prefix} {issue} in {constituency}. Public discussion and follow-up continue."
        posted_at = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))

        views = random.randint(5000, 250000)
        likes = int(views * random.uniform(0.01, 0.08))
        comments = int(likes * random.uniform(0.05, 0.35))
        shares = int(likes * random.uniform(0.03, 0.25))

        rows.append({
            "mla_name": name,
            "constituency": constituency,
            "party": party,
            "platform": random.choice(["X", "YouTube"]),
            "platform_post_id": f"DEMO-{counter:06d}",
            "post_text": text,
            "post_url": "",
            "posted_at": posted_at.isoformat(),
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "views": views,
            "language": "en",
            "data_source": "demo",
        })
        counter += 1

with posts_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} synthetic posts at {posts_path}")
