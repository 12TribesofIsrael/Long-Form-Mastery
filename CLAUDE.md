# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AI Movie — a personal workspace for building AI-generated video systems. Contains two workflows:

| Workflow | Location | Description |
|---|---|---|
| **General AI Movie** | root (`app.py`, `pipeline.py`, `src/`) | Python/Gradio pipeline: text prompt → images → video clips → narrated movie via fal.ai + OpenAI |
| **Biblical Cinematic** | `workflows/biblical-cinematic/` | Full-stack web app + n8n: paste KJV scripture → clean → review → approve → auto-generates 12–20 min cinematic video |

---

## Workflow 1: General AI Movie Pipeline

### Stack
- Python 3.11+, **Gradio** (UI), **OpenAI** (GPT-4o + TTS), **fal.ai** (FLUX + Kling), **FFmpeg**

### Pipeline
```
Script text
  → GPT-4o          parse into Scene objects     (src/features/script_parser/)
  → FLUX/fal.ai     generate image per scene     (src/features/image_gen/)
  → Kling/fal.ai    animate image to video clip  (src/features/video_gen/)
  → OpenAI TTS      generate narration audio     (src/features/audio_gen/)
  → FFmpeg          assemble final movie.mp4     (src/features/assembler/)
```

Each run saves to `output/<run-id>/`.

### Setup
```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # fill in OPENAI_API_KEY and FAL_KEY
# Also install FFmpeg and add to PATH: https://ffmpeg.org/download.html
```

### Commands
```bash
python app.py                          # Gradio UI at http://localhost:7860
python pipeline.py path/to/script.txt  # CLI mode
pytest tests/
```

### Key Files
| File | Purpose |
|---|---|
| [app.py](app.py) | Gradio UI entry point |
| [pipeline.py](pipeline.py) | Full pipeline orchestrator |
| [src/features/script_parser/models.py](src/features/script_parser/models.py) | `Scene` + `Script` dataclasses |
| [src/features/script_parser/parser.py](src/features/script_parser/parser.py) | GPT-4o scene breakdown |
| [src/features/image_gen/generator.py](src/features/image_gen/generator.py) | FLUX image generation |
| [src/features/video_gen/generator.py](src/features/video_gen/generator.py) | Kling image-to-video |
| [src/features/audio_gen/generator.py](src/features/audio_gen/generator.py) | OpenAI TTS narration |
| [src/features/assembler/assembler.py](src/features/assembler/assembler.py) | FFmpeg stitching |
| [src/shared/config.py](src/shared/config.py) | Settings from `.env` |

---

## Workflow 2: Biblical Cinematic (Web App + n8n)

### Stack
- **FastAPI** (web server + API), **Python** (text processing), **n8n** (video pipeline orchestration)
- **Perplexity AI** (scene gen), **ElevenLabs** (voice), **JSON2Video** (rendering)

### Full Pipeline
```
Browser (http://localhost:8000)
  → POST /api/clean    FastAPI server runs text processor → returns cleaned sections
  → POST /api/generate FastAPI POSTs to n8n webhook
      → n8n workflow:
          → Perplexity sonar-pro    → 20 cinematic scene descriptions
          → ElevenLabs              → narration audio (214 WPM)
          → JSON2Video (Ken Burns)  → renders 20-scene HD video
  → Final MP4 (12–20 min)
```

**Cost:** ~$1.27/video | **Time:** 8–13 min | **Version:** v6.0.2

### Start the web app
```bash
cd workflows/biblical-cinematic/server
pip install -r requirements.txt   # first time only
python app.py
# Opens at http://localhost:8000
```

### How to use
1. Go to **http://localhost:8000**
2. Paste KJV scripture → **Convert & Clean**
3. Review/edit the cleaned text → **Approve & Generate Video**
4. n8n workflow fires automatically → check JSON2Video dashboard in 8–13 min

### n8n setup notes
- The n8n workflow must be **Published/Active** for the production webhook to fire
- The `Bible Chapter Text Input` Set node must have `{{ $json.body.text }}` as its value
- Kill stale server processes on Windows with: `python -c "import subprocess; subprocess.run(['taskkill', '/F', '/PID', '<pid>'], shell=True)"`
- `find_dotenv()` is used (not manual path) to locate `.env` — reliable across uvicorn reload workers

### Key Files
| File | Purpose |
|---|---|
| [workflows/biblical-cinematic/README.md](workflows/biblical-cinematic/README.md) | Complete setup guide |
| [workflows/biblical-cinematic/server/app.py](workflows/biblical-cinematic/server/app.py) | FastAPI server — landing page + `/api/clean` + `/api/generate` |
| [workflows/biblical-cinematic/server/requirements.txt](workflows/biblical-cinematic/server/requirements.txt) | Server dependencies |
| [workflows/biblical-cinematic/text_processor/biblical_text_processor_v2.py](workflows/biblical-cinematic/text_processor/biblical_text_processor_v2.py) | KJV text cleaner/splitter (imported by server) |
| [workflows/biblical-cinematic/n8n/Biblical-Video-Workflow-v6.0.2.json](workflows/biblical-cinematic/n8n/Biblical-Video-Workflow-v6.0.2.json) | Import into n8n |
| [workflows/biblical-cinematic/templates/JSON2Video-Template-FIXED.json](workflows/biblical-cinematic/templates/JSON2Video-Template-FIXED.json) | Import into JSON2Video |

---

## Environment Variables

See [.env.example](.env.example) for all keys. The `.env` file lives at the workspace root.

| Variable | Used By |
|---|---|
| `OPENAI_API_KEY` | General pipeline (GPT-4o + TTS) |
| `FAL_KEY` | General pipeline (FLUX + Kling) |
| `N8N_WEBHOOK_URL` | Biblical web app → triggers n8n workflow |
| `PERPLEXITY_API_KEY` | Reference only (configured inside n8n) |
| `ELEVENLABS_API_KEY` | Reference only (configured inside n8n) |
| `JSON2VIDEO_API_KEY` | Reference only (configured inside n8n) |

The biblical server uses `find_dotenv()` to locate `.env` by walking up the directory tree from `server/app.py`.
