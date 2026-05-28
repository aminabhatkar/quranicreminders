# @quranic.reminders.co — Daily Dua Automation

A fully automated, human-in-the-loop pipeline that wakes up every day, picks a Quranic dua from `duas.json`, renders a beautiful 3-slide pastel carousel using Pillow, writes a peaceful caption using Claude, and asks for your approval on Telegram before posting to Instagram — all on a randomised schedule so it never looks like a bot.

---

## How It Works

```
GitHub Actions triggers (start of day's posting window)
            ↓
  Sleep random minutes within window
            ↓
  Pick dua → Render 3 carousel slides (Pillow)
  Slide 1: Title + Arabic text (Amiri font)
  Slide 2: Translation + Transliteration
  Slide 3: Description + Surah reference
            ↓
  Claude writes caption + 30 hashtags
            ↓
  Telegram sends you a preview:
  [slide 1] [slide 2] [slide 3]
  [✅ Post] [❌ Skip] [✏️ Edit Caption]
            ↓
  You approve (or edit) on your phone
            ↓
  Upload all 3 slides to Cloudflare R2
            ↓
  Post 3-slide carousel to Instagram
            ↓
  Telegram confirms: ✅ Posted!
```

---

## Project Structure

```
├── main.py                        # Orchestrates the full pipeline
├── generate_image.py              # Pillow carousel renderer (3 pastel slides)
├── claude_routine.py              # Calls Anthropic Claude API for caption + hashtags
├── telegram_approval.py           # Sends carousel preview, waits for approval
├── upload_to_r2.py                # Uploads all 3 slides to Cloudflare R2
├── post_to_instagram.py           # Posts 3-slide carousel via Meta Graph API
├── duas.json                      # Dua library (57 Quranic duas)
├── requirements.txt
├── assets/
│   └── fonts/
│       ├── Amiri-Regular.ttf      # Arabic text (Slide 1)
│       ├── Amiri-Bold.ttf         # Arabic bold variant
│       ├── Cormorant-Regular.ttf  # Translation body
│       ├── Cormorant-Italic.ttf   # Transliteration / italic
│       ├── Poppins-Regular.ttf    # Description body text
│       ├── Poppins-Medium.ttf     # Labels, handle
│       └── Poppins-SemiBold.ttf   # Slide titles
├── output_images/                 # Generated slides saved here (gitignored)
└── .github/
    └── workflows/
        └── daily_dua.yml          # Cron job — runs once daily per schedule
```

---

## Carousel Design

Each dua generates **3 slides**, all sharing the same pastel colour theme:

| Slide | Content | Font |
|-------|---------|------|
| 1 | Surah/verse label · Title · Arabic text (large, centred) | Amiri Bold |
| 2 | Translation (large italic) · Transliteration (muted) | Cormorant Italic |
| 3 | "When to Recite" description · Surah name · Verse reference | Poppins |

### Pastel Palettes

One colour theme is assigned per dua, cycling deterministically through 5 palettes:

| Palette | Background | Accent |
|---------|-----------|--------|
| Rose Blush | Soft blush pinks | Deep rose |
| Sage Mist | Sage green to mint | Forest green |
| Lavender Haze | Lilac to lavender | Deep violet |
| Golden Sand | Warm cream | Antique gold |
| Sky Bloom | Powder blue to periwinkle | Deep sky blue |

Every slide shares consistent decorative elements: thin rounded border, corner diamond ornaments, centred divider lines, and the `@quranic.reminders.co` handle at the bottom.

---

## Posting Schedule (IST)

Posts **once daily** at a random time within the day's window, so the posting pattern never looks automated.

| Day | Window (IST) | Notes |
|-----|-------------|-------|
| Monday – Thursday | 9:00 AM – 12:00 PM | Morning peak engagement |
| Friday | 12:00 PM – 2:00 PM | Post-Jumu'ah audience spike |
| Saturday – Sunday | 10:00 AM – 1:00 PM | Weekend late-morning sweet spot |

GitHub Actions triggers at the start of each window. `main.py` then reads `WINDOW_MINUTES` from the environment and sleeps a random number of minutes before running — so the Telegram approval message arrives at an unpredictable time within the window.

---

## Telegram Approval Flow

Before anything is uploaded or posted, you receive a Telegram preview:

1. **Three slides** — the full carousel sent as a photo group, with the dua title, Arabic text, and surah/verse reference as the caption
2. **Caption + hashtags** — the Claude-generated text
3. **Three inline buttons:**

| Button | Action |
|--------|--------|
| ✅ Post | Proceeds — uploads to R2 and posts the carousel |
| ❌ Skip | Skips today's slot, no post made |
| ✏️ Edit Caption | Bot prompts you to type a new caption; shows a preview with Confirm / Revert buttons |

**Timeout:** If there is no response within **30 minutes**, the slot is **automatically posted with the original Claude-generated caption** and you receive a timeout notification. This applies even if you were mid-edit when the timeout hit — your in-progress edit is discarded and the original caption is used. To actively cancel a slot, tap **❌ Skip**.

---

## duas.json Format

```json
[
  {
    "id": 3,
    "title": "Dua for Good in Both Worlds",
    "arabic": "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
    "transliteration": "Rabbana atina fid dunyaa hasanatanw wa fil aakhirati hasanatanw wa qinaa azaaban Naar",
    "translation": "Our Lord, give us in this world that which is good and in the Hereafter that which is good, and protect us from the punishment of the Fire.",
    "surah": "Al-Baqarah",
    "verse": "2:201",
    "theme": "dunya_akhira",
    "keywords": ["dunya", "akhira", "hereafter", "protection", "hellfire", "good life", "blessing"],
    "description": "One of the most beloved duas any believer can recite. It balances asking for goodness in this life while never forgetting the hereafter. Recite it daily, especially after salah.",
    "used": false
  }
]
```

**Fields:**
- **`arabic`** — displayed large on Slide 1 in Amiri font
- **`transliteration`** — shown muted beneath the translation on Slide 2
- **`translation`** — large italic centrepiece of Slide 2
- **`theme`** — used by Claude to generate relevant hashtags (e.g. `repentance`, `guidance`, `family`)
- **`keywords`** — fed into the Claude caption prompt for richer, more targeted hashtags
- **`description`** — the "when to recite" body text on Slide 3
- **`used`** — set to `true` after posting. When all 57 duas are used, the cycle resets automatically.

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Fonts

All fonts are already included in `assets/fonts/`. No action needed.

If you ever need to re-download them, all are free from Google Fonts:
- [Amiri](https://fonts.google.com/specimen/Amiri) — `Amiri-Regular.ttf`, `Amiri-Bold.ttf`
- [Cormorant Garamond](https://fonts.google.com/specimen/Cormorant+Garamond) — `CormorantGaramond-Regular.ttf` → rename to `Cormorant-Regular.ttf`, same for Italic
- [Poppins](https://fonts.google.com/specimen/Poppins) — `Poppins-Regular.ttf`, `Poppins-Medium.ttf`, `Poppins-SemiBold.ttf`

### 4. Create a Telegram bot

1. Message [@BotFather](https://t.me/botfather) → `/newbot` → follow the steps
2. Copy the **bot token** it gives you
3. Message [@userinfobot](https://t.me/userinfobot) to get your **personal chat ID**
4. Start a conversation with your new bot (send it any message) so it can message you back

### 5. Get an Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in → **Settings → API Keys → Create Key**
3. Copy the key (you'll only see it once)
4. Add a small amount of credit under **Settings → Billing** — the pipeline uses Claude Haiku, which costs a few cents per month at once-daily posting

### 6. Set up Cloudflare R2

1. Go to [Cloudflare dashboard](https://dash.cloudflare.com) → **R2**
2. Create a bucket
3. Enable **Public Access** on the bucket (required — Instagram fetches images by URL)
4. Go to **Manage R2 API Tokens** → create a token with **Object Read & Write** permission
5. Note your Account ID, Access Key ID, Secret Access Key, bucket name, and public URL (`https://pub-xxxx.r2.dev`)

### 7. Set up Instagram Graph API

1. Create a **Meta Developer App** at [developers.facebook.com](https://developers.facebook.com)
2. Add the **Instagram Graph API** product
3. Connect your Instagram **Business** or **Creator** account
4. Generate a **long-lived access token** via the [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
5. Note your **Instagram User ID** and **Access Token**

> **Note:** The access token expires every **60 days**. Set a calendar reminder to refresh it before it expires — the pipeline will fail silently if the token is stale.

### 8. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add all of the following:

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | From [console.anthropic.com](https://console.anthropic.com) |
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | R2 API token access key |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret key |
| `R2_BUCKET_NAME` | Your R2 bucket name |
| `R2_PUBLIC_URL` | Public bucket URL e.g. `https://pub-xxxx.r2.dev` |
| `IG_USER_ID` | Instagram Business/Creator Account ID |
| `IG_ACCESS_TOKEN` | Long-lived token from Graph API Explorer |
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_CHAT_ID` | From @userinfobot |

### 9. Run locally to test

```bash
export ANTHROPIC_API_KEY=your_key
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id
export R2_ACCOUNT_ID=your_id
export R2_ACCESS_KEY_ID=your_key
export R2_SECRET_ACCESS_KEY=your_secret
export R2_BUCKET_NAME=your_bucket
export R2_PUBLIC_URL=https://pub-xxxx.r2.dev
export IG_USER_ID=your_id
export IG_ACCESS_TOKEN=your_token

WINDOW_MINUTES=1 python main.py
```

Setting `WINDOW_MINUTES=1` skips the random sleep so it runs immediately.

### 10. Do a manual GitHub Actions test

1. Go to your repo → **Actions** tab
2. Click **Daily Dua Post** → **Run workflow**
3. Set `window_minutes` to `1` for an immediate run
4. Watch the logs in real time
5. Approve on Telegram when the preview arrives
6. Confirm the carousel appears on Instagram

---

## Customisation

**Change the posting schedule** — edit `WINDOW_IST` in `main.py` and update the cron expressions in `.github/workflows/daily_dua.yml` (convert IST → UTC by subtracting 5 hours 30 minutes).

**Change the approval timeout** — edit `TIMEOUT_SECONDS` in `telegram_approval.py`:
```python
TIMEOUT_SECONDS = 30 * 60   # e.g. 15 * 60 for 15 minutes
```
On timeout the pipeline auto-posts with the original Claude caption. To skip instead, change the timeout return in `request_approval()` to `{"approved": False, ...}`.

**Add or edit duas** — edit `duas.json`. Each dua needs all fields: `id`, `title`, `arabic`, `transliteration`, `translation`, `surah`, `verse`, `theme`, `keywords`, `description`, `used`.

**Change the handle** — update `HANDLE` at the top of `generate_image.py`:
```python
HANDLE = "@quranic.reminders.co"
```

**Extend the carousel** — add a 4th slide by writing a `render_slide_4()` function in `generate_image.py`, appending it to the `generate()` return dict, and updating `main.py` and `post_to_instagram.py` accordingly.

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Image generation | [Pillow](https://python-pillow.org/) |
| Arabic rendering | [Amiri font](https://fonts.google.com/specimen/Amiri) via Pillow |
| AI caption writing | [Anthropic Claude](https://www.anthropic.com) (claude-haiku-4-5) |
| Human approval | [Telegram Bot API](https://core.telegram.org/bots/api) |
| Object storage | [Cloudflare R2](https://developers.cloudflare.com/r2/) |
| Social posting | [Meta Graph API](https://developers.facebook.com/docs/instagram-api/) |
| Automation | [GitHub Actions](https://docs.github.com/en/actions) |

---

## License

MIT — free to fork and adapt for your own Islamic reminder page.

---

*اللَّهُمَّ آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ*
