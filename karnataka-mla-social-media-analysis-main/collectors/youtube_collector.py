import os
import csv
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

BASE_URL = "https://www.googleapis.com/youtube/v3"

# Input/output files
ACCOUNTS_FILE = Path("data/mla_social_accounts.csv")
OUTPUT_FILE = Path("data/youtube_metrics.csv")
VIDEOS_FILE = Path("data/youtube_videos.csv")
COMMENTS_FILE = Path("data/youtube_comments.csv")
HISTORY_FILE = Path("data/youtube_history.json")

# Dashboard period
DAYS = 30

# Maximum videos per channel to inspect
MAX_VIDEOS = 50

# Maximum comments per video
MAX_COMMENTS_PER_VIDEO = 100


# ============================================================
# SENTIMENT MODEL
# ============================================================

sentiment_analyzer = SentimentIntensityAnalyzer()


# ============================================================
# VALIDATE API KEY
# ============================================================

if not YOUTUBE_API_KEY:
    raise ValueError(
        "YOUTUBE_API_KEY is missing in .env"
    )


# ============================================================
# YOUTUBE API REQUEST
# ============================================================

def youtube_get(endpoint, params):

    params = dict(params)

    params["key"] = YOUTUBE_API_KEY

    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        params=params,
        timeout=30
    )

    if response.status_code != 200:

        try:
            error_data = response.json()

        except Exception:
            error_data = response.text

        raise RuntimeError(
            f"YouTube API Error "
            f"{response.status_code}: "
            f"{error_data}"
        )

    return response.json()


# ============================================================
# GET CHANNEL
# ============================================================

def get_channel(
    channel_id=None,
    handle=None
):

    # --------------------------------------------------------
    # Search by channel ID
    # --------------------------------------------------------

    if channel_id:

        data = youtube_get(
            "channels",
            {
                "part": (
                    "snippet,"
                    "contentDetails,"
                    "statistics"
                ),
                "id": channel_id
            }
        )

    # --------------------------------------------------------
    # Search by YouTube handle
    # --------------------------------------------------------

    elif handle:

        handle = str(handle).strip()

        if not handle.startswith("@"):
            handle = "@" + handle

        data = youtube_get(
            "channels",
            {
                "part": (
                    "snippet,"
                    "contentDetails,"
                    "statistics"
                ),
                "forHandle": handle
            }
        )

    else:

        return None

    items = data.get("items", [])

    if not items:
        return None

    return items[0]


# ============================================================
# GET VIDEO IDS
# ============================================================

def get_video_ids(
    uploads_playlist_id,
    max_videos=MAX_VIDEOS
):

    video_ids = []

    page_token = None

    while len(video_ids) < max_videos:

        params = {
            "part": "contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": min(
                50,
                max_videos - len(video_ids)
            )
        }

        if page_token:
            params["pageToken"] = page_token

        data = youtube_get(
            "playlistItems",
            params
        )

        for item in data.get("items", []):

            video_id = (
                item
                .get("contentDetails", {})
                .get("videoId")
            )

            if video_id:
                video_ids.append(video_id)

        page_token = data.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return video_ids[:max_videos]


# ============================================================
# GET VIDEO DETAILS
# ============================================================

def get_video_details(video_ids):

    if not video_ids:
        return []

    videos = []

    for i in range(
        0,
        len(video_ids),
        50
    ):

        batch = video_ids[i:i + 50]

        data = youtube_get(
            "videos",
            {
                "part": (
                    "snippet,"
                    "statistics"
                ),
                "id": ",".join(batch)
            }
        )

        videos.extend(
            data.get("items", [])
        )

    return videos


# ============================================================
# CLEAN COMMENT TEXT
# ============================================================

def clean_comment(text):

    if not text:
        return ""

    # Remove HTML
    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    # Remove extra whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# GET COMMENTS FOR VIDEO
# ============================================================

def get_video_comments(
    video_id,
    max_comments=MAX_COMMENTS_PER_VIDEO
):

    comments = []

    page_token = None

    while len(comments) < max_comments:

        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(
                100,
                max_comments - len(comments)
            ),
            "order": "relevance",
            "textFormat": "plainText"
        }

        if page_token:
            params["pageToken"] = page_token

        try:

            data = youtube_get(
                "commentThreads",
                params
            )

        except Exception as e:

            error_text = str(e)

            # Comments disabled
            if (
                "commentsDisabled"
                in error_text
            ):
                return comments

            print(
                f"      Comment error: "
                f"{error_text}"
            )

            return comments

        for item in data.get(
            "items",
            []
        ):

            snippet = (
                item
                .get("snippet", {})
                .get("topLevelComment", {})
                .get("snippet", {})
            )

            text = clean_comment(
                snippet.get(
                    "textDisplay",
                    ""
                )
            )

            if text:

                comments.append({
                    "text": text,

                    "author": snippet.get(
                        "authorDisplayName",
                        ""
                    ),

                    "published_at": snippet.get(
                        "publishedAt",
                        ""
                    ),

                    "like_count": int(
                        snippet.get(
                            "likeCount",
                            0
                        )
                    )
                })

        page_token = data.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return comments[:max_comments]


# ============================================================
# ANALYZE ONE COMMENT
# ============================================================

def analyze_comment(text):

    result = sentiment_analyzer.polarity_scores(
        text
    )

    compound = result["compound"]

    if compound >= 0.05:

        label = "Positive"

    elif compound <= -0.05:

        label = "Negative"

    else:

        label = "Neutral"

    return {
        "label": label,
        "score": round(
            compound,
            4
        ),

        "positive_score": round(
            result["pos"],
            4
        ),

        "negative_score": round(
            result["neg"],
            4
        ),

        "neutral_score": round(
            result["neu"],
            4
        )
    }


# ============================================================
# ANALYZE ALL COMMENTS
# ============================================================

def analyze_sentiment(comments):

    positive = 0
    negative = 0
    neutral = 0

    scores = []

    analyzed_comments = []

    positive_comments = []
    negative_comments = []

    for comment in comments:

        text = comment["text"]

        sentiment = analyze_comment(
            text
        )

        label = sentiment["label"]

        score = sentiment["score"]

        scores.append(score)

        if label == "Positive":

            positive += 1

            positive_comments.append({
                "text": text,
                "score": score
            })

        elif label == "Negative":

            negative += 1

            negative_comments.append({
                "text": text,
                "score": score
            })

        else:

            neutral += 1

        analyzed_comments.append({
            **comment,
            **sentiment
        })

    total = len(
        analyzed_comments
    )

    # --------------------------------------------------------
    # Percentages
    # --------------------------------------------------------

    if total > 0:

        positive_percentage = round(
            positive / total * 100,
            2
        )

        negative_percentage = round(
            negative / total * 100,
            2
        )

        neutral_percentage = round(
            neutral / total * 100,
            2
        )

        average_score = round(
            sum(scores) / total,
            4
        )

    else:

        positive_percentage = 0
        negative_percentage = 0
        neutral_percentage = 0
        average_score = 0

    # --------------------------------------------------------
    # Overall sentiment
    # --------------------------------------------------------

    if average_score >= 0.05:

        overall = "Positive"

    elif average_score <= -0.05:

        overall = "Negative"

    else:

        overall = "Neutral"

    # --------------------------------------------------------
    # Strongest positive comments
    # --------------------------------------------------------

    positive_comments.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # --------------------------------------------------------
    # Strongest negative comments
    # --------------------------------------------------------

    negative_comments.sort(
        key=lambda x: x["score"]
    )

    return {

        "total_comments_analyzed":
            total,

        "positive_comments":
            positive,

        "negative_comments":
            negative,

        "neutral_comments":
            neutral,

        "positive_percentage":
            positive_percentage,

        "negative_percentage":
            negative_percentage,

        "neutral_percentage":
            neutral_percentage,

        "average_sentiment_score":
            average_score,

        "overall_sentiment":
            overall,

        "top_positive_comments":
            positive_comments[:5],

        "top_negative_comments":
            negative_comments[:5],

        "analyzed_comments":
            analyzed_comments
    }


# ============================================================
# LOAD HISTORY
# ============================================================

def load_history():

    if not HISTORY_FILE.exists():
        return {}

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


# ============================================================
# SAVE HISTORY
# ============================================================

def save_history(history):

    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            history,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# LOAD MLA ACCOUNTS
# ============================================================

def load_accounts():

    if not ACCOUNTS_FILE.exists():

        raise FileNotFoundError(
            f"File not found: "
            f"{ACCOUNTS_FILE}"
        )

    with open(
        ACCOUNTS_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        return list(
            csv.DictReader(f)
        )


# ============================================================
# CALCULATE CHANNEL METRICS
# ============================================================

def calculate_metrics(
    account,
    channel,
    videos,
    history
):

    channel_id = channel["id"]

    channel_snippet = (
        channel.get(
            "snippet",
            {}
        )
    )

    channel_stats = (
        channel.get(
            "statistics",
            {}
        )
    )

    # --------------------------------------------------------
    # Channel information
    # --------------------------------------------------------

    channel_name = (
        channel_snippet.get(
            "title",
            ""
        )
    )

    custom_url = (
        channel_snippet.get(
            "customUrl",
            ""
        )
    )

    subscribers = int(
        channel_stats.get(
            "subscriberCount",
            0
        )
    )

    lifetime_views = int(
        channel_stats.get(
            "viewCount",
            0
        )
    )

    lifetime_videos = int(
        channel_stats.get(
            "videoCount",
            0
        )
    )

    # --------------------------------------------------------
    # Date filter
    # --------------------------------------------------------

    cutoff = (
        datetime.now(
            timezone.utc
        )
        -
        timedelta(
            days=DAYS
        )
    )

    recent_videos = []

    for video in videos:

        published_at = (
            video
            .get("snippet", {})
            .get("publishedAt")
        )

        if not published_at:
            continue

        try:

            published_date = (
                datetime.fromisoformat(
                    published_at.replace(
                        "Z",
                        "+00:00"
                    )
                )
            )

        except Exception:

            continue

        if published_date >= cutoff:

            recent_videos.append(
                video
            )

    # --------------------------------------------------------
    # Video metrics
    # --------------------------------------------------------

    total_views = 0

    total_likes = 0

    total_comments = 0

    top_video = None

    top_video_views = -1

    video_rows = []

    all_comments = []

    # --------------------------------------------------------
    # Process videos
    # --------------------------------------------------------

    for video in recent_videos:

        video_id = video.get(
            "id",
            ""
        )

        snippet = video.get(
            "snippet",
            {}
        )

        stats = video.get(
            "statistics",
            {}
        )

        title = snippet.get(
            "title",
            ""
        )

        published_at = snippet.get(
            "publishedAt",
            ""
        )

        views = int(
            stats.get(
                "viewCount",
                0
            )
        )

        likes = int(
            stats.get(
                "likeCount",
                0
            )
        )

        comments_count = int(
            stats.get(
                "commentCount",
                0
            )
        )

        engagement = (
            likes +
            comments_count
        )

        total_views += views

        total_likes += likes

        total_comments += comments_count

        # ----------------------------------------------------
        # Get comments
        # ----------------------------------------------------

        comments = get_video_comments(
            video_id
        )

        for comment in comments:

            comment["video_id"] = video_id

            comment["video_title"] = title

            all_comments.append(
                comment
            )

        # ----------------------------------------------------
        # Top video
        # ----------------------------------------------------

        if views > top_video_views:

            top_video_views = views

            top_video = {
                "video_id": video_id,
                "title": title,
                "views": views,
                "likes": likes,
                "comments": comments_count,
                "published_at": published_at,
                "url": (
                    "https://www.youtube.com/"
                    f"watch?v={video_id}"
                )
            }

        # ----------------------------------------------------
        # Per-video row
        # ----------------------------------------------------

        video_rows.append({

            "channel_id":
                channel_id,

            "channel_name":
                channel_name,

            "video_id":
                video_id,

            "title":
                title,

            "published_at":
                published_at,

            "views":
                views,

            "likes":
                likes,

            "comments":
                comments_count,

            "engagement":
                engagement,

            "engagement_rate":
                round(
                    (
                        engagement /
                        views
                    ) * 100,
                    2
                )
                if views > 0
                else 0,

            "comments_analyzed":
                len(comments),

            "url":
                (
                    "https://www.youtube.com/"
                    f"watch?v={video_id}"
                )
        })

    # --------------------------------------------------------
    # Engagement
    # --------------------------------------------------------

    total_engagement = (
        total_likes +
        total_comments
    )

    if total_views > 0:

        avg_engagement_rate = round(
            (
                total_engagement /
                total_views
            ) * 100,
            2
        )

    else:

        avg_engagement_rate = 0

    # --------------------------------------------------------
    # Subscriber growth
    # --------------------------------------------------------

    previous_subscribers = (
        history
        .get(channel_id, {})
        .get("subscribers")
    )

    if previous_subscribers is not None:

        subscribers_gained = max(
            subscribers -
            int(previous_subscribers),
            0
        )

    else:

        subscribers_gained = 0

    # --------------------------------------------------------
    # SENTIMENT
    # --------------------------------------------------------

    sentiment = analyze_sentiment(
        all_comments
    )

    # --------------------------------------------------------
    # Update history
    # --------------------------------------------------------

    history[channel_id] = {

        "subscribers":
            subscribers,

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat()
    }

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {

        # ====================================================
        # MLA
        # ====================================================

        "name":
            account.get(
                "name",
                channel_name
            ),

        # ====================================================
        # CHANNEL
        # ====================================================

        "channel_id":
            channel_id,

        "channel_name":
            channel_name,

        "youtube_channel_name":
            channel_name,

        "youtube_username":
            custom_url,

        "youtube_subscribers":
            subscribers,

        "youtube_views":
            lifetime_views,

        "youtube_videos":
            lifetime_videos,

        # ====================================================
        # DASHBOARD METRICS
        # ====================================================

        "posts_published":
            len(recent_videos),

        "total_views":
            total_views,

        "total_likes":
            total_likes,

        "total_engagement":
            total_engagement,

        "avg_engagement_rate":
            avg_engagement_rate,

        "followers_gained":
            subscribers_gained,

        "comments_received":
            total_comments,

        # YouTube public API does not provide
        # share count for arbitrary public channels.
        "shares_reposts":
            None,

        # ====================================================
        # TOP VIDEO
        # ====================================================

        "top_post":
            (
                top_video["title"]
                if top_video
                else ""
            ),

        "top_post_views":
            (
                top_video["views"]
                if top_video
                else 0
            ),

        "top_post_likes":
            (
                top_video["likes"]
                if top_video
                else 0
            ),

        "top_post_comments":
            (
                top_video["comments"]
                if top_video
                else 0
            ),

        "top_post_url":
            (
                top_video["url"]
                if top_video
                else ""
            ),

        # ====================================================
        # SENTIMENT
        # ====================================================

        "sentiment_total_comments":
            sentiment[
                "total_comments_analyzed"
            ],

        "sentiment_positive":
            sentiment[
                "positive_comments"
            ],

        "sentiment_negative":
            sentiment[
                "negative_comments"
            ],

        "sentiment_neutral":
            sentiment[
                "neutral_comments"
            ],

        "sentiment_positive_percentage":
            sentiment[
                "positive_percentage"
            ],

        "sentiment_negative_percentage":
            sentiment[
                "negative_percentage"
            ],

        "sentiment_neutral_percentage":
            sentiment[
                "neutral_percentage"
            ],

        "sentiment_score":
            sentiment[
                "average_sentiment_score"
            ],

        "overall_sentiment":
            sentiment[
                "overall_sentiment"
            ],

        # ====================================================
        # SENTIMENT EXAMPLES
        # ====================================================

        "top_positive_comments":
            json.dumps(
                sentiment[
                    "top_positive_comments"
                ],
                ensure_ascii=False
            ),

        "top_negative_comments":
            json.dumps(
                sentiment[
                    "top_negative_comments"
                ],
                ensure_ascii=False
            ),

        # ====================================================
        # OTHER
        # ====================================================

        "period_days":
            DAYS,

        "last_sync":
            datetime.now(
                timezone.utc
            ).isoformat(),

        # Used internally
        "videos":
            video_rows,

        "comments":
            sentiment[
                "analyzed_comments"
            ]
    }


# ============================================================
# SAVE MAIN METRICS
# ============================================================

def save_metrics(rows):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not rows:
        return

    csv_rows = []

    for row in rows:

        clean_row = {
            key: value
            for key, value in row.items()
            if key not in [
                "videos",
                "comments"
            ]
        }

        csv_rows.append(
            clean_row
        )

    fieldnames = list(
        csv_rows[0].keys()
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            csv_rows
        )


# ============================================================
# SAVE VIDEOS
# ============================================================

def save_videos(rows):

    all_videos = []

    for row in rows:

        all_videos.extend(
            row.get(
                "videos",
                []
            )
        )

    if not all_videos:
        return

    fieldnames = list(
        all_videos[0].keys()
    )

    with open(
        VIDEOS_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            all_videos
        )


# ============================================================
# SAVE COMMENTS
# ============================================================

def save_comments(rows):

    all_comments = []

    for row in rows:

        all_comments.extend(
            row.get(
                "comments",
                []
            )
        )

    if not all_comments:
        return

    fieldnames = list(
        all_comments[0].keys()
    )

    with open(
        COMMENTS_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            all_comments
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "KARNATAKA MLA YOUTUBE "
        "COLLECTOR + SENTIMENT"
    )
    print("=" * 70)

    print(
        f"Period: Last {DAYS} days"
    )

    print(
        f"Max videos/channel: "
        f"{MAX_VIDEOS}"
    )

    print(
        f"Max comments/video: "
        f"{MAX_COMMENTS_PER_VIDEO}"
    )

    print()

    accounts = load_accounts()

    history = load_history()

    results = []

    # ========================================================
    # PROCESS EVERY MLA
    # ========================================================

    for account in accounts:

        name = (
            account.get(
                "name"
            )
            or
            account.get(
                "youtube_channel_name"
            )
            or
            "Unknown"
        )

        channel_id = (
            account.get(
                "youtube_channel_id"
            )
            or
            account.get(
                "channel_id"
            )
        )

        handle = (
            account.get(
                "youtube_username"
            )
        )

        print(
            "-" * 70
        )

        print(
            f"Searching YouTube: "
            f"{name}"
        )

        try:

            # ------------------------------------------------
            # CHANNEL
            # ------------------------------------------------

            channel = get_channel(
                channel_id=channel_id,
                handle=handle
            )

            if not channel:

                print(
                    "  Channel NOT FOUND"
                )

                continue

            actual_channel_id = (
                channel["id"]
            )

            channel_name = (
                channel
                .get(
                    "snippet",
                    {}
                )
                .get(
                    "title",
                    ""
                )
            )

            print(
                f"  Channel: "
                f"{channel_name}"
            )

            # ------------------------------------------------
            # UPLOAD PLAYLIST
            # ------------------------------------------------

            uploads_playlist = (
                channel
                .get(
                    "contentDetails",
                    {}
                )
                .get(
                    "relatedPlaylists",
                    {}
                )
                .get(
                    "uploads"
                )
            )

            if not uploads_playlist:

                print(
                    "  Upload playlist NOT FOUND"
                )

                continue

            # ------------------------------------------------
            # VIDEOS
            # ------------------------------------------------

            video_ids = get_video_ids(
                uploads_playlist
            )

            print(
                f"  Videos collected: "
                f"{len(video_ids)}"
            )

            if not video_ids:

                print(
                    "  No videos found"
                )

                continue

            videos = get_video_details(
                video_ids
            )

            # ------------------------------------------------
            # METRICS + SENTIMENT
            # ------------------------------------------------

            metrics = calculate_metrics(
                account,
                channel,
                videos,
                history
            )

            # Make sure actual channel ID
            # is stored

            metrics[
                "channel_id"
            ] = actual_channel_id

            results.append(
                metrics
            )

            # ------------------------------------------------
            # PRINT RESULT
            # ------------------------------------------------

            print()

            print(
                f"  Subscribers: "
                f"{metrics['youtube_subscribers']:,}"
            )

            print(
                f"  Lifetime views: "
                f"{metrics['youtube_views']:,}"
            )

            print(
                f"  Videos: "
                f"{metrics['youtube_videos']:,}"
            )

            print(
                f"  Posts ({DAYS} days): "
                f"{metrics['posts_published']}"
            )

            print(
                f"  Views ({DAYS} days): "
                f"{metrics['total_views']:,}"
            )

            print(
                f"  Engagement: "
                f"{metrics['total_engagement']:,}"
            )

            print(
                f"  Engagement rate: "
                f"{metrics['avg_engagement_rate']}%"
            )

            print(
                f"  Comments: "
                f"{metrics['comments_received']:,}"
            )

            # ------------------------------------------------
            # SENTIMENT
            # ------------------------------------------------

            print()

            print(
                "  SENTIMENT"
            )

            print(
                f"    Comments analyzed: "
                f"{metrics['sentiment_total_comments']:,}"
            )

            print(
                f"    Positive: "
                f"{metrics['sentiment_positive']} "
                f"({metrics['sentiment_positive_percentage']}%)"
            )

            print(
                f"    Neutral: "
                f"{metrics['sentiment_neutral']} "
                f"({metrics['sentiment_neutral_percentage']}%)"
            )

            print(
                f"    Negative: "
                f"{metrics['sentiment_negative']} "
                f"({metrics['sentiment_negative_percentage']}%)"
            )

            print(
                f"    Score: "
                f"{metrics['sentiment_score']}"
            )

            print(
                f"    Overall: "
                f"{metrics['overall_sentiment']}"
            )

            # ------------------------------------------------
            # TOP VIDEO
            # ------------------------------------------------

            if metrics["top_post"]:

                print()

                print(
                    f"  Top video: "
                    f"{metrics['top_post']}"
                )

                print(
                    f"  Top video views: "
                    f"{metrics['top_post_views']:,}"
                )

        except Exception as e:

            print(
                f"  ERROR: {e}"
            )

    # ========================================================
    # SAVE EVERYTHING
    # ========================================================

    save_history(
        history
    )

    save_metrics(
        results
    )

    save_videos(
        results
    )

    save_comments(
        results
    )

    # ========================================================
    # COMPLETED
    # ========================================================

    print()
    print("=" * 70)
    print("COMPLETED")
    print("=" * 70)

    print(
        f"Main metrics: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Video data: "
        f"{VIDEOS_FILE}"
    )

    print(
        f"Comment/sentiment data: "
        f"{COMMENTS_FILE}"
    )

    print(
        f"Subscriber history: "
        f"{HISTORY_FILE}"
    )

    print()

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print(
        "YOUTUBE SUMMARY"
    )

    print(
        "-" * 70
    )

    for row in results:

        print(
            f"{row['name']} | "
            f"Posts: "
            f"{row['posts_published']} | "
            f"Views: "
            f"{row['total_views']:,} | "
            f"Engagement: "
            f"{row['total_engagement']:,} | "
            f"Sentiment: "
            f"{row['overall_sentiment']} | "
            f"Positive: "
            f"{row['sentiment_positive_percentage']}% | "
            f"Negative: "
            f"{row['sentiment_negative_percentage']}%"
        )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()