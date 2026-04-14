#!/usr/bin/env python3
"""
Build the Wahly a Ojo community cookbook PDF.

Usage:
    python scripts/build-pdf.py

Output:
    output/cookbook.pdf
"""

import pathlib
import re
import sys

import markdown
import yaml
from weasyprint import HTML

ROOT_DIR     = pathlib.Path(__file__).resolve().parent.parent
DOCS_DIR     = ROOT_DIR / "docs"
RECIPES_DIR  = DOCS_DIR / "recipes"
ASSETS_DIR   = ROOT_DIR / "assets"
TEMPLATES_DIR = ROOT_DIR / "templates" / "pdf"
OUTPUT_DIR   = ROOT_DIR / "output"

COURSE_ORDER = [
    "appetizer", "bread", "breakfast", "dessert",
    "drink", "entree", "side", "soup", "other",
]

COURSE_LABELS = {
    "appetizer": "Appetizers",
    "bread":     "Breads",
    "breakfast": "Breakfast",
    "dessert":   "Desserts",
    "drink":     "Drinks",
    "entree":    "Entrées",
    "side":      "Sides",
    "soup":      "Soups & Stews",
    "other":     "Other",
}

MD = markdown.Markdown(extensions=["tables", "fenced_code"])


def parse_recipe(path: pathlib.Path) -> dict | None:
    content = path.read_text(encoding="utf-8")
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm:
        print(f"[warn] No frontmatter: {path.name}", file=sys.stderr)
        return None
    try:
        meta = yaml.safe_load(fm.group(1))
    except yaml.YAMLError as exc:
        print(f"[warn] Bad YAML in {path.name}: {exc}", file=sys.stderr)
        return None
    if not isinstance(meta, dict):
        return None

    body = content[fm.end():]

    # Convert Markdown body to HTML
    MD.reset()
    body_html = MD.convert(body)

    return {
        "slug":      path.stem,
        "title":     meta.get("title") or path.stem,
        "author":    meta.get("author") or "",
        "course":    (meta.get("course") or "other").lower().strip(),
        "servings":  meta.get("servings") or "",
        "prep_time": meta.get("prep_time") or "",
        "cook_time": meta.get("cook_time") or "",
        "body_html": body_html,
    }


def build_html(recipes: list[dict]) -> str:
    # Group recipes by course, preserving COURSE_ORDER
    grouped: dict[str, list] = {}
    for course in COURSE_ORDER:
        matching = [r for r in recipes if r["course"] == course]
        if matching:
            grouped[course] = matching
    # Recipes with unrecognised course fall into "other"
    for r in recipes:
        if r["course"] not in COURSE_ORDER:
            grouped.setdefault("other", []).append(r)

    # ── Cover page ───────────────────────────────────────────
    cover_src = (ASSETS_DIR / "cover.jpg").as_uri()
    cover_template = (TEMPLATES_DIR / "cover.html").read_text(encoding="utf-8")
    cover_html = cover_template.replace("{cover_image_src}", cover_src)

    # ── Table of contents ────────────────────────────────────
    toc_items = ""
    for course, course_recipes in grouped.items():
        label = COURSE_LABELS.get(course, course.title())
        toc_items += (
            f'<li class="toc-section">'
            f'<a href="#section-{course}">{label}</a></li>\n'
        )
        for r in course_recipes:
            toc_items += (
                f'<li class="toc-entry">'
                f'<a href="#recipe-{r["slug"]}">{r["title"]}</a></li>\n'
            )

    toc_html = f"""
<div class="toc-page">
  <h1>Table of Contents</h1>
  <ul class="toc">
    {toc_items}
  </ul>
</div>"""

    # ── Recipe sections ──────────────────────────────────────
    sections_html = ""
    for course, course_recipes in grouped.items():
        label = COURSE_LABELS.get(course, course.title())
        sections_html += f"""
<div class="section-divider" id="section-{course}">
  <h1 class="section-title">{label}</h1>
</div>"""

        for r in course_recipes:
            meta_parts = []
            if r["author"]:    meta_parts.append(f"By {r['author']}")
            if r["servings"]:  meta_parts.append(f"Yield: {r['servings']}")
            if r["prep_time"]: meta_parts.append(f"Prep: {r['prep_time']}")
            if r["cook_time"]: meta_parts.append(f"Cook: {r['cook_time']}")

            meta_html = ""
            if meta_parts:
                items_html = "".join(
                    f'<span class="pdf-meta-item">{p}</span>' for p in meta_parts
                )
                meta_html = f'<div class="pdf-meta">{items_html}</div>'

            sections_html += f"""
<article class="recipe-page" id="recipe-{r['slug']}">
  {meta_html}
  {r['body_html']}
</article>"""

    # ── CSS ──────────────────────────────────────────────────
    css = (TEMPLATES_DIR / "style.css").read_text(encoding="utf-8")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Wahly a Ojo Cookbook</title>
  <style>{css}</style>
</head>
<body>
  {cover_html}
  {toc_html}
  {sections_html}
</body>
</html>"""


def main() -> None:
    recipe_files = sorted(RECIPES_DIR.glob("*.md"))
    if not recipe_files:
        print("No recipes found in docs/recipes/", file=sys.stderr)
        sys.exit(1)

    recipes = [r for f in recipe_files if (r := parse_recipe(f))]
    print(f"Building PDF from {len(recipes)} recipe(s)…")

    html = build_html(recipes)

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "cookbook.pdf"

    # base_url set to docs/recipes/ so ../images/… paths resolve correctly
    base_url = (DOCS_DIR / "recipes" / "").as_uri()
    HTML(string=html, base_url=base_url).write_pdf(str(output_path))

    print(f"PDF written to {output_path}")


if __name__ == "__main__":
    main()
