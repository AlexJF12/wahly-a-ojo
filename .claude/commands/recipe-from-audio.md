# recipe-from-audio

Transcribe an audio recording of someone describing a recipe and write a
formatted recipe Markdown file in the cookbook style.

## Usage

```
/recipe-from-audio <path-to-audio-file> [--author "Name"] [--model base]
```

**Supported formats:** `.mp3`, `.m4a`, `.wav`, `.webm`, `.ogg`, `.flac`

**Whisper model sizes** (tradeoff: speed vs. accuracy):
- `tiny` / `base` — fast, good enough for clear recordings
- `small` / `medium` — better for accents or background noise
- `large` — most accurate, slowest

## What it does

1. **Whisper** transcribes the audio locally (no API call for this step).
2. **Claude** (`claude-opus-4-7`) reads the transcript and formats it as a
   cookbook recipe — natural voice, YAML frontmatter, `## Ingredients`,
   `## Instructions`, optional `## Notes`.
3. Saves to `docs/recipes/<slug>.md` and prints next steps.

`uv` manages the Python environment automatically — no manual venv setup needed.

## Steps

```bash
uv run scripts/transcribe-recipe.py $ARGUMENTS
```

After running, show the user:
- The saved file path
- A reminder to review/edit the recipe for accuracy
- A reminder to add a hero image at `docs/images/<slug>/hero.jpg`
- The validate command: `uv run scripts/validate-recipes.py docs/recipes/<slug>.md`

If the script fails, explain the error:
- Missing `ANTHROPIC_API_KEY` → set the env var
- Whisper model download fails → check internet connection
- Unsupported file format → convert with ffmpeg first
