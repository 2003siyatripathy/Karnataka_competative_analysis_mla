import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Karnataka MLA Intelligence",
    page_icon="📊",
    layout="wide",
)

st.title("Karnataka MLA Social Media Intelligence")
st.caption("Near-real-time public social-media analytics • Demo data is clearly labeled")

try:
    summary = requests.get(f"{API}/api/summary", timeout=5).json()
    mlas = requests.get(f"{API}/api/mlas", timeout=5).json()
    posts = requests.get(f"{API}/api/posts?limit=500", timeout=5).json()
    sentiment = requests.get(f"{API}/api/sentiment", timeout=5).json()
    issues = requests.get(f"{API}/api/issues", timeout=5).json()
    alerts = requests.get(f"{API}/api/alerts", timeout=5).json()
except Exception as e:
    st.error(f"Could not connect to FastAPI at {API}. Start the API first. Error: {e}")
    st.stop()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("MLAs", summary["mlas"])
c2.metric("Posts", f'{summary["posts"]:,}')
c3.metric("Views", f'{summary["views"]:,}')
c4.metric("Avg engagement", f'{summary["avg_engagement_rate"]:.2f}%')
c5.metric("Open alerts", summary["open_alerts"])

st.divider()

df = pd.DataFrame(posts)
mla_df = pd.DataFrame(mlas)

if not df.empty:
    left, right = st.columns(2)

    with left:
        st.subheader("Sentiment")
        s_df = pd.DataFrame(sentiment)
        fig = px.pie(s_df, names="sentiment", values="count", hole=0.45)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Issue Radar")
        i_df = pd.DataFrame(issues).sort_values("mentions", ascending=True)
        fig = px.bar(i_df, x="mentions", y="topic", orientation="h")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("MLA Pulse Score")
    if not mla_df.empty:
        st.dataframe(
            mla_df.sort_values("pulse_score", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Engagement by MLA")
    agg = df.groupby("mla", as_index=False).agg(
        posts=("id", "count"),
        views=("views", "sum"),
        avg_engagement=("engagement_rate", "mean"),
    )
    fig = px.bar(
        agg.sort_values("avg_engagement", ascending=False),
        x="mla",
        y="avg_engagement",
        hover_data=["posts", "views"],
        labels={"avg_engagement": "Average engagement rate (%)"},
    )
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Live Social Feed")
    st.dataframe(
        df[[
            "mla", "platform", "text", "posted_at", "likes",
            "comments", "shares", "views", "engagement_rate",
            "sentiment", "topic", "data_source"
        ]].head(100),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Alerts")
if alerts:
    st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
else:
    st.info("No alerts yet.")

st.caption(f"API: {API}")
