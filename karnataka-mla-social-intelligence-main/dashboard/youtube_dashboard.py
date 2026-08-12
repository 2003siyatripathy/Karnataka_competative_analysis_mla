import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Karnataka MLA - YouTube Intelligence",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

METRICS_FILE = DATA_DIR / "youtube_metrics.csv"
VIDEOS_FILE = DATA_DIR / "youtube_videos.csv"
COMMENTS_FILE = DATA_DIR / "youtube_comments.csv"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f7f8fa;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    .dashboard-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .dashboard-subtitle {
        color: #6b7280;
        font-size: 15px;
        margin-bottom: 20px;
    }

    .metric-card {
        background: white;
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        min-height: 120px;
    }

    .metric-label {
        color: #6b7280;
        font-size: 14px;
    }

    .metric-value {
        font-size: 27px;
        font-weight: 700;
        margin-top: 8px;
    }

    .positive {
        color: #16a34a;
    }

    .negative {
        color: #dc2626;
    }

    .neutral {
        color: #6b7280;
    }

    .section-title {
        font-size: 21px;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPERS
# ============================================================

def safe_number(df, column):

    if column not in df.columns:
        return 0

    return pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0)


def format_number(value):

    try:
        value = float(value)

        if value >= 1_00_00_000:
            return f"{value / 1_00_00_000:.2f} Cr"

        if value >= 1_00_000:
            return f"{value / 1_00_000:.2f} L"

        if value >= 1_000:
            return f"{value / 1_000:.1f}K"

        return f"{int(value):,}"

    except Exception:
        return "0"


def metric_card(label, value, css_class=""):

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {css_class}">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(ttl=60)
def load_data():

    if not METRICS_FILE.exists():
        return None, None, None

    metrics = pd.read_csv(
        METRICS_FILE
    )

    if VIDEOS_FILE.exists():

        videos = pd.read_csv(
            VIDEOS_FILE
        )

    else:

        videos = pd.DataFrame()

    if COMMENTS_FILE.exists():

        comments = pd.read_csv(
            COMMENTS_FILE
        )

    else:

        comments = pd.DataFrame()

    return metrics, videos, comments


metrics, videos, comments = load_data()


# ============================================================
# CHECK DATA
# ============================================================

if metrics is None:

    st.error(
        "youtube_metrics.csv not found."
    )

    st.code(
        "data/youtube_metrics.csv"
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "Karnataka MLA"
)

st.sidebar.caption(
    "Social Intelligence Platform"
)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "INTELLIGENCE",
    [
        "YouTube Overview",
        "Video Performance",
        "Sentiment",
        "Comments"
    ]
)

st.sidebar.markdown("---")

st.sidebar.caption(
    f"Channels: {len(metrics)}"
)

if "period_days" in metrics.columns:

    period = metrics["period_days"].iloc[0]

    st.sidebar.caption(
        f"Period: Last {period} days"
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">'
    'YouTube Intelligence'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'YouTube performance, engagement and public sentiment '
    'for Karnataka MLA channels'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# CHANNEL FILTER
# ============================================================

channel_options = ["All"]

if "name" in metrics.columns:

    channel_options += sorted(
        metrics["name"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

selected_channel = st.selectbox(
    "Select MLA / Channel",
    channel_options
)


if selected_channel != "All":

    filtered_metrics = metrics[
        metrics["name"].astype(str)
        == selected_channel
    ].copy()

else:

    filtered_metrics = metrics.copy()


# ============================================================
# PAGE 1 - YOUTUBE OVERVIEW
# ============================================================

if page == "YouTube Overview":

    st.markdown(
        '<div class="section-title">'
        'Executive Overview'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # TOTAL METRICS
    # --------------------------------------------------------

    total_channels = len(
        filtered_metrics
    )

    posts = safe_number(
        filtered_metrics,
        "posts_published"
    ).sum()

    views = safe_number(
        filtered_metrics,
        "total_views"
    ).sum()

    engagement = safe_number(
        filtered_metrics,
        "total_engagement"
    ).sum()

    comments_received = safe_number(
        filtered_metrics,
        "comments_received"
    ).sum()

    subscribers = safe_number(
        filtered_metrics,
        "youtube_subscribers"
    ).sum()

    followers_gained = safe_number(
        filtered_metrics,
        "followers_gained"
    ).sum()

    positive = safe_number(
        filtered_metrics,
        "sentiment_positive"
    ).sum()

    negative = safe_number(
        filtered_metrics,
        "sentiment_negative"
    ).sum()

    neutral = safe_number(
        filtered_metrics,
        "sentiment_neutral"
    ).sum()

    sentiment_total = (
        positive +
        negative +
        neutral
    )

    if sentiment_total > 0:

        positive_pct = (
            positive /
            sentiment_total *
            100
        )

    else:

        positive_pct = 0

    # --------------------------------------------------------
    # CARDS
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Connected YouTube Channels",
            format_number(total_channels)
        )

    with c2:
        metric_card(
            "Videos Published",
            format_number(posts)
        )

    with c3:
        metric_card(
            "Total Views",
            format_number(views)
        )

    with c4:
        metric_card(
            "Total Engagement",
            format_number(engagement)
        )

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        metric_card(
            "Subscribers",
            format_number(subscribers)
        )

    with c6:
        metric_card(
            "Subscribers Gained",
            format_number(followers_gained)
        )

    with c7:
        metric_card(
            "Comments Received",
            format_number(comments_received)
        )

    with c8:
        metric_card(
            "Positive Sentiment",
            f"{positive_pct:.1f}%",
            "positive"
        )

    st.markdown("---")

    # --------------------------------------------------------
    # CHANNEL PERFORMANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Channel Performance'
        '</div>',
        unsafe_allow_html=True
    )

    if not filtered_metrics.empty:

        chart_df = filtered_metrics.copy()

        chart_df["views"] = safe_number(
            chart_df,
            "total_views"
        )

        chart_df["engagement"] = safe_number(
            chart_df,
            "total_engagement"
        )

        fig = px.bar(
            chart_df,
            x="name",
            y="views",
            title="Views by MLA",
            labels={
                "name": "MLA",
                "views": "Views"
            }
        )

        fig.update_layout(
            height=400,
            showlegend=False
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # SENTIMENT DISTRIBUTION
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Overall Sentiment'
        '</div>',
        unsafe_allow_html=True
    )

    s1, s2 = st.columns(2)

    with s1:

        sentiment_df = pd.DataFrame({
            "Sentiment": [
                "Positive",
                "Neutral",
                "Negative"
            ],
            "Comments": [
                positive,
                neutral,
                negative
            ]
        })

        fig = px.pie(
            sentiment_df,
            names="Sentiment",
            values="Comments",
            hole=0.55
        )

        fig.update_layout(
            height=400
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with s2:

        st.subheader(
            "Sentiment Summary"
        )

        metric_card(
            "Positive",
            f"{positive:,.0f} "
            f"({positive_pct:.1f}%)",
            "positive"
        )

        negative_pct = (
            negative /
            sentiment_total *
            100
            if sentiment_total
            else 0
        )

        st.markdown("")

        metric_card(
            "Negative",
            f"{negative:,.0f} "
            f"({negative_pct:.1f}%)",
            "negative"
        )

        neutral_pct = (
            neutral /
            sentiment_total *
            100
            if sentiment_total
            else 0
        )

        st.markdown("")

        metric_card(
            "Neutral",
            f"{neutral:,.0f} "
            f"({neutral_pct:.1f}%)",
            "neutral"
        )


# ============================================================
# PAGE 2 - VIDEO PERFORMANCE
# ============================================================

elif page == "Video Performance":

    st.markdown(
        '<div class="section-title">'
        'Video Performance'
        '</div>',
        unsafe_allow_html=True
    )

    if videos.empty:

        st.warning(
            "youtube_videos.csv is empty."
        )

        st.stop()

    video_df = videos.copy()

    # --------------------------------------------------------
    # FILTER CHANNEL
    # --------------------------------------------------------

    if (
        selected_channel != "All"
        and "channel_name" in video_df.columns
    ):

        # Match by MLA name if possible
        channel_row = filtered_metrics.iloc[0]

        channel_id = channel_row.get(
            "channel_id",
            ""
        )

        if "channel_id" in video_df.columns:

            video_df = video_df[
                video_df["channel_id"].astype(str)
                == str(channel_id)
            ]

    # --------------------------------------------------------
    # NUMERIC
    # --------------------------------------------------------

    for col in [
        "views",
        "likes",
        "comments",
        "engagement",
        "engagement_rate"
    ]:

        if col in video_df.columns:

            video_df[col] = pd.to_numeric(
                video_df[col],
                errors="coerce"
            ).fillna(0)

    # --------------------------------------------------------
    # TOP VIDEOS
    # --------------------------------------------------------

    top_videos = video_df.sort_values(
        "views",
        ascending=False
    ).head(10)

    fig = px.bar(
        top_videos,
        x="views",
        y="title",
        orientation="h",
        title="Top 10 Videos by Views"
    )

    fig.update_layout(
        height=500,
        yaxis={
            "categoryorder": "total ascending"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # VIDEO TABLE
    # --------------------------------------------------------

    display_columns = [
        "title",
        "published_at",
        "views",
        "likes",
        "comments",
        "engagement",
        "engagement_rate"
    ]

    display_columns = [
        c for c in display_columns
        if c in video_df.columns
    ]

    st.dataframe(
        video_df[
            display_columns
        ].sort_values(
            "views",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# PAGE 3 - SENTIMENT
# ============================================================

elif page == "Sentiment":

    st.markdown(
        '<div class="section-title">'
        'YouTube Sentiment Intelligence'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # SENTIMENT METRICS
    # --------------------------------------------------------

    positive = safe_number(
        filtered_metrics,
        "sentiment_positive"
    ).sum()

    negative = safe_number(
        filtered_metrics,
        "sentiment_negative"
    ).sum()

    neutral = safe_number(
        filtered_metrics,
        "sentiment_neutral"
    ).sum()

    total = (
        positive +
        negative +
        neutral
    )

    if total > 0:

        positive_pct = (
            positive / total * 100
        )

        negative_pct = (
            negative / total * 100
        )

        neutral_pct = (
            neutral / total * 100
        )

    else:

        positive_pct = 0
        negative_pct = 0
        neutral_pct = 0

    scores = safe_number(
        filtered_metrics,
        "sentiment_score"
    )

    if len(scores) > 0:

        sentiment_score = scores.mean()

    else:

        sentiment_score = 0

    if sentiment_score >= 0.05:

        overall = "Positive"

    elif sentiment_score <= -0.05:

        overall = "Negative"

    else:

        overall = "Neutral"

    # --------------------------------------------------------
    # CARDS
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        metric_card(
            "Comments Analyzed",
            format_number(total)
        )

    with c2:

        metric_card(
            "Positive",
            f"{positive_pct:.1f}%",
            "positive"
        )

    with c3:

        metric_card(
            "Negative",
            f"{negative_pct:.1f}%",
            "negative"
        )

    with c4:

        css = (
            "positive"
            if overall == "Positive"
            else
            "negative"
            if overall == "Negative"
            else
            "neutral"
        )

        metric_card(
            "Overall Sentiment",
            overall,
            css
        )

    st.markdown("---")

    # --------------------------------------------------------
    # PIE + SCORE
    # --------------------------------------------------------

    left, right = st.columns(2)

    with left:

        sentiment_chart = pd.DataFrame({

            "Sentiment": [
                "Positive",
                "Neutral",
                "Negative"
            ],

            "Count": [
                positive,
                neutral,
                negative
            ]
        })

        fig = px.pie(
            sentiment_chart,
            names="Sentiment",
            values="Count",
            hole=0.6,
            title="Sentiment Distribution"
        )

        fig.update_layout(
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.subheader(
            "Sentiment Score"
        )

        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=sentiment_score,
                number={
                    "valueformat": ".3f"
                },
                gauge={
                    "axis": {
                        "range": [-1, 1]
                    }
                }
            )
        )

        gauge.update_layout(
            height=350
        )

        st.plotly_chart(
            gauge,
            use_container_width=True
        )

    # --------------------------------------------------------
    # CHANNEL SENTIMENT
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Sentiment by MLA'
        '</div>',
        unsafe_allow_html=True
    )

    sentiment_columns = [
        "name",
        "sentiment_positive_percentage",
        "sentiment_negative_percentage",
        "sentiment_neutral_percentage",
        "overall_sentiment"
    ]

    sentiment_columns = [
        c for c in sentiment_columns
        if c in filtered_metrics.columns
    ]

    if len(sentiment_columns) > 1:

        st.dataframe(
            filtered_metrics[
                sentiment_columns
            ],
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # COMMENTS
    # --------------------------------------------------------

    if not comments.empty:

        comments_df = comments.copy()

        # Filter channel
        if (
            selected_channel != "All"
            and "channel_name" in comments_df.columns
        ):

            channel_row = filtered_metrics.iloc[0]

            channel_id = channel_row.get(
                "channel_id",
                ""
            )

            if "channel_id" in comments_df.columns:

                comments_df = comments_df[
                    comments_df["channel_id"]
                    .astype(str)
                    ==
                    str(channel_id)
                ]

        # ----------------------------------------------------
        # POSITIVE COMMENTS
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">'
            'Top Positive Comments'
            '</div>',
            unsafe_allow_html=True
        )

        if "label" in comments_df.columns:

            positive_comments = (
                comments_df[
                    comments_df["label"]
                    .astype(str)
                    .str.lower()
                    == "positive"
                ]
                .sort_values(
                    "score",
                    ascending=False
                )
                .head(10)
            )

            if not positive_comments.empty:

                for _, row in positive_comments.iterrows():

                    st.success(
                        str(
                            row.get(
                                "text",
                                ""
                            )
                        )
                    )

        # ----------------------------------------------------
        # NEGATIVE COMMENTS
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">'
            'Top Negative Comments'
            '</div>',
            unsafe_allow_html=True
        )

        if "label" in comments_df.columns:

            negative_comments = (
                comments_df[
                    comments_df["label"]
                    .astype(str)
                    .str.lower()
                    == "negative"
                ]
                .sort_values(
                    "score",
                    ascending=True
                )
                .head(10)
            )

            if not negative_comments.empty:

                for _, row in negative_comments.iterrows():

                    st.error(
                        str(
                            row.get(
                                "text",
                                ""
                            )
                        )
                    )


# ============================================================
# PAGE 4 - COMMENTS
# ============================================================

elif page == "Comments":

    st.markdown(
        '<div class="section-title">'
        'YouTube Comments'
        '</div>',
        unsafe_allow_html=True
    )

    if comments.empty:

        st.warning(
            "No comments available."
        )

        st.stop()

    comments_df = comments.copy()

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search = st.text_input(
        "Search comments",
        placeholder="Search keyword..."
    )

    if search:

        comments_df = comments_df[
            comments_df["text"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    # --------------------------------------------------------
    # SENTIMENT FILTER
    # --------------------------------------------------------

    if "label" in comments_df.columns:

        sentiment_filter = st.selectbox(
            "Sentiment",
            [
                "All",
                "Positive",
                "Neutral",
                "Negative"
            ]
        )

        if sentiment_filter != "All":

            comments_df = comments_df[
                comments_df["label"]
                .astype(str)
                .str.lower()
                ==
                sentiment_filter.lower()
            ]

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    display_cols = [
        "text",
        "label",
        "score",
        "video_title",
        "author",
        "published_at",
        "like_count"
    ]

    display_cols = [
        c for c in display_cols
        if c in comments_df.columns
    ]

    st.dataframe(
        comments_df[
            display_cols
        ],
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"{len(comments_df):,} comments shown"
    )