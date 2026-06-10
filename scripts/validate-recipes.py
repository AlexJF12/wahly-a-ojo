#!/usr/bin/env python3
"""
Validate recipe Markdown files against the cookbook spec.

Usage:
    # Validate specific files (used by CI on changed files):
    python scripts/validate-recipes.py docs/recipes/my-recipe.md [...]

    # Validate all recipes:
    python scripts/validate-recipes.py
"""

import pathlib
import re
import sys

import yaml

ROOT_DIR    = pathlib.Path(__file__).resolve().parent.parent
DOCS_DIR    = ROOT_DIR / "docs"
RECIPES_DIR = DOCS_DIR / "recipes"

VALID_COURSES = {
    "appetizer", "bread", "breakfast", "dessert",
    "drink", "entree", "side", "soup", "other",
}

MAX_IMAGE_MB = 2.0


def validate(path: pathlib.Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for the given recipe file."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"Cannot read file: {exc}")
        return errors, warnings

    # ── Frontmatter ──────────────────────────────────────────
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm:
        errors.append(
            "Missing YAML frontmatter. "
            "Add --- delimiters at the very top of the file."
        )
        return errors, warnings  # can't check further without frontmatter

    try:
        meta = yaml.safe_load(fm.group(1))
    except yaml.YAMLError as exc:
        errors.append(f"Invalid YAML frontmatter: {exc}")
        return errors, warnings

    if not isinstance(meta, dict):
        errors.append("Frontmatter must be a YAML key-value mapping.")
        return errors, warnings

    # Required fields
    if not meta.get("title"):
        errors.append(
            'Missing required field "title". '
            'Add title: "Your Recipe Name" to the frontmatter.'
        )

    if not meta.get("author"):
        errors.append(
            'Missing required field "author". '
            'Add author: "Your Name" to the frontmatter.'
        )

    course = meta.get("course")
    if not course:
        errors.append(
            'Missing required field "course". '
            f'Must be one of: {", ".join(sorted(VALID_COURSES))}.'
        )
    elif course.lower() not in VALID_COURSES:
        errors.append(
            f'Invalid course value "{course}". '
            f'Must be one of: {", ".join(sorted(VALID_COURSES))}.'
        )

    # Encouraged field
    if not meta.get("servings"):
        warnings.append(
            'Consider adding "servings" (e.g. servings: "4 servings") '
            "so readers know the yield."
        )

    # Optional family commentary
    commentary = meta.get("commentary")
    if commentary is not None:
        if not isinstance(commentary, list):
            errors.append(
                '"commentary" must be a list of {author, text} entries.'
            )
        else:
            for idx, entry in enumerate(commentary, start=1):
                if not isinstance(entry, dict) or not entry.get("author") or not entry.get("text"):
                    warnings.append(
                        f'"commentary" entry {idx} is missing "author" or "text" '
                        "and will be skipped."
                    )

    # ── Body sections ─────────────────────────────────────────
    body = content[fm.end():]

    if not re.search(r"^## Ingredients", body, re.MULTILINE):
        errors.append(
            'Missing "## Ingredients" section. '
            "Add a level-2 heading followed by an ingredient list."
        )
    elif not re.search(r"^## Ingredients\s*\n+\S", body, re.MULTILINE):
        errors.append(
            '"## Ingredients" section has no content below it. '
            "Add at least one ingredient."
        )

    if not re.search(r"^## Instructions", body, re.MULTILINE):
        errors.append(
            'Missing "## Instructions" section. '
            "Add a level-2 heading followed by numbered steps."
        )
    elif not re.search(r"^## Instructions\s*\n+\S", body, re.MULTILINE):
        errors.append(
            '"## Instructions" section has no content below it. '
            "Add at least one step."
        )

    # ── Images ───────────────────────────────────────────────
    img_refs = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", content)

    if not img_refs:
        warnings.append(
            "No images found. Consider adding at least one photo "
            "(place it in docs/images/<recipe-slug>/ and reference it as "
            "![description](../images/<slug>/hero.jpg))."
        )

    for _alt, img_path in img_refs:
        if img_path.startswith(("http://", "https://")):
            warnings.append(
                f'External image URL detected: "{img_path}". '
                "Prefer local images stored in docs/images/."
            )
            continue

        abs_img = (path.parent / img_path).resolve()
        if not abs_img.exists():
            errors.append(
                f'Image not found: "{img_path}". '
                f"Expected file at: {abs_img}. "
                "Create the folder docs/images/<recipe-slug>/ and add the image."
            )
        else:
            size_mb = abs_img.stat().st_size / (1024 * 1024)
            if size_mb > MAX_IMAGE_MB:
                warnings.append(
                    f'Image "{img_path}" is {size_mb:.1f} MB '
                    f"(max {MAX_IMAGE_MB} MB). "
                    "Resize with: "
                    f"magick {abs_img.name} -resize \"1600x1600>\" -quality 85 output.jpg"
                )

    return errors, warnings


def main() -> None:
    if len(sys.argv) > 1:
        paths = [pathlib.Path(p) for p in sys.argv[1:] if p.endswith(".md")]
    else:
        paths = sorted(RECIPES_DIR.glob("*.md"))

    if not paths:
        print("No recipe files to validate.")
        sys.exit(0)

    all_errors: list[str] = []
    all_warnings: list[str] = []

    for path in paths:
        errs, warns = validate(path)
        for msg in warns:
            all_warnings.append(f"{path.name}: {msg}")
        for msg in errs:
            all_errors.append(f"{path.name}: {msg}")

    if all_warnings:
        print("\nWarnings:")
        for w in all_warnings:
            print(f"  [warn] {w}")

    if all_errors:
        print("\nErrors:")
        for e in all_errors:
            print(f"  [error] {e}")
        print(
            f"\n{len(all_errors)} error(s) in {len(paths)} file(s). "
            "Fix the issues above and push again."
        )
        sys.exit(1)

    print(f"All {len(paths)} recipe file(s) passed validation.")


if __name__ == "__main__":
    main()
