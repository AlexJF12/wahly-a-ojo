#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "openai-whisper",
#   "anthropic",
# ]
# ///
"""
Transcribe an audio recording of someone describing a recipe and write
a properly formatted cookbook Markdown file.

Usage:
    uv run scripts/transcribe-recipe.py <audio-file> [options]

Options:
    --author "Name"          Author name for the frontmatter (default: Unknown)
    --model base             Whisper model: tiny, base, small, medium, large (default: base)
    --tone casual            Writing style: casual, tight, storytelling (default: casual)
    --measurements loose     Quantity style: loose, exact (default: loose)
    --language en            Language for the output recipe (default: en)

Whisper transcribes the audio locally; Claude formats the transcript
into a cookbook-style Markdown file.

Supported audio formats: .mp3, .m4a, .wav, .webm, .ogg, .flac
Output: docs/recipes/<slug>.md
"""

import argparse
import pathlib
import re
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
RECIPES_DIR = ROOT_DIR / "docs" / "recipes"

_TONE_INSTRUCTIONS = {
    "casual": (
        "Write in a natural, human voice — casual and direct, not stiff or formal. "
        "A little personality is welcome, but keep it grounded."
    ),
    "tight": (
        "Write in a stripped-down, no-nonsense style. "
        "Each instruction is one action, one sentence. "
        "No preamble, no color commentary, no filler. "
        "Notes (if any) should be a sentence or two at most."
    ),
    "storytelling": (
        "Write with warmth and personality. "
        "Weave in any anecdotes, memories, or context the speaker shared — that's the point. "
        "A short intro paragraph after the title is encouraged when there's a good story. "
        "Notes should feel like a conversation, not a warning label."
    ),
}

_MEASUREMENT_INSTRUCTIONS = {
    "loose": (
        "Quantities and times can be approximate or descriptive — "
        "\"a handful\", \"until golden\", \"about 20 minutes\". "
        "Precise numbers are fine when the speaker gave them, but don't force them."
    ),
    "exact": (
        "Use specific measurements whenever the speaker mentioned them. "
        "For anything vague, make a reasonable estimate and mark it as approximate "
        "(e.g. \"about 1 cup\", \"roughly 2 tablespoons\")."
    ),
}

SYSTEM_PROMPT_TEMPLATE = """\
You are a cookbook editor. You will receive a raw transcript of someone \
describing a recipe out loud. Turn it into a clean, properly formatted \
Markdown recipe file that matches the style of the cookbook.

Tone: {tone_instruction}

Measurements: {measurement_instruction}

Language: Write the entire recipe in {language_name}. \
If the transcript is in a different language, translate as you format.

Rules:
- Never use the phrase "a ojo" anywhere in the output.
- Do not invent ingredients or steps that were not in the transcript. \
If something is unclear, use your best judgment to stay true to what was said.
- The output must be ONLY the Markdown file, starting with --- and ending \
after the last section. No explanation, no preamble, no code fences.

Output format:

---
title: "<Recipe Title>"
author: "{author}"
course: "<one of: appetizer, bread, breakfast, dessert, drink, entree, side, soup, other>"
servings: "<e.g. 4 servings, enough for 6>"
prep_time: "<e.g. 15 min>"
cook_time: "<e.g. 30 min>"
---

# <Recipe Title>

## Ingredients

- ...

## Instructions

1. ...

## Notes

<Optional. Only include if the speaker shared tips, context, or \
stories worth keeping. Omit this section entirely if there is nothing \
worth noting.>
"""

# ISO 639-1 → English name for a handful of common languages.
# Whisper uses the same codes; anything not listed is passed through as-is.
_LANGUAGE_NAMES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ja": "Japanese", "zh": "Chinese",
    "ko": "Korean", "ar": "Arabic", "hi": "Hindi", "ru": "Russian",
    "nl": "Dutch", "pl": "Polish", "sv": "Swedish", "tr": "Turkish",
}


def slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def transcribe_audio(audio_path: pathlib.Path, whisper_model: str, language: str) -> str:
    import whisper

    print(f"Loading Whisper model '{whisper_model}'…", flush=True)
    model = whisper.load_model(whisper_model)
    print(f"Transcribing {audio_path.name}…", flush=True)
    result = model.transcribe(str(audio_path), language=language)
    return result["text"].strip()


def format_recipe(
    transcript: str,
    author: str,
    tone: str,
    measurements: str,
    language: str,
) -> str:
    import anthropic

    client = anthropic.Anthropic()
    language_name = _LANGUAGE_NAMES.get(language, language)
    system = SYSTEM_PROMPT_TEMPLATE.format(
        author=author,
        tone_instruction=_TONE_INSTRUCTIONS[tone],
        measurement_instruction=_MEASUREMENT_INSTRUCTIONS[measurements],
        language_name=language_name,
    )

    print(f"Formatting transcript with Claude (tone={tone}, measurements={measurements})…", flush=True)

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=system,
        messages=[
            {
                "role": "user",
                "content": transcript,
            }
        ],
    ) as stream:
        message = stream.get_final_message()

    # Last content block is the text response (thinking blocks come first)
    for block in reversed(message.content):
        if block.type == "text":
            return block.text.strip()

    sys.exit("Claude returned no text content.")


def extract_title(markdown: str) -> str | None:
    m = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return m.group(1).strip() if m else None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe a recipe audio recording and write a cookbook Markdown file."
    )
    parser.add_argument("audio", help="Path to the audio file")
    parser.add_argument(
        "--author",
        default="Unknown",
        help="Author name for the frontmatter (default: Unknown)",
    )
    parser.add_argument(
        "--model",
        default="base",
        metavar="WHISPER_MODEL",
        help="Whisper model size: tiny, base, small, medium, large (default: base)",
    )
    parser.add_argument(
        "--tone",
        default="casual",
        choices=list(_TONE_INSTRUCTIONS),
        help=(
            "Writing style for the recipe. "
            "casual: natural and direct (default). "
            "tight: short, no-frills, one action per step. "
            "storytelling: anecdotes and warmth, intro prose welcome."
        ),
    )
    parser.add_argument(
        "--measurements",
        default="loose",
        choices=list(_MEASUREMENT_INSTRUCTIONS),
        help=(
            "How quantities are expressed. "
            "loose: approximate and descriptive (default). "
            "exact: specific amounts; estimates flagged as approximate."
        ),
    )
    parser.add_argument(
        "--language",
        default="en",
        metavar="LANG",
        help=(
            "ISO 639-1 language code for the output recipe (default: en). "
            "Whisper uses the same code for transcription. "
            "Examples: es, fr, de, it, pt, ja, zh."
        ),
    )
    args = parser.parse_args()

    audio_path = pathlib.Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        sys.exit(f"File not found: {audio_path}")

    transcript = transcribe_audio(audio_path, args.model, args.language)
    print(f"\nTranscript ({len(transcript)} chars):\n{transcript[:300]}{'…' if len(transcript) > 300 else ''}\n")

    markdown = format_recipe(transcript, args.author, args.tone, args.measurements, args.language)

    title = extract_title(markdown)
    if not title:
        sys.exit("Could not find a # Heading in the generated Markdown. Aborting.")

    slug = slugify(title)
    out_path = RECIPES_DIR / f"{slug}.md"

    if out_path.exists():
        print(f"Warning: {out_path} already exists and will be overwritten.")

    RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")

    print(f"Saved: {out_path}")
    print()
    print("Next steps:")
    print(f"  1. Review and edit {out_path}")
    print(f"  2. Add a hero image at docs/images/{slug}/hero.jpg")
    print(f"  3. uv run scripts/validate-recipes.py {out_path}")


if __name__ == "__main__":
    main()
