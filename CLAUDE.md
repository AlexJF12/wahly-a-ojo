# CLAUDE.md

Guidance for Claude Code when working in this repo.

## Project

A recipe collection rendered to a website (MkDocs Material) and PDF. Recipes live in
`docs/recipes/` as Markdown with YAML frontmatter (`title`, `author`, `course`,
`servings`, `cook_time`) and per-recipe images in `docs/images/<recipe>/`.

## Writing recipes

**When writing or editing any recipe, follow [STYLE_GUIDE.md](STYLE_GUIDE.md).** Key rules:

- **Recipe:** max 5 steps; casual tone; lean on smell, sight, and touch as cues.
- **Unsolicited Opinions:** a 2–4 person conversation, snarky and funny, with suggestions
  that genuinely improve the dish. Cast is Nate, Alex, Ben, Tim, and Carolyn — **the
  recipe's author must NOT appear in this section.**

Match the structure of existing recipes (e.g. `docs/recipes/larb.md`): frontmatter, `#`
title, hero image, intro line, `## Ingredients`, `## Instructions`, `## Unsolicited Opinions`.
