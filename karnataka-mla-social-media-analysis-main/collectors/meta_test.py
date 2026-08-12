import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

GRAPH_API_VERSION = "v24.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MLA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "mla_profiles.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "mla_social_accounts.csv"
)


# ============================================================
# COMMON META API FUNCTION
# ============================================================

def meta_get(endpoint, params=None):

    if not META_ACCESS_TOKEN:
        print("ERROR: META_ACCESS_TOKEN is missing in .env")
        return None

    if params is None:
        params = {}

    params["access_token"] = META_ACCESS_TOKEN

    url = f"{GRAPH_URL}/{endpoint}"

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        data = response.json()

        if response.status_code != 200:

            print("\nMETA API ERROR")
            print("--------------------------------")
            print(data)
            print("--------------------------------")

            return None

        return data

    except Exception as e:

        print("\nREQUEST ERROR")
        print(e)

        return None


# ============================================================
# GET FACEBOOK PAGES CONNECTED TO META ACCOUNT
# ============================================================

def get_facebook_pages():

    print("\nSearching Facebook Pages...")

    fields = (
        "id,"
        "name,"
        "username,"
        "link,"
        "fan_count,"
        "followers_count,"
        "instagram_business_account"
    )

    data = meta_get(
        "me/accounts",
        {
            "fields": fields,
            "limit": 100
        }
    )

    if not data:
        return []

    pages = data.get("data", [])

    print(f"Facebook Pages found: {len(pages)}")

    return pages


# ============================================================
# GET FACEBOOK PAGE DETAILS
# ============================================================

def get_facebook_page(page):

    page_id = page.get("id")

    page_name = page.get("name")

    print("\nFacebook Page")
    print("--------------------------------")
    print("Name:", page_name)
    print("Page ID:", page_id)
    print("Username:", page.get("username"))
    print("Followers:", page.get("followers_count"))
    print("URL:", page.get("link"))

    return {
        "facebook_page_id": page_id,
        "facebook_page_name": page_name,
        "facebook_username": page.get("username"),
        "facebook_url": page.get("link"),
        "facebook_followers": (
            page.get("followers_count")
            or page.get("fan_count")
            or 0
        )
    }


# ============================================================
# GET FACEBOOK POSTS
# ============================================================

def get_facebook_posts(page_id, page_access_token):

    fields = (
        "id,"
        "message,"
        "created_time,"
        "permalink_url,"
        "shares,"
        "reactions.limit(0).summary(true),"
        "comments.limit(0).summary(true)"
    )

    url = f"{GRAPH_URL}/{page_id}/posts"

    try:

        response = requests.get(
            url,
            params={
                "fields": fields,
                "limit": 25,
                "access_token": page_access_token
            },
            timeout=30
        )

        data = response.json()

        if response.status_code != 200:

            print("\nFacebook Posts Error")
            print(data)

            return []

        posts = []

        for post in data.get("data", []):

            reactions = (
                post.get("reactions", {})
                .get("summary", {})
                .get("total_count", 0)
            )

            comments = (
                post.get("comments", {})
                .get("summary", {})
                .get("total_count", 0)
            )

            shares = (
                post.get("shares", {})
                .get("count", 0)
            )

            posts.append({

                "platform": "Facebook",

                "post_id": post.get("id"),

                "text": post.get(
                    "message",
                    ""
                ),

                "published_at": post.get(
                    "created_time"
                ),

                "url": post.get(
                    "permalink_url"
                ),

                "likes": reactions,

                "comments": comments,

                "shares": shares
            })

        return posts

    except Exception as e:

        print("Facebook posts request error:", e)

        return []


# ============================================================
# GET INSTAGRAM ACCOUNT FROM FACEBOOK PAGE
# ============================================================

def get_instagram_account(
    page_id,
    page_access_token
):

    fields = (
        "instagram_business_account"
    )

    url = f"{GRAPH_URL}/{page_id}"

    try:

        response = requests.get(
            url,
            params={
                "fields": fields,
                "access_token": page_access_token
            },
            timeout=30
        )

        data = response.json()

        if response.status_code != 200:

            print("\nInstagram Account Error")
            print(data)

            return None

        instagram_account = data.get(
            "instagram_business_account"
        )

        if not instagram_account:

            return None

        instagram_id = instagram_account.get(
            "id"
        )

        return instagram_id

    except Exception as e:

        print(
            "Instagram account request error:",
            e
        )

        return None


# ============================================================
# GET INSTAGRAM PROFILE
# ============================================================

def get_instagram_profile(
    instagram_id,
    page_access_token
):

    fields = (
        "id,"
        "username,"
        "name,"
        "biography,"
        "profile_picture_url,"
        "followers_count,"
        "follows_count,"
        "media_count"
    )

    url = f"{GRAPH_URL}/{instagram_id}"

    try:

        response = requests.get(
            url,
            params={
                "fields": fields,
                "access_token": page_access_token
            },
            timeout=30
        )

        data = response.json()

        if response.status_code != 200:

            print("\nInstagram Profile Error")
            print(data)

            return None

        return data

    except Exception as e:

        print(
            "Instagram profile request error:",
            e
        )

        return None


# ============================================================
# GET INSTAGRAM POSTS
# ============================================================

def get_instagram_posts(
    instagram_id,
    page_access_token
):

    fields = (
        "id,"
        "caption,"
        "media_type,"
        "media_url,"
        "permalink,"
        "timestamp,"
        "like_count,"
        "comments_count"
    )

    url = (
        f"{GRAPH_URL}/"
        f"{instagram_id}/media"
    )

    try:

        response = requests.get(
            url,
            params={
                "fields": fields,
                "limit": 25,
                "access_token": page_access_token
            },
            timeout=30
        )

        data = response.json()

        if response.status_code != 200:

            print("\nInstagram Posts Error")
            print(data)

            return []

        posts = []

        for post in data.get(
            "data",
            []
        ):

            posts.append({

                "platform": "Instagram",

                "post_id": post.get(
                    "id"
                ),

                "text": post.get(
                    "caption",
                    ""
                ),

                "media_type": post.get(
                    "media_type"
                ),

                "published_at": post.get(
                    "timestamp"
                ),

                "url": post.get(
                    "permalink"
                ),

                "likes": post.get(
                    "like_count",
                    0
                ),

                "comments": post.get(
                    "comments_count",
                    0
                )
            })

        return posts

    except Exception as e:

        print(
            "Instagram posts request error:",
            e
        )

        return []


# ============================================================
# PROCESS FACEBOOK + INSTAGRAM
# ============================================================

def process_meta():

    print("\n")
    print("=" * 70)
    print("KARNATAKA MLA META COLLECTOR")
    print("=" * 70)

    pages = get_facebook_pages()

    if not pages:

        print("\nNo Facebook Pages available.")
        print(
            "Check your Meta access token "
            "and permissions."
        )

        return

    all_accounts = []

    for index, page in enumerate(
        pages,
        start=1
    ):

        print("\n")
        print("=" * 70)
        print(
            f"[{index}/{len(pages)}] "
            f"Processing: {page.get('name')}"
        )
        print("=" * 70)

        page_id = page.get("id")

        # ----------------------------------------------------
        # PAGE ACCESS TOKEN
        # ----------------------------------------------------

        page_access_token = page.get(
            "access_token"
        )

        if not page_access_token:

            # Try requesting it separately
            page_data = meta_get(
                page_id,
                {
                    "fields": "access_token"
                }
            )

            if page_data:

                page_access_token = page_data.get(
                    "access_token"
                )

        if not page_access_token:

            print(
                "No Page Access Token available."
            )

            continue

        # ----------------------------------------------------
        # FACEBOOK
        # ----------------------------------------------------

        facebook = get_facebook_page(
            page
        )

        facebook_posts = get_facebook_posts(
            page_id,
            page_access_token
        )

        print(
            "Facebook posts:",
            len(facebook_posts)
        )

        # ----------------------------------------------------
        # INSTAGRAM
        # ----------------------------------------------------

        instagram_id = get_instagram_account(
            page_id,
            page_access_token
        )

        instagram = None
        instagram_posts = []

        if instagram_id:

            print(
                "Instagram ID:",
                instagram_id
            )

            instagram = get_instagram_profile(
                instagram_id,
                page_access_token
            )

            instagram_posts = get_instagram_posts(
                instagram_id,
                page_access_token
            )

            print(
                "Instagram posts:",
                len(instagram_posts)
            )

        else:

            print(
                "Instagram account not connected "
                "to this Facebook Page."
            )

        # ----------------------------------------------------
        # SAVE ACCOUNT DATA
        # ----------------------------------------------------

        account = {

            "facebook_page_id":
                facebook.get(
                    "facebook_page_id"
                ),

            "facebook_page_name":
                facebook.get(
                    "facebook_page_name"
                ),

            "facebook_username":
                facebook.get(
                    "facebook_username"
                ),

            "facebook_url":
                facebook.get(
                    "facebook_url"
                ),

            "facebook_followers":
                facebook.get(
                    "facebook_followers",
                    0
                ),

            "instagram_user_id":
                instagram_id,

            "instagram_username":
                (
                    instagram.get(
                        "username"
                    )
                    if instagram
                    else None
                ),

            "instagram_name":
                (
                    instagram.get(
                        "name"
                    )
                    if instagram
                    else None
                ),

            "instagram_url":
                (
                    f"https://www.instagram.com/"
                    f"{instagram.get('username')}/"
                    if instagram
                    and instagram.get(
                        "username"
                    )
                    else None
                ),

            "instagram_followers":
                (
                    instagram.get(
                        "followers_count",
                        0
                    )
                    if instagram
                    else 0
                ),

            "instagram_following":
                (
                    instagram.get(
                        "follows_count",
                        0
                    )
                    if instagram
                    else 0
                ),

            "instagram_media_count":
                (
                    instagram.get(
                        "media_count",
                        0
                    )
                    if instagram
                    else 0
                ),

            "facebook_posts":
                len(facebook_posts),

            "instagram_posts":
                len(instagram_posts)
        }

        all_accounts.append(account)

    # ========================================================
    # SAVE CSV
    # ========================================================

    if all_accounts:

        df = pd.DataFrame(
            all_accounts
        )

        df.to_csv(
            OUTPUT_FILE,
            index=False
        )

        print("\n")
        print("=" * 70)
        print("COMPLETED")
        print("=" * 70)

        print(
            f"Saved to: {OUTPUT_FILE}"
        )

        print("\nFinal Meta data:")

        print(
            df.to_string(
                index=False
            )
        )

    else:

        print(
            "\nNo Meta accounts were collected."
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    process_meta()