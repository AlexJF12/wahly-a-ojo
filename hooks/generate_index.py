"""
MkDocs hooks for Wahly a Ojo.

on_pre_build  — regenerate docs/index.md from the current recipe collection.
on_page_markdown — inject a metadata block and back-link into each recipe page,
                   and mark up the Peanut Gallery dialogue.
"""

import pathlib
import re
import yaml

_OPINION_RE = re.compile(r"^\*\*(Nate|Alex|Ben|Tim|Carolyn):\*\*\s*(.+)$")

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

    (docs_dir / "index.md").write_text(index_md, encoding="utf-8")


def _wrap_opinions(markdown: str) -> str:
    """Turn `**Name:** line` dialogue into speaker-tagged HTML.

    Emitted as one contiguous raw-HTML block (no blank lines inside) so the
    Markdown parser passes it through untouched.
    """
    lines = markdown.splitlines(keepends=True)
    out: list[str] = []
    in_section = False
    open_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            if open_block:
                out.append("</div>\n\n")
                open_block = False
            in_section = stripped == "## Peanut Gallery"
            out.append(line)
            continue

        match = _OPINION_RE.match(stripped) if in_section else None
        if match:
            if not open_block:
                out.append('\n<div class="opinions">')
                open_block = True
            speaker, text = match.groups()
            out.append(
                f'<p class="opinion" data-speaker="{speaker}">'
                f'<span class="opinion__name">{speaker}</span>{text}</p>'
            )
            continue

        if open_block and not stripped:
            continue

        if open_block:
            out.append("</div>\n\n")
            open_block = False
        out.append(line)

    if open_block:
        out.append("</div>\n")

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

    markdown = _wrap_opinions(markdown)

    meta = page.meta or {}

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
