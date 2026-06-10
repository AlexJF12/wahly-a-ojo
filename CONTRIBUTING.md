# Contributing to Wahly a Ojo

Everyone is welcome to add a recipe. Here's the full process.

---

## Adding a recipe from a voice recording

If it's easier to talk through a recipe than to write it out, drop an audio
file in a local `audio/` folder at the repo root (it's gitignored — recordings
never get committed) and run:

```
/recipe-from-audio audio/my-recording.m4a --author "Your Name"
```

This transcribes the recording and writes a formatted recipe to
`docs/recipes/<slug>.md`. From there, jump to [Add photos](#2-add-photos) and
[Open a pull request](#3-open-a-pull-request) below — review the generated
text first, since transcription isn't perfect.

---

## Adding a recipe

### 1. Write your recipe

Create a new file in `docs/recipes/` named after your recipe using lowercase words and hyphens:

```
docs/recipes/my-recipe-name.md
```

Copy the template below and fill it in:

```markdown
---
title: "Your Recipe Title"
author: "Your Name"
course: "entree"
servings: "4 servings"
prep_time: "20 min"
cook_time: "30 min"
---

# Your Recipe Title

![Description of the photo](../images/my-recipe-name/hero.jpg)

## Ingredients

- Ingredient one
- Ingredient two
- Ingredient three

## Instructions

1. First step.
2. Second step.
3. Third step.

## Notes

Optional extra context, tips, or variations.
```

### Frontmatter fields

| Field       | Required   | Description |
|-------------|------------|-------------|
| `title`     | Yes        | Recipe name |
| `author`    | Yes        | Your display name |
| `course`    | Yes        | See allowed values below |
| `servings`  | Encouraged | Yield (e.g. `"4 servings"`, `"2 loaves"`, `"12 cookies"`) |
| `prep_time` | Optional   | Active prep time (e.g. `"20 min"`) |
| `cook_time` | Optional   | Cooking/baking time (e.g. `"45 min"`) |

### Family commentary (optional)

Want to add a sibling's two cents? Add a `commentary` list to the
frontmatter — it renders as a "Family notes" sidebar next to the recipe:

```yaml
commentary:
  - author: "Alex"
    text: "I always double the garlic. Don't @ me."
  - author: "Ceci"
    text: "Agreed, but go easy on the salt if you're using canned beans."
```

Each entry needs an `author` and a `text`. Keep it short — these are quick
asides, not a second set of instructions. Markdown (like *emphasis* or
**bold**) works in `text`.

### Allowed `course` values

| Value       | What it covers |
|-------------|----------------|
| `appetizer` | Starters, snacks, dips, small plates |
| `bread`     | Breads, rolls, flatbreads, pizza dough |
| `breakfast` | Morning meals, brunch |
| `dessert`   | Sweets, pastries, cakes, ice cream |
| `drink`     | Cocktails, smoothies, hot drinks |
| `entree`    | Main dishes |
| `side`      | Side dishes, salads, vegetables |
| `soup`      | Soups, stews, chili |
| `other`     | Sauces, condiments, preserves, anything that doesn't fit |

---

### 2. Add photos

Create a folder inside `docs/images/` that matches your recipe filename (without `.md`):

```
docs/images/my-recipe-name/
  hero.jpg          ← main photo — this is what appears on the card grid
  step-2.jpg        ← optional additional shots (1–3 total recommended)
```

Reference images in your recipe using a path relative to the recipe file:

```markdown
![A description of the photo](../images/my-recipe-name/hero.jpg)
```

**Photo guidelines:**

- JPEG format preferred, PNG acceptable for graphics
- Max 2 MB per image — CI will warn you if an image is oversized
- Resize with [ImageMagick](https://imagemagick.org) if needed:

```bash
magick input.jpg -resize "1600x1600>" -quality 85 output.jpg
```

---

### 3. Open a pull request

Push your branch and open a PR. CI will automatically validate:

- Required frontmatter fields (`title`, `author`, `course`)
- Valid `course` value
- `## Ingredients` and `## Instructions` sections with content below them
- All image paths resolve to files that exist in the repo

The checks print clear messages explaining exactly what to fix. Once they pass, request a review.

---

### 4. After merge

Once your PR merges to `main`, the site rebuilds automatically (usually within a minute or two) and your recipe appears on the homepage card grid.

---

## Preview the site locally

```bash
pip install -r requirements.txt
mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The site hot-reloads as you save files.

---

## Generate the PDF locally

```bash
pip install -r requirements-pdf.txt
python scripts/build-pdf.py
```

The PDF is written to `output/cookbook.pdf`. You can also trigger PDF generation from the **Actions** tab on GitHub (select **Build PDF Cookbook** → **Run workflow**).
