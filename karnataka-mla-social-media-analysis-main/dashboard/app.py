import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Karnataka MLA Social Media Analysis",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# DARK BLUE THEME
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL BACKGROUND
       ======================================================== */

    html,
    body,
    [data-testid="stAppViewContainer"] {
        background: #061525 !important;
        color: #ffffff !important;
    }

    .stApp {
        background: linear-gradient(
            135deg,
            #061525 0%,
            #0a1f35 50%,
            #061525 100%
        ) !important;

        color: #ffffff !important;
    }


    /* ========================================================
       REMOVE TOP WHITE SPACE
       ======================================================== */

    header[data-testid="stHeader"] {
        display: none !important;
    }

    [data-testid="stDecoration"] {
        display: none !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1500px;
    }


    /* ========================================================
       TITLE
       ======================================================== */

    h1 {
        color: #ffffff !important;
        font-size: 38px !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
        margin-bottom: 5px !important;
    }

    h2,
    h3 {
        color: #ffffff !important;
        font-weight: 750 !important;
    }

    .stCaption {
        color: #9bb6d1 !important;
    }


    /* ========================================================
       METRIC CARDS
       ======================================================== */

    [data-testid="stMetric"] {
        background: linear-gradient(
            145deg,
            #102d49,
            #0b2138
        );

        border: 1px solid #1d5f91;
        border-radius: 14px;

        padding: 20px;

        min-height: 125px;

        box-shadow:
            0 8px 25px rgba(0, 0, 0, 0.30),
            inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }

    [data-testid="stMetric"]:hover {
        border-color: #168cff;

        box-shadow:
            0 0 20px rgba(22, 140, 255, 0.20);
    }

    [data-testid="stMetricLabel"] {
        color: #91aec7 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 30px !important;
        font-weight: 800 !important;
    }

    [data-testid="stMetricDelta"] {
        color: #35e0a1 !important;
    }


    /* ========================================================
       SECTION HEADINGS
       ======================================================== */

    .stSubheader {
        color: #ffffff !important;
        font-weight: 750 !important;
    }


    /* ========================================================
       DIVIDER
       ======================================================== */

    hr {
        border-color: #1b496f !important;
        margin-top: 25px !important;
        margin-bottom: 25px !important;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #061525 0%,
            #0a2742 100%
        ) !important;

        border-right: 1px solid #164d78;
    }

    section[data-testid="stSidebar"] * {
        color: #eaf5ff !important;
    }


    /* ========================================================
       DATAFRAMES
       ======================================================== */

    div[data-testid="stDataFrame"] {
        background-color: #102d49 !important;

        border-radius: 12px;

        border: 1px solid #2a6696;

        overflow: hidden;

        box-shadow:
            0 8px 25px rgba(0, 0, 0, 0.25);
    }


    /* ========================================================
       ALERT / INFO BOX
       ======================================================== */

    div[data-testid="stAlert"] {
        background-color: #102d49 !important;

        color: #ffffff !important;

        border: 1px solid #1d5f91;

        border-radius: 10px;
    }


    /* ========================================================
       SELECT BOX
       ======================================================== */

    div[data-baseweb="select"] > div {
        background-color: #102d49 !important;

        border: 1px solid #28628f !important;

        color: #ffffff !important;

        border-radius: 8px;
    }

    div[data-baseweb="select"] span {
        color: #ffffff !important;
    }


    /* ========================================================
       SCROLLBAR
       ======================================================== */

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #061525;
    }

    ::-webkit-scrollbar-thumb {
        background: #155f91;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #168cff;
    }


    /* ========================================================
       FOOTER
       ======================================================== */

    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API
# ============================================================

API = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000"
)


# ============================================================
# HEADER
# ============================================================

st.title("Karnataka MLA Social Media Analysis")

st.caption(
    "Near-real-time public social-media analytics • "
    "Demo data is clearly labeled"
)


# ============================================================
# GET DATA FROM FASTAPI
# ============================================================

try:

    summary = requests.get(
        f"{API}/api/summary",
        timeout=5
    ).json()

    mlas = requests.get(
        f"{API}/api/mlas",
        timeout=5
    ).json()

    posts = requests.get(
        f"{API}/api/posts?limit=500",
        timeout=5
    ).json()

    sentiment = requests.get(
        f"{API}/api/sentiment",
        timeout=5
    ).json()

    issues = requests.get(
        f"{API}/api/issues",
        timeout=5
    ).json()

    alerts = requests.get(
        f"{API}/api/alerts",
        timeout=5
    ).json()

except Exception as e:

    st.error(
        f"Could not connect to FastAPI at {API}. "
        f"Start the API first. Error: {e}"
    )

    st.stop()


# ============================================================
# TOP METRICS
# ============================================================

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "MLAs",
    summary["mlas"]
)

c2.metric(
    "Posts",
    f'{summary["posts"]:,}'
)

c3.metric(
    "Views",
    f'{summary["views"]:,}'
)

c4.metric(
    "Avg Engagement",
    f'{summary["avg_engagement_rate"]:.2f}%'
)

c5.metric(
    "Open Alerts",
    summary["open_alerts"]
)


st.divider()


# ============================================================
# DATAFRAMES
# ============================================================

df = pd.DataFrame(posts)

mla_df = pd.DataFrame(mlas)


# ============================================================
# SENTIMENT + ISSUE RADAR
# ============================================================

if not df.empty:

    left, right = st.columns(2)

    # --------------------------------------------------------
    # SENTIMENT
    # --------------------------------------------------------

    with left:

        st.subheader("Sentiment")

        s_df = pd.DataFrame(sentiment)

        fig = px.pie(
            s_df,
            names="sentiment",
            values="count",
            hole=0.45,
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            legend=dict(
                font=dict(color="white")
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # --------------------------------------------------------
    # ISSUE RADAR
    # --------------------------------------------------------

    with right:

        st.subheader("Issue Radar")

        i_df = pd.DataFrame(issues).sort_values(
            "mentions",
            ascending=True
        )

        fig = px.bar(
            i_df,
            x="mentions",
            y="topic",
            orientation="h",
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            xaxis=dict(
                color="#9bb6d1",
                gridcolor="#1b496f"
            ),
            yaxis=dict(
                color="#ffffff"
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# MLA PULSE SCORE
# ============================================================

st.subheader("MLA Pulse Score")

if not mla_df.empty:

    st.dataframe(
        mla_df.sort_values(
            "pulse_score",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# ENGAGEMENT BY MLA
# ============================================================

if not df.empty:

    st.subheader("Engagement by MLA")

    agg = df.groupby(
        "mla",
        as_index=False
    ).agg(
        posts=("id", "count"),
        views=("views", "sum"),
        avg_engagement=("engagement_rate", "mean"),
    )

    fig = px.bar(
        agg.sort_values(
            "avg_engagement",
            ascending=False
        ),
        x="mla",
        y="avg_engagement",
        hover_data=[
            "posts",
            "views"
        ],
        labels={
            "avg_engagement":
            "Average engagement rate (%)"
        },
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(
            color="#ffffff",
            gridcolor="#1b496f"
        ),
        yaxis=dict(
            color="#ffffff",
            gridcolor="#1b496f"
        ),
        xaxis_tickangle=-35,
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# LIVE SOCIAL FEED
# ============================================================

st.subheader("Live Social Feed")

if not df.empty:

    st.dataframe(
        df[
            [
                "mla",
                "platform",
                "text",
                "posted_at",
                "likes",
                "comments",
                "shares",
                "views",
                "engagement_rate",
                "sentiment",
                "topic",
                "data_source",
            ]
        ].head(100),

        use_container_width=True,

        hide_index=True,
    )


# ============================================================
# ALERTS
# ============================================================

st.subheader("Alerts")

if alerts:

    st.dataframe(
        pd.DataFrame(alerts),

        use_container_width=True,

        hide_index=True,
    )

else:

    st.info("No alerts yet.")


# ============================================================
# API FOOTER
# ============================================================

st.caption(f"API: {API}")

