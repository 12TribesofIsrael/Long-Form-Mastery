# AI Movie

A personal workspace for building AI-generated video systems. Contains two independent workflows for generating cinematic videos from text.

---

## Workflows

### 1. Biblical Cinematic (Production — Working)

Paste KJV scripture into a web app and automatically generate a 12–20 minute cinematic video with narration, Ken Burns effects, and professional audio.

**Stack:** FastAPI · n8n · Perplexity AI · ElevenLabs · JSON2Video

**Cost:** ~$1.27/video | **Time:** 8–13 min

```bash
cd workflows/biblical-cinematic/server
pip install -r requirements.txt   # first time only
python app.py
# Open http://localhost:8000
```

1. Paste KJV scripture → **Convert & Clean**
2. Review the cleaned text → **Approve & Generate Video**
3. Check your JSON2Video dashboard in 8–13 minutes

See [workflows/biblical-cinematic/README.md](workflows/biblical-cinematic/README.md) for full setup including n8n configuration.

---

### 2. General AI Movie Pipeline

Generate a narrated movie from any script or text prompt using AI image generation, video animation, and text-to-speech.

**Stack:** Python · Gradio · OpenAI GPT-4o + TTS · fal.ai (FLUX + Kling) · FFmpeg

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # add OPENAI_API_KEY and FAL_KEY
python app.py
# Open http://localhost:7860
```

**Pipeline:**
```
Script text → GPT-4o (scenes) → FLUX (images) → Kling (video clips) → TTS (narration) → FFmpeg (final .mp4)
```

---

## Setup

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

| Variable | Required For |
|---|---|
| `OPENAI_API_KEY` | General pipeline |
| `FAL_KEY` | General pipeline |
| `N8N_WEBHOOK_URL` | Biblical Cinematic |

Perplexity, ElevenLabs, and JSON2Video keys are configured inside n8n — not in `.env`.

---

## Project Structure

```
AI Movie/
├── app.py                          # General pipeline — Gradio UI
├── pipeline.py                     # General pipeline — orchestrator
├── src/features/                   # Script parser, image gen, video gen, audio, assembler
├── workflows/
│   └── biblical-cinematic/
│       ├── server/app.py           # FastAPI web app
│       ├── text_processor/         # KJV text cleaner
│       ├── n8n/                    # n8n workflow (import into n8n)
│       └── templates/              # JSON2Video template
└── output/                         # Generated videos saved here
```
