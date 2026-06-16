"""
MkDocs hooks for Wahly a Ojo.

on_pre_build  — regenerate docs/index.md from the current recipe collection.
on_page_markdown — inject a metadata block and back-link into each recipe page.
"""

import pathlib
import re
import yaml


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
    """Regenerate docs/index.md with the full recipe card grid."""
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

    # Recipe cards
    cards = ""
    for r in recipes:
        time_parts = []
        if r["prep_time"]:
            time_parts.append(f"{r['prep_time']} prep")
        if r["cook_time"]:
            time_parts.append(f"{r['cook_time']} cook")
        time_html = (
            f'<p class="recipe-card__time">{" &middot; ".join(time_parts)}</p>'
            if time_parts else ""
        )

        img_html = (
            f'<img src="{r["hero"]}" alt="{r["title"]}" loading="lazy">'
            if r["hero"]
            else '<div class="recipe-card__no-image"></div>'
        )

        cards += f"""\
<a class="recipe-card" href="recipes/{r['slug']}/" data-course="{r['course']}">
  <div class="recipe-card__image">{img_html}</div>
  <div class="recipe-card__body">
    <div class="recipe-card__top">
      <span class="course-badge course-{r['course']}">{r['course'].title()}</span>
    </div>
    <h3 class="recipe-card__title">{r['title']}</h3>
    <p class="recipe-card__author">By {r['author']}</p>
    {time_html}
  </div>
</a>
"""

    index_md = f"""\
---
hide:
  - navigation
  - toc
---

<div class="cookbook-hero">
  <h1>Wahly a Ojo</h1>
  <p>A community cookbook. Recipes cooked <em>a ojo</em>&thinsp;&mdash;&thinsp;by sight, by feel, by taste.</p>
</div>

<div class="recipe-grid" id="recipe-grid">
{cards}</div>
"""

    (docs_dir / "index.md").write_text(index_md, encoding="utf-8")


def on_page_markdown(markdown, page, config, files, **kwargs):
    """Inject a metadata block and back-link at the top of every recipe page."""
    if not page.file.src_path.startswith("recipes/"):
        return markdown

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
        '  <a href="../" class="back-link">&larr; All Recipes</a>\n'
        f'  <div class="meta-items">{"".join(items)}</div>\n'
        "</div>\n\n"
    )

    # Insert immediately after the first `# Heading` line
    lines = markdown.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines.insert(i + 1, meta_block)
            break

    return "".join(lines)
