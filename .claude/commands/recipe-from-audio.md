# recipe-from-audio

Transcribe an audio recording of someone describing a recipe and write a
formatted recipe Markdown file in the cookbook style.

## Usage

```
/recipe-from-audio <path-to-audio-file> [--author "Name"] [--model base] [--tone casual] [--measurements loose] [--language en]
```

**Supported formats:** `.mp3`, `.m4a`, `.wav`, `.webm`, `.ogg`, `.flac`

## Options

### `--tone` (default: `casual`)
Controls the writing style of the formatted recipe.

| Value | Style |
|---|---|
| `casual` | Natural, human voice — direct but not stiff. A little personality is fine. |
| `tight` | Stripped-down. One action per instruction step. No color commentary, no filler. |
| `storytelling` | Warmth and anecdotes. Weaves in memories or context the speaker shared. Short intro prose after the title is encouraged. |

### `--measurements` (default: `loose`)
Controls how quantities are expressed.

| Value | Style |
|---|---|
| `loose` | Approximate and descriptive — "a handful", "until golden", "about 20 minutes". |
| `exact` | Specific amounts when mentioned; vague ones get a reasonable estimate flagged as approximate ("about 1 cup"). |

### `--language` (default: `en`)
ISO 639-1 language code for the output recipe (`en`, `es`, `fr`, `de`, `it`, `pt`, `ja`, `zh`, …).
Whisper uses the same code for transcription, so this also helps it recognize the spoken language.
If the recording is in a different language than the output, Claude will translate as it formats.

### `--model` (default: `base`)
Whisper model size — tradeoff between speed and accuracy.

| Value | When to use |
|---|---|
| `tiny` / `base` | Fast, good for clear recordings |
| `small` / `medium` | Better for accents or background noise |
| `large` | Most accurate, slowest |

## What it does

1. **Whisper** transcribes the audio locally (no API call for this step).
2. **Claude** (`claude-opus-4-7`) reads the transcript and formats it as a
   cookbook recipe using the specified tone, measurement style, and language.
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
