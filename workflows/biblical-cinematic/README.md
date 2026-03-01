# Biblical Cinematic Video Workflow

Generates professional 12–20 minute biblical cinematic videos from KJV scripture text.
A web app handles text cleaning and review, then automatically triggers the n8n pipeline.

**Current version: v6.0.2** (stable, production confirmed working)

---

## How It Works

```
Browser (http://localhost:8000)
  → Paste scripture → Convert & Clean
  → Review cleaned text → Approve & Generate Video
  → FastAPI server POSTs to n8n webhook
      → Perplexity AI (sonar-pro)    → 20 cinematic scenes
      → ElevenLabs                   → narration audio
      → JSON2Video (Ken Burns)       → HD video render
  → Final MP4 ready in 8–13 minutes
```

**Cost per video:** ~$1.27 — Perplexity $0.15 + ElevenLabs $0.50–$2.50 + JSON2Video $1.00

---

## Quick Start

### 1. Set your n8n webhook URL in `.env` (workspace root)

```
N8N_WEBHOOK_URL=https://your-n8n-instance.app.n8n.cloud/webhook/your-path
```

### 2. Start the web server

```bash
cd workflows/biblical-cinematic/server
pip install -r requirements.txt   # first time only
python app.py
```

### 3. Open the web app

Go to **http://localhost:8000** — paste scripture, convert, approve.

---

## n8n Workflow Setup (one-time)

If setting up from scratch or on a new n8n instance:

1. Import `n8n/Biblical-Video-Workflow-v6.0.2.json` into n8n
2. Import `templates/JSON2Video-Template-FIXED.json` into JSON2Video → copy the Template ID
3. In the workflow, configure credentials:
   - **Perplexity AI node**: `Bearer YOUR_PERPLEXITY_API_KEY`
   - **ElevenLabs node**: your ElevenLabs API key
   - **JSON2Video node**: your JSON2Video API key + Template ID
4. Replace the **Manual Trigger** node with a **Webhook** node:
   - HTTP Method: POST
   - Respond: Immediately
   - Connect it to **"Bible Chapter Text Input"**
5. In **"Bible Chapter Text Input"** Set node, set the value to: `{{ $json.body.text }}`
6. **Save** the workflow and toggle it to **Published/Active**
7. Copy the **Production URL** → paste into `.env` as `N8N_WEBHOOK_URL`

---

## Prerequisites

- **n8n** — cloud ($20/mo) or self-hosted (free): https://n8n.io
- **Perplexity AI** API key: https://perplexity.ai
- **ElevenLabs** API key: https://elevenlabs.io
- **JSON2Video** API key: https://json2video.com
- **Python 3.7+**

---

## ElevenLabs Voice IDs

| Voice | ID | Style |
|---|---|---|
| Young Jamal *(default)* | `6OzrBCQf8cjERkYgzSg8` | Young, clear narration |
| Tommy Israel *(personal)* | `T4sLxEj9xEGMREO21ACw` | Personal voice |
| William J | `C8OtYB0OTgD7K0YWkg7y` | Professional |
| Hakeem | `nJvj5shg2xu1GKGxqfkE` | African American, deep |
| Lamar Lincoln | `CVRACyqNcQefTlxMj9b` | Black narrator |

---

## Folder Structure

```
biblical-cinematic/
├── README.md                              ← this file
├── server/
│   ├── app.py                             ← FastAPI web server (run this)
│   └── requirements.txt                   ← pip install -r requirements.txt
├── text_processor/
│   ├── biblical_text_processor_v2.py      ← imported by server; also runnable standalone
│   ├── Input                              ← paste KJV text here (standalone use)
│   └── Output                             ← cleaned text (standalone use)
├── n8n/
│   └── Biblical-Video-Workflow-v6.0.2.json ← import into n8n
├── templates/
│   └── JSON2Video-Template-FIXED.json     ← import into JSON2Video
├── ui/                                    ← original React frontend (unused, replaced by server/)
└── archive/
    └── releases/                          ← v1.0 through v6.0.1 history
```

---

## Troubleshooting

**Workflow not triggering:**
- Make sure the n8n workflow is **Published** (green badge, top-right of workflow editor)
- Check `N8N_WEBHOOK_URL` uses `/webhook/` not `/webhook-test/`
- Test directly: `python -c "import httpx; r=httpx.post('YOUR_URL', json={'text':'test'}); print(r.status_code, r.text)"`

**Server not reading `.env`:**
- The server uses `find_dotenv()` which walks up from `server/` to find `.env` at workspace root
- If stale server processes are running on port 8000, kill them: `python -c "import subprocess; subprocess.run(['taskkill', '/F', '/PID', '<pid>'], shell=True)"`

**Text processor errors:**
- The server imports `biblical_text_processor_v2.py` directly from `text_processor/`
- Can also run standalone: paste into `Input` file, run `python biblical_text_processor_v2.py`, read `Output`
