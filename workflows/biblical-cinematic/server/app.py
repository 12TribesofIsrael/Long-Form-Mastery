"""
Biblical Cinematic Generator — Web Server
==========================================
Run:  python app.py
URL:  http://localhost:8000

Endpoints:
  GET  /             → landing page
  POST /api/clean    → clean biblical text, return sections
  POST /api/generate → send approved text to n8n webhook
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv, find_dotenv

# find_dotenv() walks up the directory tree from this file to locate .env
load_dotenv(find_dotenv(), override=True)

# Make the text_processor module importable
sys.path.insert(0, str(Path(__file__).parent.parent / "text_processor"))

import re
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from biblical_text_processor_v2 import (
    clean_text,
    kjv_narration_fix,
    split_into_words,
    create_sections,
    format_section,
)

app = FastAPI(title="Biblical Cinematic Generator")


# ── Request / Response models ─────────────────────────────────────────────────

class CleanRequest(BaseModel):
    text: str


class Section(BaseModel):
    index: int
    text: str
    word_count: int
    estimated_minutes: float
    estimated_scenes: int


class CleanResponse(BaseModel):
    sections: list[Section]
    total_sections: int


class GenerateRequest(BaseModel):
    text: str           # The approved (possibly edited) section text
    section_index: int = 0


class GenerateResponse(BaseModel):
    status: str
    message: str


# ── API Routes ────────────────────────────────────────────────────────────────

@app.post("/api/clean", response_model=CleanResponse)
async def api_clean(req: CleanRequest):
    """Clean and split raw biblical text into video-ready sections."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # Run the same pipeline as the CLI script
    cleaned = clean_text(req.text)
    cleaned = kjv_narration_fix(cleaned)
    words = split_into_words(cleaned)

    if not words:
        raise HTTPException(status_code=400, detail="No text remained after cleaning.")

    raw_sections = create_sections(words)

    sections: list[Section] = []
    for i, section_words in enumerate(raw_sections):
        formatted = format_section(section_words, i + 1)
        word_count = len(section_words)
        sections.append(
            Section(
                index=i,
                text=formatted.strip(),
                word_count=word_count,
                estimated_minutes=round(word_count / 214, 1),
                estimated_scenes=word_count // 40,
            )
        )

    return CleanResponse(sections=sections, total_sections=len(sections))


@app.post("/api/generate", response_model=GenerateResponse)
async def api_generate(req: GenerateRequest):
    """Send approved text to the n8n webhook to trigger video generation."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Approved text cannot be empty.")

    # Re-read from env on every request so .env changes don't require restart
    load_dotenv(find_dotenv(), override=True)
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

    if not N8N_WEBHOOK_URL:
        raise HTTPException(
            status_code=500,
            detail="N8N_WEBHOOK_URL is not set in your .env file. "
                   "Follow the n8n setup instructions in workflows/biblical-cinematic/README.md.",
        )

    payload = {"text": req.text.strip()}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(N8N_WEBHOOK_URL, json=payload)
            resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"n8n webhook returned an error: {e.response.status_code} — {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach n8n webhook: {e}",
        )

    return GenerateResponse(
        status="sent",
        message="Workflow triggered successfully. Your video will be ready in 8–13 minutes. Check your JSON2Video dashboard.",
    )


# ── Landing Page ──────────────────────────────────────────────────────────────

LANDING_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Biblical Cinematic Generator</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    body { font-family: 'Inter', sans-serif; }
    .title-font { font-family: 'Cinzel', serif; }
    .step-panel { transition: all 0.4s ease; }
    textarea { resize: vertical; }
    .spinner {
      border: 3px solid rgba(255,255,255,0.1);
      border-top-color: #f59e0b;
      border-radius: 50%;
      width: 20px; height: 20px;
      animation: spin 0.8s linear infinite;
      display: inline-block;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen">

  <!-- Header -->
  <header class="border-b border-gray-800 px-6 py-5 flex items-center gap-4">
    <div class="text-amber-500 text-2xl">✦</div>
    <div>
      <h1 class="title-font text-xl font-semibold text-amber-400 tracking-wide">Biblical Cinematic Generator</h1>
      <p class="text-xs text-gray-500 mt-0.5">Perplexity AI · ElevenLabs · JSON2Video · n8n</p>
    </div>
    <div class="ml-auto text-xs text-gray-600">v6.0.2 · ~$1.27/video · 8–13 min</div>
  </header>

  <main class="max-w-4xl mx-auto px-6 py-12">

    <!-- Hero -->
    <div class="text-center mb-12">
      <h2 class="title-font text-3xl font-bold text-white mb-3">Transform Scripture into Cinema</h2>
      <p class="text-gray-400 text-base max-w-xl mx-auto">
        Paste your KJV biblical text below. The pipeline will clean it,
        let you review, then automatically generate a professional 12–20 minute cinematic video.
      </p>
    </div>

    <!-- Step indicators -->
    <div class="flex items-center justify-center gap-2 mb-10 text-sm">
      <div id="step-dot-1" class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-full bg-amber-500 text-black font-bold flex items-center justify-center text-xs">1</div>
        <span class="text-amber-400 font-medium">Input</span>
      </div>
      <div class="h-px w-10 bg-gray-700"></div>
      <div id="step-dot-2" class="flex items-center gap-2 opacity-40">
        <div class="w-7 h-7 rounded-full bg-gray-700 text-gray-300 font-bold flex items-center justify-center text-xs">2</div>
        <span class="text-gray-400 font-medium">Review</span>
      </div>
      <div class="h-px w-10 bg-gray-700"></div>
      <div id="step-dot-3" class="flex items-center gap-2 opacity-40">
        <div class="w-7 h-7 rounded-full bg-gray-700 text-gray-300 font-bold flex items-center justify-center text-xs">3</div>
        <span class="text-gray-400 font-medium">Generating</span>
      </div>
    </div>

    <!-- ── STEP 1: Input ── -->
    <div id="step1" class="step-panel">
      <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <label class="block text-sm font-medium text-gray-300 mb-3">
          Biblical Text <span class="text-gray-500 font-normal">(KJV scripture — any length)</span>
        </label>
        <textarea
          id="raw-text"
          rows="14"
          placeholder="Paste your KJV scripture or biblical story here...&#10;&#10;Example: In the beginning God created the heaven and the earth..."
          class="w-full bg-gray-950 border border-gray-700 rounded-xl px-4 py-3 text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
        ></textarea>
        <div class="flex items-center justify-between mt-4">
          <span id="char-count" class="text-xs text-gray-600">0 characters</span>
          <button
            id="convert-btn"
            onclick="convertText()"
            class="bg-amber-500 hover:bg-amber-400 text-black font-semibold px-8 py-3 rounded-xl transition-colors duration-200 flex items-center gap-2"
          >
            <span>Convert &amp; Clean</span>
          </button>
        </div>
        <div id="convert-error" class="mt-3 text-red-400 text-sm hidden"></div>
      </div>
    </div>

    <!-- ── STEP 2: Review ── -->
    <div id="step2" class="step-panel hidden">
      <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">

        <div class="flex items-start justify-between mb-4">
          <div>
            <h3 class="text-base font-semibold text-white">Review Cleaned Text</h3>
            <p class="text-sm text-gray-400 mt-0.5">Edit if needed, then approve to start video generation.</p>
          </div>
          <button onclick="backToStep1()" class="text-xs text-gray-500 hover:text-gray-300 underline">← Start over</button>
        </div>

        <!-- Section tabs (hidden when only 1 section) -->
        <div id="section-tabs" class="flex gap-2 mb-4 hidden"></div>

        <!-- Stats bar -->
        <div id="stats-bar" class="flex gap-6 mb-4 p-3 bg-gray-800 rounded-lg text-xs text-gray-400"></div>

        <!-- Cleaned text area -->
        <textarea
          id="cleaned-text"
          rows="14"
          class="w-full bg-gray-950 border border-gray-700 rounded-xl px-4 py-3 text-gray-100 text-sm focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
        ></textarea>

        <div class="flex items-center justify-between mt-4">
          <p class="text-xs text-gray-500">✏️ You can edit the text above before approving.</p>
          <button
            id="approve-btn"
            onclick="approveText()"
            class="bg-green-600 hover:bg-green-500 text-white font-semibold px-8 py-3 rounded-xl transition-colors duration-200 flex items-center gap-2"
          >
            <span>✓ Approve &amp; Generate Video</span>
          </button>
        </div>
        <div id="approve-error" class="mt-3 text-red-400 text-sm hidden"></div>
      </div>
    </div>

    <!-- ── STEP 3: Generating ── -->
    <div id="step3" class="step-panel hidden">
      <div class="bg-gray-900 border border-gray-800 rounded-2xl p-8 text-center">
        <div class="text-5xl mb-5">🎬</div>
        <h3 class="title-font text-xl font-semibold text-amber-400 mb-2">Video Generation Started</h3>
        <p id="success-message" class="text-gray-300 text-sm mb-6"></p>

        <div class="bg-gray-800 rounded-xl p-5 text-left text-sm space-y-3 max-w-md mx-auto mb-6">
          <div class="flex items-center gap-3 text-gray-300">
            <span class="text-green-400">✓</span> Text cleaned and processed
          </div>
          <div class="flex items-center gap-3 text-gray-300">
            <span class="text-green-400">✓</span> Sent to n8n workflow
          </div>
          <div class="flex items-center gap-3 text-gray-400">
            <span class="text-amber-400">⏳</span> Perplexity AI generating 20 scenes...
          </div>
          <div class="flex items-center gap-3 text-gray-400">
            <span class="text-gray-600">○</span> ElevenLabs synthesizing narration...
          </div>
          <div class="flex items-center gap-3 text-gray-400">
            <span class="text-gray-600">○</span> JSON2Video rendering with Ken Burns effects...
          </div>
        </div>

        <p class="text-xs text-gray-500 mb-6">
          Video will be ready in <span class="text-amber-400 font-medium">8–13 minutes</span>.
          Check your <a href="https://json2video.com" target="_blank" class="text-amber-400 hover:text-amber-300 underline">JSON2Video dashboard</a> for the completed video.
        </p>

        <button
          onclick="startOver()"
          class="text-sm text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 px-6 py-2 rounded-lg transition-colors"
        >
          Generate Another Video
        </button>
      </div>
    </div>

  </main>

  <script>
    // ── State ──
    let allSections = [];
    let activeSectionIndex = 0;

    // ── Character counter ──
    document.getElementById('raw-text').addEventListener('input', function() {
      const count = this.value.length;
      const words = this.value.trim() ? this.value.trim().split(/\\s+/).length : 0;
      document.getElementById('char-count').textContent = `${words.toLocaleString()} words · ${count.toLocaleString()} characters`;
    });

    // ── Step 1: Convert ──
    async function convertText() {
      const rawText = document.getElementById('raw-text').value.trim();
      if (!rawText) {
        showError('convert-error', 'Please paste some biblical text first.');
        return;
      }

      const btn = document.getElementById('convert-btn');
      btn.innerHTML = '<span class="spinner"></span><span>Cleaning...</span>';
      btn.disabled = true;
      hideError('convert-error');

      try {
        const res = await fetch('/api/clean', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: rawText }),
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Cleaning failed.');
        }

        const data = await res.json();
        allSections = data.sections;
        activeSectionIndex = 0;
        showStep2();
      } catch (e) {
        showError('convert-error', e.message);
      } finally {
        btn.innerHTML = '<span>Convert &amp; Clean</span>';
        btn.disabled = false;
      }
    }

    function showStep2() {
      // Populate section tabs if multiple sections
      const tabsEl = document.getElementById('section-tabs');
      tabsEl.innerHTML = '';

      if (allSections.length > 1) {
        tabsEl.classList.remove('hidden');
        allSections.forEach((s, i) => {
          const btn = document.createElement('button');
          btn.textContent = `Section ${i + 1}`;
          btn.className = `px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            i === 0 ? 'bg-amber-500 text-black' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`;
          btn.onclick = () => switchSection(i);
          tabsEl.appendChild(btn);
        });
      }

      displaySection(0);
      setStep(2);
    }

    function switchSection(index) {
      activeSectionIndex = index;
      displaySection(index);
      // Update tab styles
      const tabs = document.querySelectorAll('#section-tabs button');
      tabs.forEach((t, i) => {
        t.className = `px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
          i === index ? 'bg-amber-500 text-black' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
        }`;
      });
    }

    function displaySection(index) {
      const s = allSections[index];
      document.getElementById('cleaned-text').value = s.text;
      document.getElementById('stats-bar').innerHTML = `
        <span>📝 <strong class="text-white">${s.word_count.toLocaleString()}</strong> words</span>
        <span>⏱ ~<strong class="text-amber-400">${s.estimated_minutes} min</strong> video</span>
        <span>🎬 ~${s.estimated_scenes} scenes</span>
        ${allSections.length > 1 ? `<span class="ml-auto text-amber-500">Section ${index + 1} of ${allSections.length}</span>` : ''}
      `;
    }

    // ── Step 2: Approve ──
    async function approveText() {
      const approvedText = document.getElementById('cleaned-text').value.trim();
      if (!approvedText) {
        showError('approve-error', 'Text cannot be empty.');
        return;
      }

      const btn = document.getElementById('approve-btn');
      btn.innerHTML = '<span class="spinner"></span><span>Sending to n8n...</span>';
      btn.disabled = true;
      hideError('approve-error');

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: approvedText, section_index: activeSectionIndex }),
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Failed to trigger workflow.');
        }

        const data = await res.json();
        document.getElementById('success-message').textContent = data.message;
        setStep(3);
      } catch (e) {
        showError('approve-error', e.message);
      } finally {
        btn.innerHTML = '<span>✓ Approve &amp; Generate Video</span>';
        btn.disabled = false;
      }
    }

    // ── Navigation ──
    function backToStep1() { setStep(1); }
    function startOver() { setStep(1); document.getElementById('raw-text').value = ''; document.getElementById('char-count').textContent = '0 characters'; }

    function setStep(n) {
      [1, 2, 3].forEach(i => {
        document.getElementById(`step${i}`).classList.toggle('hidden', i !== n);
      });
      // Update step dots
      [1, 2, 3].forEach(i => {
        const dot = document.getElementById(`step-dot-${i}`);
        const circle = dot.querySelector('div');
        if (i < n) {
          dot.classList.remove('opacity-40');
          circle.className = 'w-7 h-7 rounded-full bg-green-600 text-white font-bold flex items-center justify-center text-xs';
        } else if (i === n) {
          dot.classList.remove('opacity-40');
          circle.className = 'w-7 h-7 rounded-full bg-amber-500 text-black font-bold flex items-center justify-center text-xs';
        } else {
          dot.classList.add('opacity-40');
          circle.className = 'w-7 h-7 rounded-full bg-gray-700 text-gray-300 font-bold flex items-center justify-center text-xs';
        }
      });
    }

    function showError(id, msg) { const el = document.getElementById(id); el.textContent = '⚠ ' + msg; el.classList.remove('hidden'); }
    function hideError(id) { document.getElementById(id).classList.add('hidden'); }
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    return HTMLResponse(content=LANDING_PAGE)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _webhook = os.getenv("N8N_WEBHOOK_URL", "")
    if not _webhook:
        print("\n⚠  WARNING: N8N_WEBHOOK_URL is not set in your .env file.")
        print("   The /api/generate endpoint will not work until you set it.")
        print("   See workflows/biblical-cinematic/README.md for n8n setup steps.\n")
    else:
        print(f"\n✓ n8n webhook configured: {_webhook[:60]}...\n")

    print("Starting Biblical Cinematic Generator at http://localhost:8000\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
