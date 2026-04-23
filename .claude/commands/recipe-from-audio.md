# recipe-from-audio

Transcribe an audio recording of someone describing a recipe and write a
formatted recipe Markdown file in the cookbook style.

## Usage

```
/recipe-from-audio <path-to-audio-file> [--author "Name"]
```

**Supported formats:** `.mp3`, `.m4a`, `.wav`, `.webm`

## What it does

1. Reads the audio file and sends it to Claude with a prompt to transcribe
   and format the recipe.
2. Writes `docs/recipes/<slug>.md` with proper YAML frontmatter, `## Ingredients`,
   `## Instructions`, and an optional `## Notes` section.
3. Prints the output path and next steps (add a hero image, validate).

## Steps

Run the transcription script, then validate the result:

```bash
python scripts/transcribe-recipe.py $ARGUMENTS
python scripts/validate-recipes.py docs/recipes/<slug>.md
```

After running, show the user the saved file path and remind them to:
- Review and edit the generated recipe for accuracy
- Add a hero image at `docs/images/<slug>/hero.jpg`
- Run the validator if they haven't already

If the script fails (missing `anthropic` package, unsupported format, no
`ANTHROPIC_API_KEY`), explain the error clearly and tell the user what to fix.
