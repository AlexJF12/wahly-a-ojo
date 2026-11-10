"""
MkDocs hooks for Wahly a Ojo.

on_pre_build  — regenerate docs/index.md from the current recipe collection.
on_page_markdown — inject a metadata block and back-link into each recipe page,
                   and mark up the Peanut Gallery dialogue.

Recipes with `gallery: filler` in their frontmatter still have placeholder
Peanut Gallery comments. The build lists them and the page labels them.
"""

import html
import logging
import pathlib
import re
import zlib

import yaml

log = logging.getLogger("mkdocs.hooks.wahly")

# `**Name:** comment` — any name, so anyone in the family can chime in.
_OPINION_RE = re.compile(r"^\*\*([^*:]{1,40}):\*\*\s*(.*)$")

_FILLER_NOTE = (
    '<p class="gallery-filler">Placeholder comments. '
    "The real ones are still being written.</p>\n"
)

# Populated by on_pre_build, read by on_page_markdown for the "More from" block.
_BY_AUTHOR: dict[str, list[dict]] = {}


def _parse_recipe(path: pathlib.Path) -> dict | None:
    content = path.read_text(encoding="utf-8")
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm:
        return None
    try:
        meta = yaml.safe_load(fm.group(1))
    except yaml.YAMLError:
        return None
    if not isinstance(meta, dict):
        return None

    # First image reference in the file
    img = re.search(r"!\[[^\]]*\]\(([^)]+)\)", content)
    hero = None
    if img:
        # Recipe image refs look like ../images/slug/hero.jpg
        # From the homepage (docs/index.md) the correct relative path is images/slug/hero.jpg
        raw = img.group(1)
        hero = raw.removeprefix("../")

    return {
        "slug": path.stem,
        "title": meta.get("title") or path.stem,
        "author": meta.get("author") or "",
        "course": (meta.get("course") or "other").lower().strip(),
        "servings": meta.get("servings") or "",
        "prep_time": meta.get("prep_time") or "",
        "cook_time": meta.get("cook_time") or "",
        "hero": hero,
        "filler": _is_filler(meta),
    }


def on_pre_build(config, **kwargs):
    """Regenerate docs/index.md with a book-style table of contents."""
    docs_dir = pathlib.Path(config["docs_dir"])
    recipes_dir = docs_dir / "recipes"
    if not recipes_dir.exists():
        return

    recipes = []
    for f in sorted(recipes_dir.glob("*.md")):
        r = _parse_recipe(f)
        if r:
            recipes.append(r)

    if not recipes:
        return

    filler = [r["slug"] for r in recipes if r["filler"]]
    if filler:
        log.info(
            "Peanut Gallery still filler in %d of %d recipes: %s",
            len(filler), len(recipes), ", ".join(filler),
        )

    by_author: dict[str, list[dict]] = {}
    for r in recipes:
        author = r["author"] or "Unknown"
        by_author.setdefault(author, []).append(r)

    _BY_AUTHOR.clear()
    _BY_AUTHOR.update(by_author)

    chapters = ""
    for i, (author, author_recipes) in enumerate(sorted(by_author.items()), 1):
        entries = ""
        for r in author_recipes:
            # Time-based detail (course is shown as a colored badge instead).
            # Keep it short for the single-line index: drop parentheticals and
            # any "/ alternative" so verbose frontmatter times don't overflow.
            def _short_time(value: str) -> str:
                value = re.sub(r"\s*\([^)]*\)", "", value)
                value = value.split("/")[0]
                return value.strip()

            detail_parts = []
            if r["prep_time"]:
                detail_parts.append(f'{_short_time(r["prep_time"])} prep')
            if r["cook_time"]:
                detail_parts.append(f'{_short_time(r["cook_time"])} cook')
            detail = " · ".join(detail_parts)

            course = r["course"]
            if course and course != "other":
                badge = (
                    f'<span class="course-badge course-{course}">'
                    f'{course.title()}</span>'
                )
            else:
                badge = ""

            entries += (
                f'  <a class="toc-entry" href="recipes/{r["slug"]}/">'
                f'<span class="toc-entry__title">{r["title"]}</span>'
                f'<span class="toc-entry__dots"></span>'
                f'{badge}'
                f'<span class="toc-entry__detail">{detail}</span>'
                f'</a>\n'
            )

        chapters += (
            f'<div class="toc-chapter">\n'
            f'  <h2 class="toc-chapter__heading">'
            f'<span class="toc-chapter__number">Chapter {i}</span>'
            f'{author}</h2>\n'
            f'{entries}'
            f'</div>\n\n'
        )

    index_md = f"""\
---
hide:
  - navigation
  - toc
---

<div class="cookbook-hero">
  <h1>Wahly a Ojo</h1>
  <p>A family cookbook. Recipes cooked <em>a ojo</em>.</p>
</div>

<div class="toc-book">
{chapters}</div>
"""

    # index.md is generated (and gitignored). Only touch it when it changes so
    # `mkdocs serve` doesn't see a fresh write on every rebuild.
    index_path = docs_dir / "index.md"
    if not index_path.exists() or index_path.read_text(encoding="utf-8") != index_md:
        index_path.write_text(index_md, encoding="utf-8")


def _is_filler(meta: dict) -> bool:
    return str(meta.get("gallery") or "").lower().strip() == "filler"


def _wrap_opinions(markdown: str, filler: bool = False) -> str:
    """Turn `**Name:** comment` dialogue into speaker-tagged blocks.

    A comment starts at a `**Name:**` line and runs until the next one (or the
    next heading), so it can span several paragraphs and include photos. The
    blocks use `markdown="1"` (md_in_html) so their contents are still parsed
    as Markdown.
    """
    out: list[str] = []
    in_section = False
    comment: list[str] | None = None  # lines of the comment being collected
    speaker = ""
    any_open = False

    def flush():
        nonlocal comment
        if comment is None:
            return
        body = "".join(comment).strip()
        name = html.escape(speaker, quote=True)
        hue = zlib.crc32(speaker.lower().encode("utf-8")) % 360
        out.append(
            f'<div class="opinion" data-speaker="{name}" '
            f'style="--speaker-hue: {hue}" markdown="1">\n'
            f'<span class="opinion__name">{name}</span>\n\n'
            f"{body}\n\n"
            "</div>\n"
        )
        comment = None

    def close():
        nonlocal any_open
        flush()
        if any_open:
            out.append("</div>\n\n")
            any_open = False

    in_fence = False
    for line in markdown.splitlines(keepends=True):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_fence = not in_fence

        if not in_fence and re.match(r"#{1,6} ", stripped):
            close()
            in_section = stripped == "## Peanut Gallery"
            out.append(line)
            if in_section and filler:
                out.append("\n" + _FILLER_NOTE)
            continue

        match = _OPINION_RE.match(stripped) if in_section and not in_fence else None
        if match:
            flush()
            if not any_open:
                out.append('\n<div class="opinions" markdown="1">\n')
                any_open = True
            speaker = match.group(1).strip()
            comment = [match.group(2) + "\n"]
            continue

        if comment is not None:
            comment.append(line)
        else:
            out.append(line)

    close()
    return "".join(out)


def _more_from(author: str, current_slug: str) -> str:
    """Links to the author's other recipes. Empty if this is their only one."""
    others = [r for r in _BY_AUTHOR.get(author, []) if r["slug"] != current_slug]
    if not others:
        return ""

    entries = ""
    for r in others:
        course = r["course"]
        badge = (
            f'<span class="course-badge course-{course}">{course.title()}</span>'
            if course and course != "other"
            else ""
        )
        entries += (
            f'<a class="more-from__entry" href="../{r["slug"]}/">'
            f'<span class="more-from__title">{r["title"]}</span>'
            f"{badge}</a>"
        )

    return (
        f'\n<div class="more-from">'
        f'<h2 class="more-from__heading">More from {author}</h2>'
        f"{entries}</div>\n"
    )


def on_page_markdown(markdown, page, config, files, **kwargs):
    """Inject a metadata block and back-link at the top of every recipe page."""
    if not page.file.src_path.startswith("recipes/"):
        return markdown

    meta = page.meta or {}

    markdown = _wrap_opinions(markdown, filler=_is_filler(meta))

    items = []
    if meta.get("author"):
        items.append(f'<span class="meta-author">By {meta["author"]}</span>')
    if meta.get("course"):
        c = meta["course"].lower()
        items.append(
            f'<span class="meta-item course-badge course-{c}">{c.title()}</span>'
        )
    if meta.get("servings"):
        items.append(f'<span class="meta-item">Yield: {meta["servings"]}</span>')
    if meta.get("prep_time"):
        items.append(f'<span class="meta-item">Prep: {meta["prep_time"]}</span>')
    if meta.get("cook_time"):
        items.append(f'<span class="meta-item">Cook: {meta["cook_time"]}</span>')

    meta_block = (
        '\n<div class="recipe-meta">\n'
        '  <a href="../../" class="back-link">&larr; All Recipes</a>\n'
        f'  <div class="meta-items">{"".join(items)}</div>\n'
        "</div>\n\n"
    )

    # Insert immediately after the first `# Heading` line
    lines = markdown.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines.insert(i + 1, meta_block)
            break

    slug = pathlib.Path(page.file.src_path).stem
    return "".join(lines) + _more_from(meta.get("author") or "", slug)
