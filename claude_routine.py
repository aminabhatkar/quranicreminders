"""
claude_routine.py
-----------------
Calls the Anthropic Claude API to generate a peaceful Instagram caption
and relevant hashtags for a given Quranic dua.

Required environment variables:
    ANTHROPIC_API_KEY   - From https://console.anthropic.com
"""

import os
import json
import anthropic


# ── Client ────────────────────────────────────────────────────────────────────
def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set.")
    return anthropic.Anthropic(api_key=api_key)


# ── Prompts ───────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a calm, spiritual social media writer for the Instagram page @quranic.reminders.co,
which shares duas (supplications) directly from the Holy Quran. Your writing style is:
- Simple, warm, and deeply peaceful
- Rooted in the Quran — always reference where the dua comes from
- Never preachy, never overly formal
- Invites the reader to pause, reflect, and make the dua themselves
- Feels like a gentle reminder, not a lecture
- Connects the reader emotionally to the words of Allah

You always respond with valid JSON only. No preamble, no markdown fences, no extra text.
"""

USER_PROMPT_TEMPLATE = """\
Write an Instagram caption and hashtags for this Quranic dua:

Title: "{title}"
Arabic: {arabic}
Transliteration: {transliteration}
Translation: "{translation}"
Surah & Verse: {surah} ({verse})
Theme: {theme}
Keywords: {keywords}
Context: {description}

Return ONLY this exact JSON structure with no extra text:
{{
  "caption": "2 to 3 short peaceful sentences connecting the reader emotionally to this dua and when to recite it. Then on a new line the translation wrapped in asterisks like *translation here*. Then on a new line the source reference like — {surah}, {verse}. End with one gentle call-to-action such as Save this dua 🤍 or Share with someone who needs this ✨",
  "hashtags": "exactly 30 hashtags as a single space-separated string. Mix Quranic duas, Islamic reminders, spiritual wellness, the specific theme of this dua, and general inspirational tags."
}}
"""


# ── Main function ─────────────────────────────────────────────────────────────
def generate_caption_and_hashtags(dua: dict) -> dict:
    """
    Given a dua dict (from duas.json), calls Claude and returns:
        {
            "caption":  "...",
            "hashtags": "#QuranDua #IslamicReminder ..."
        }
    """
    client = _get_client()

    prompt = USER_PROMPT_TEMPLATE.format(
        title          = dua["title"],
        arabic         = dua["arabic"],
        transliteration= dua["transliteration"],
        translation    = dua["translation"],
        surah          = dua["surah"],
        verse          = dua["verse"],
        theme          = dua["theme"],
        keywords       = ", ".join(dua.get("keywords", [])),
        description    = dua.get("description", ""),
    )

    print("Calling Claude API to generate caption and hashtags...")

    message = client.messages.create(
        model      = "claude-haiku-4-5-20251001",
        max_tokens = 1024,
        system     = SYSTEM_PROMPT,
        messages   = [{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Strip accidental markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON:\n{raw}") from e

    if "caption" not in result or "hashtags" not in result:
        raise ValueError(f"Claude response missing expected keys:\n{result}")

    print("✓ Caption and hashtags generated.")
    print(f"  Preview: {result['caption'][:90]}...")

    return result


# ── Entry point (for testing standalone) ─────────────────────────────────────
if __name__ == "__main__":
    test_dua = {
        "id":              3,
        "title":           "Dua for Good in Both Worlds",
        "arabic":          "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        "transliteration": "Rabbana atina fid dunyaa hasanatanw wa fil aakhirati hasanatanw wa qinaa azaaban Naar",
        "translation":     "Our Lord, give us in this world that which is good and in the Hereafter that which is good and protect us from the punishment of the Fire.",
        "surah":           "Al-Baqarah",
        "verse":           "2:201",
        "theme":           "dunya_akhira",
        "keywords":        ["dunya", "akhira", "hereafter", "protection", "hellfire", "good life", "blessing"],
        "description":     "One of the most beloved duas any believer can recite. It balances asking for goodness in this life while never forgetting the hereafter. Recite it daily, especially after salah.",
    }

    output = generate_caption_and_hashtags(test_dua)
    print("\nFull Caption:\n")
    print(output["caption"])
    print("\nHashtags:\n")
    print(output["hashtags"])
