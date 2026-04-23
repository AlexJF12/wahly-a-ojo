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
    uv run scripts/transcribe-recipe.py <audio-file> [--author "Name"] [--model base]

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

SYSTEM_PROMPT = """\
You are a cookbook editor. You will receive a raw transcript of someone \
describing a recipe out loud. Turn it into a clean, properly formatted \
Markdown recipe file that matches the style of the cookbook.

Rules:
- Write in a natural, human voice — casual and direct, not stiff or formal.
- Never use the phrase "a ojo" anywhere in the output.
- Quantities and times can be approximate or descriptive ("a handful", \
"until golden", "about 20 minutes") — that is the spirit of this cookbook.
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


def slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def transcribe_audio(audio_path: pathlib.Path, whisper_model: str) -> str:
    import whisper

    print(f"Loading Whisper model '{whisper_model}'…", flush=True)
    model = whisper.load_model(whisper_model)
    print(f"Transcribing {audio_path.name}…", flush=True)
    result = model.transcribe(str(audio_path))
    return result["text"].strip()


def format_recipe(transcript: str, author: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    system = SYSTEM_PROMPT.replace("{author}", author)

    print("Formatting transcript with Claude…", flush=True)

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
    args = parser.parse_args()

    audio_path = pathlib.Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        sys.exit(f"File not found: {audio_path}")

    transcript = transcribe_audio(audio_path, args.model)
    print(f"\nTranscript ({len(transcript)} chars):\n{transcript[:300]}{'…' if len(transcript) > 300 else ''}\n")

    markdown = format_recipe(transcript, args.author)

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
