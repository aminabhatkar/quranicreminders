"""
post_to_instagram.py
--------------------
Posts a 3-slide carousel to Instagram using the Meta Graph API.

Slides:
    1. Title + Arabic text
    2. Translation + Transliteration
    3. Description + Source reference

Carousel flow:
    1. Create a child container for each slide (image_url must be public)
    2. Create a carousel container referencing all children + caption
    3. Publish the carousel container

Required environment variables:
    IG_USER_ID       - Instagram Business Account user ID
    IG_ACCESS_TOKEN  - Long-lived Page/Instagram access token
"""

import os
import time
import requests


GRAPH_BASE = "https://graph.instagram.com/v21.0"


# ── Helpers ──────────────────────────────────────────────────────────────────
def _user_id() -> str:
    return os.environ["IG_USER_ID"]


def _token() -> str:
    return os.environ["IG_ACCESS_TOKEN"]


def _raise_for_error(resp: requests.Response, context: str):
    try:
        data = resp.json()
    except Exception:
        resp.raise_for_status()
        return
    if "error" in data:
        raise RuntimeError(f"{context} failed: {data['error']}")
    resp.raise_for_status()


# ── Step 1 — Create child media containers ───────────────────────────────────
def _create_child_container(image_url: str) -> str:
    """
    Uploads one image as a carousel child container.
    Returns the container ID string.
    """
    url  = f"{GRAPH_BASE}/{_user_id()}/media"
    resp = requests.post(url, params={
        "image_url":     image_url,
        "is_carousel_item": "true",
        "access_token":  _token(),
    })
    _raise_for_error(resp, f"Child container for {image_url}")
    container_id = resp.json()["id"]
    print(f"  ✓ Child container created: {container_id}")
    return container_id


# ── Step 2 — Create carousel container ───────────────────────────────────────
def _create_carousel_container(
    child_ids: list[str],
    caption: str,
    hashtags: str,
) -> str:
    """
    Creates a carousel container referencing the child IDs.
    Returns the carousel container ID.
    """
    full_caption = f"{caption}\n\n{hashtags}"

    url  = f"{GRAPH_BASE}/{_user_id()}/media"
    resp = requests.post(url, params={
        "media_type":    "CAROUSEL",
        "children":      ",".join(child_ids),
        "caption":       full_caption,
        "access_token":  _token(),
    })
    _raise_for_error(resp, "Carousel container")
    carousel_id = resp.json()["id"]
    print(f"  ✓ Carousel container created: {carousel_id}")
    return carousel_id


# ── Step 3 — Publish ─────────────────────────────────────────────────────────
def _publish_container(container_id: str) -> str:
    """
    Publishes a ready carousel container.
    Returns the published media ID.
    """
    url  = f"{GRAPH_BASE}/{_user_id()}/media_publish"
    resp = requests.post(url, params={
        "creation_id":  container_id,
        "access_token": _token(),
    })
    _raise_for_error(resp, "Publish carousel")
    media_id = resp.json()["id"]
    print(f"  ✓ Published! Media ID: {media_id}")
    return media_id


# ── Public function ───────────────────────────────────────────────────────────
def post_carousel(
    slide_urls: list[str],
    caption:    str,
    hashtags:   str,
) -> str:
    """
    Full carousel post flow for a 3-slide dua carousel.

    Args:
        slide_urls: List of 3 public R2 URLs — [slide_1, slide_2, slide_3]
        caption:    Claude-generated caption text
        hashtags:   Space-separated hashtag string

    Returns:
        The published Instagram media ID.
    """
    if len(slide_urls) < 2:
        raise ValueError(f"post_carousel requires at least 2 slides, got {len(slide_urls)}")

    print(f"\nPosting Instagram carousel ({len(slide_urls)} slides)...")

    # 1. Create child containers — one per slide with a small delay between each
    print("  Creating child containers...")
    child_ids = []
    for i, url in enumerate(slide_urls, start=1):
        container_id = _create_child_container(url)
        child_ids.append(container_id)
        if i < len(slide_urls):
            time.sleep(2)   # avoid rate-limit edge cases between uploads

    time.sleep(2)

    # 2. Create carousel container
    print("  Creating carousel container...")
    carousel_id = _create_carousel_container(
        child_ids = child_ids,
        caption   = caption,
        hashtags  = hashtags,
    )
    time.sleep(3)

    # 3. Publish
    print("  Publishing carousel...")
    media_id = _publish_container(carousel_id)

    print(f"\n✓ Carousel posted successfully to @quranic.reminders.co")
    return media_id


# ── Entry point (for testing standalone) ─────────────────────────────────────
if __name__ == "__main__":
    # Requires env vars + real public image URLs to test
    base = "https://YOUR_R2_PUBLIC_URL/duas"
    test_slides = [
        f"{base}/dua_003_slide1.jpg",
        f"{base}/dua_003_slide2.jpg",
        f"{base}/dua_003_slide3.jpg",
    ]
    test_caption = (
        "Every day we return to this dua — the most complete supplication "
        "a believer can make. ✨\n\n"
        "*Our Lord, give us in this world that which is good and in the "
        "Hereafter that which is good, and protect us from the punishment "
        "of the Fire.*\n\n"
        "— Al-Baqarah, 2:201\n\n"
        "Save this dua 🤍"
    )
    test_hashtags = (
        "#QuranDua #IslamicReminder #DuaFromQuran #Rabbana "
        "#AlBaqarah #MuslimDaily #Quran #DuaOfTheDay"
    )

    post_carousel(test_slides, test_caption, test_hashtags)
