"""
main.py
-------
Orchestrates the full daily dua pipeline with:
  - Random delay within a per-day time window (IST)
  - Telegram preview + human approval before posting
  - Claude-generated caption + hashtags
  - Pillow image rendering
  - Cloudflare R2 upload
  - Instagram carousel post

Triggered by GitHub Actions once daily.
Window length is passed via environment variable: WINDOW_MINUTES=<int>
(set by the workflow based on day-of-week; defaults to 60 if not set).
"""

import os
import sys
import time
import random

from generate_image    import generate
from claude_routine    import generate_caption_and_hashtags
from upload_to_r2      import upload_images
from post_to_instagram import post_carousel
from telegram_approval import request_approval, notify_posted, notify_error

# IST = UTC+5:30
# The workflow cron fires at the start of each day's posting window.
# WINDOW_MINUTES is passed in by the workflow (180 for Mon–Thu & Sat–Sun,
# 120 for Friday). main.py sleeps a random duration within that window
# so the actual post lands unpredictably — keeping the account organic.

# Posting windows per day for logging purposes (IST)
WINDOW_IST = {
    0: (9,  12),   # Monday
    1: (9,  12),   # Tuesday
    2: (9,  12),   # Wednesday
    3: (9,  12),   # Thursday
    4: (12, 14),   # Friday  — post-Jumu'ah peak
    5: (10, 13),   # Saturday
    6: (10, 13),   # Sunday
}


def random_sleep_within_window(window_minutes: int):
    from datetime import datetime, timezone, timedelta

    IST = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(IST)
    day = now.weekday()

    window = WINDOW_IST[day]
    # Sleep anywhere from 1 minute up to (window_minutes - 5) to leave
    # enough runway for the pipeline itself to complete inside the window.
    max_sleep = max(1, window_minutes - 5)
    sleep_minutes = random.randint(1, 3)

    print(f"  Day            : {now.strftime('%A')}")
    print(f"  Window (IST)   : {window[0]}:00 – {window[1]}:00")
    print(f"  Window length  : {window_minutes} min")
    print(f"  Sleeping        : {sleep_minutes} min before running pipeline...")

    time.sleep(sleep_minutes * 60)


def run():
    window_minutes = int(os.environ.get("WINDOW_MINUTES", "60"))

    print("=" * 55)
    print("  @quranic.reminders.co  —  Daily Dua Pipeline")
    print("=" * 55)

    try:
        # ── Random delay within window ────────────────────────────────────────
        print("\n[0/5] Calculating random delay within window...")
        random_sleep_within_window(window_minutes)

        # ── Step 1: Generate images ───────────────────────────────────────────
        print("\n[1/5] Generating images with Pillow...")
        result = generate()
        dua    = result["dua"]

        print(f'\n  Dua   : "{dua["translation"][:70]}..."')
        print(f'  Source: {dua["surah"]}, {dua["verse"]}')

        # 3-slide carousel: Arabic, Translation, Description
        image_paths = {
            "slide_1": result["slide_1"],   # Title + Arabic
            "slide_2": result["slide_2"],   # Translation + Transliteration
            "slide_3": result["slide_3"],   # Description + Source
        }

        # ── Step 2: Claude generates caption + hashtags ───────────────────────
        print("\n[2/5] Calling Claude for caption and hashtags...")
        content  = generate_caption_and_hashtags(dua)
        caption  = content["caption"]
        hashtags = content["hashtags"]

        # ── Step 3: Telegram approval ─────────────────────────────────────────
        print("\n[3/5] Requesting Telegram approval...")
        decision = request_approval(
            image_paths = image_paths,
            caption     = caption,
            hashtags    = hashtags,
            quote       = dua,
        )

        if not decision["approved"]:
            print("\n  Post skipped. Pipeline complete.")
            sys.exit(0)

        # Use potentially edited caption
        final_caption  = decision["caption"]
        final_hashtags = decision["hashtags"]

        # ── Step 4: Upload all slides to R2 ──────────────────────────────────
        print("\n[4/5] Uploading carousel slides to Cloudflare R2...")
        urls = upload_images(image_paths)

        if not all(k in urls for k in ("slide_1", "slide_2", "slide_3")):
            raise RuntimeError("One or more carousel slides failed to upload to R2.")

        # ── Step 5: Post carousel to Instagram ───────────────────────────────
        print("\n[5/5] Posting carousel to Instagram...")
        media_id = post_carousel(
            slide_urls = [urls["slide_1"], urls["slide_2"], urls["slide_3"]],
            caption    = final_caption,
            hashtags   = final_hashtags,
        )

        # ── Notify success ────────────────────────────────────────────────────
        notify_posted(media_id, dua)

        print("\n" + "=" * 55)
        print("  ✓ Pipeline complete!")
        print(f"  Instagram Media ID : {media_id}")
        print(f"  R2 Slide 1         : {urls.get('slide_1')}")
        print(f"  R2 Slide 2         : {urls.get('slide_2')}")
        print(f"  R2 Slide 3         : {urls.get('slide_3')}")
        print("=" * 55)

    except Exception as e:
        error_msg = str(e)
        print(f"\n✗ Pipeline failed: {error_msg}")
        notify_error(error_msg)
        sys.exit(1)


if __name__ == "__main__":
    run()
