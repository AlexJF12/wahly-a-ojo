#!/usr/bin/env python3
"""
Transcribe an audio recording of someone describing a recipe and write
a properly formatted cookbook Markdown file.

Usage:
    python scripts/transcribe-recipe.py <audio-file> [--author "Name"]

Supported audio formats: .mp3, .m4a, .wav, .webm
Output: docs/recipes/<slug>.md
"""

import argparse
import base64
import pathlib
import re
import sys

MEDIA_TYPES = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
}

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
RECIPES_DIR = ROOT_DIR / "docs" / "recipes"

SYSTEM_PROMPT = """\
You are a cookbook editor. Your job is to listen to a voice recording of \
someone describing a recipe and produce a clean, properly formatted Markdown \
recipe file that matches the style of the cookbook.

Rules:
- Write in a natural, human voice — casual and direct, not stiff or formal.
- Never use the phrase "a ojo" anywhere in the recipe text.
- Quantities and times can be approximate or descriptive ("a handful", \
"until golden", "about 20 minutes") — that is the spirit of this cookbook.
- Do not invent ingredients or steps that were not described. If something is \
unclear, use your best judgment to stay true to what was said.
- The output must be ONLY the Markdown file, starting with --- and ending \
after the last section. No explanation, no preamble.

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


def transcribe(audio_path: pathlib.Path, author: str) -> str:
    try:
        import anthropic
    except ImportError:
        sys.exit("anthropic package not found. Run: pip install anthropic")

    suffix = audio_path.suffix.lower()
    media_type = MEDIA_TYPES.get(suffix)
    if not media_type:
        sys.exit(
            f"Unsupported audio format: {suffix}. "
            f"Supported: {', '.join(MEDIA_TYPES)}"
        )

    audio_data = base64.standard_b64encode(audio_path.read_bytes()).decode()

    client = anthropic.Anthropic()

    system = SYSTEM_PROMPT.replace("{author}", author)

    print(f"Sending {audio_path.name} to Claude…", flush=True)

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=system,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "audio",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": audio_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Transcribe and format this recipe recording "
                            "as a cookbook Markdown file following the rules above."
                        ),
                    },
                ],
            }
        ],
    ) as stream:
        markdown = stream.get_final_message().content[-1].text

    return markdown


def extract_title(markdown: str) -> str | None:
    m = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return m.group(1).strip() if m else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Audio → recipe Markdown")
    parser.add_argument("audio", help="Path to the audio file")
    parser.add_argument(
        "--author",
        default="Unknown",
        help="Author name to embed in the frontmatter (default: Unknown)",
    )
    args = parser.parse_args()

    audio_path = pathlib.Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        sys.exit(f"File not found: {audio_path}")

    markdown = transcribe(audio_path, args.author)

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
    print(f"Next steps:")
    print(f"  1. Review and edit {out_path}")
    print(f"  2. Add a hero image at docs/images/{slug}/hero.jpg")
    print(f"  3. Run: python scripts/validate-recipes.py {out_path}")


if __name__ == "__main__":
    main()
