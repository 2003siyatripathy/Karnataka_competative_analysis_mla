# Interview Notes

## Why PostgreSQL?

The data is relational:
- MLA -> posts
- post -> engagement snapshots
- MLA -> alerts

PostgreSQL also supports indexes, constraints, joins, JSON if needed later, and reliable transactions.

## Why near-real-time instead of real-time?

Most social APIs are rate-limited and data is not guaranteed to arrive every second. A 5-minute polling architecture is simple, honest, and sufficient for a dashboard.

## How is engagement calculated?

```text
engagement_rate =
(likes + comments + shares) / max(views, 1) * 100
```

For platforms where views are unavailable, define a platform-specific denominator and document it.

## How does anomaly detection work?

Start with rolling mean/std or Isolation Forest on engagement rate. In production, use a baseline by MLA + platform + content type because normal engagement differs between accounts.

## How does topic detection work?

The demo uses a transparent keyword classifier. A production version can replace it with:
- sentence embeddings
- BERTopic
- zero-shot classification
- fine-tuned multilingual classifier

## How does sentiment work?

The demo has a lightweight fallback. A production deployment can load a multilingual Transformer such as XLM-R based sentiment model and evaluate it on Kannada/English/Hindi samples.

## How can GenAI be added?

Use an LLM only after deterministic analytics are computed. Pass structured metrics to the LLM and ask for:
- daily summary
- key changes
- top topics
- anomaly explanation

The LLM should not invent numbers. Every generated number should come from the database.
