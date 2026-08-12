# Karnataka MLA Social Media analysis Dashboard

A portfolio-ready AI/ML project that tracks public social-media activity for 10 Karnataka MLAs and turns posts into analytics, sentiment, topics, engagement trends, anomaly alerts, and an AI-style daily brief.

> **Important:** `data/mla_profiles.csv` contains the MLA/constituency seed list. The generated demo posts are **synthetic** and are clearly labeled as demo data. They must not be presented as real statements or real political engagement. Real data is collected only through configured official/API-accessible sources.

## What this project demonstrates

- Python + FastAPI backend
- PostgreSQL database
- Streamlit dashboard
- X API collector
- YouTube Data API collector
- Near-real-time polling worker (5 minutes)
- Sentiment analysis pipeline with optional multilingual Transformer
- Topic classification
- Engagement-rate calculation
- Rolling anomaly detection / z-score
- MLA comparison
- Issue radar
- AI-style daily brief
- Docker Compose
- Clean GitHub repository structure

## Architecture

```text
                    +-------------------+
                    | X API / YouTube   |
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | Collectors         |
                    | x_collector.py    |
                    | youtube_collector |
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | PostgreSQL        |
                    | MLAs / Posts      |
                    | Snapshots         |
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | Analytics / ML    |
                    | Sentiment         |
                    | Topics            |
                    | Anomalies         |
                    +---------+---------+
                              |
                     +--------+--------+
                     |                 |
                     v                 v
              +-------------+   +-------------+
              | FastAPI     |   | Worker      |
              | REST API    |   | every 5 min |
              +------+------+   +-------------+
                     |
                     v
              +-------------+
              | Streamlit   |
              | Dashboard   |
              +-------------+
```

## 1. Prerequisites

- Python 3.11+
- Docker Desktop
- Git
- PostgreSQL (Docker is recommended)
- Optional: X API credentials
- Optional: YouTube Data API key
- Optional: Hugging Face model download for multilingual sentiment

## 2. Clone

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd karnataka-mla-social-intelligence
```

## 3. Configure environment

```bash
cp .env.example .env
```

At minimum for demo mode:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/mla_social
DEMO_MODE=true
```

For real collection, add your API credentials:

```env
X_BEARER_TOKEN=your_x_bearer_token
YOUTUBE_API_KEY=your_youtube_api_key
```

Do not commit `.env`.

## 4. Start PostgreSQL

```bash
docker compose up -d db
```

## 5. Install Python packages

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

## 6. Generate demo data

This creates synthetic posts so the dashboard works before API credentials are available.

```bash
python scripts/generate_demo_data.py
python scripts/seed_database.py
```

## 7. Start FastAPI

```bash
uvicorn backend.main:app --reload --port 8000
```

Open:

```text
http://localhost:8000/docs
```

## 8. Start Streamlit

In another terminal:

```bash
streamlit run dashboard/app.py
```

Open:

```text
http://localhost:8501
```

## 9. Run the real-data collectors

### X

First verify the official X usernames and put them in:

```text
data/mla_profiles.csv
```

Then:

```bash
python collectors/x_collector.py
```

The collector uses public API fields such as post text, created time and public metrics.

### YouTube

Put verified YouTube channel IDs in:

```text
data/mla_profiles.csv
```

Then:

```bash
python collectors/youtube_collector.py
```

### Near-real-time worker

After API credentials are configured:

```bash
python worker.py
```

It polls every 5 minutes by default.

## 10. GitHub commands

```bash
git init
git add .
git commit -m "Initial Karnataka MLA social intelligence dashboard"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/karnataka-mla-social-analysis.git
git push -u origin main
```

## Dashboard pages

1. Overview
2. MLA profiles
3. Live social feed
4. Post analytics
5. Sentiment
6. Issue radar
7. MLA comparison
8. Alerts
9. AI daily brief

## Suggested interview explanation

> I built a near-real-time social-media intelligence platform for 10 Karnataka MLAs. The system collects public social-media data through official APIs, stores it in PostgreSQL, calculates engagement metrics, performs multilingual sentiment and topic analysis, detects unusual engagement spikes, and exposes the results through FastAPI and a Streamlit dashboard. I used a five-minute polling worker for near-real-time updates and kept synthetic data clearly separated from real API data for development.

## Data-source notes

For X, configure only API-accessible public data and respect the current X developer terms and rate limits.

For YouTube, the Data API can retrieve public channel/video resources and video statistics. Store only the fields needed for the assignment.

Always verify official social accounts before adding them to the project.

## Production improvements

- Redis + Celery/RQ for distributed jobs
- Kafka for event streaming
- S3/Parquet for raw immutable data
- dbt for analytical models
- Prometheus/Grafana for monitoring
- MLflow for model tracking
- multilingual transformer fine-tuning
- vector database for semantic issue clustering
- role-based access control
- secret manager
- automated tests + GitHub Actions
