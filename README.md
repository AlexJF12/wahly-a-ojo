# wahly-a-ojo

A family cookbook, built as a static website with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

## What's here

- `docs/recipes/` — one Markdown file per recipe, with YAML frontmatter
- `docs/images/<recipe>/` — photos for each recipe
- `hooks/generate_index.py` — builds the homepage and styles the Peanut Gallery comments
- `STYLE_GUIDE.md` — how recipes and comments are written

## Running it

```bash
pip install -r requirements.txt
mkdocs serve    # preview at http://127.0.0.1:8000
```

Pushing to `main` deploys the site to GitHub Pages.

## Adding a recipe

Copy an existing file in `docs/recipes/` (for example `larb.md`), change the frontmatter and the content, and put its photos in `docs/images/<recipe>/`. The homepage (`docs/index.md`) is regenerated on every build, so there's nothing else to update.

## Adding comments

Each recipe ends with a `## Peanut Gallery` section. A comment is a bold name, a colon, and the text:

```markdown
**Carolyn:** I was wrong about the cinnamon.
```

Recipes with `gallery: "filler"` in their frontmatter still have placeholder comments. Replace them with real ones, then delete that line. `mkdocs build` prints the list of recipes that are still filler. See [STYLE_GUIDE.md](STYLE_GUIDE.md) for the details.

## PDF

There is no separate PDF renderer. Open a recipe in the browser and print it to PDF; the print styles drop the navigation links.

## Project name

"A ojo" is a Spanish cooking expression meaning to cook by sight — no strict measurements, no timers. The cook uses their eyes and judgment to decide how much seasoning to add or how long something needs on the heat. Recipes here are guides, not rules.
