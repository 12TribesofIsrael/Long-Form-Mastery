# Biblical Cinematic — Build Error Log

Running log of bugs hit during development. Kept here so we don't fix the same issue twice.
Archive this file when the app reaches full production.

---

## [2026-03-02] Ghost server blocking port 8000

**Symptom:** New server wouldn't bind to port 8000. `taskkill /F /PID <pid>` returned "process not found" but port was still occupied and serving old content.

**Root cause:** The server process was orphaned — its parent shell exited (context window ended) but the process kept running. Windows `taskkill` can't kill processes that have been orphaned from their original session in some cases.

**Fix:**
```powershell
# Kill specific PID via PowerShell (more reliable than taskkill):
Stop-Process -Id <pid> -Force

# Nuclear option — kill all Python:
Get-Process python | Stop-Process -Force
```

**Prevention:** Always use PowerShell `Stop-Process` when `taskkill` fails.

---

## [2026-03-02] Server serving stale HTML after code update

**Symptom:** After rewriting `app.py`, the server kept returning the old HTML even after restarting with a fresh `__pycache__`.

**Root cause:** `uvicorn.run("app:app", reload=True)` uses `multiprocessing.spawn` on Windows to create worker processes. The spawned worker imported a cached/old version of the module instead of reading the updated file.

**Fix:** Changed to `uvicorn.run(app, reload=False)` — no multiprocessing spawn, single process, always reads what's on disk at startup.

**Prevention:** Never use `reload=True` on Windows for this project. Restart manually after editing `app.py`.

---

## [2026-03-02] JSON2Video API key not loading — `realtime: false`

**Symptom:** `/api/status` kept returning `realtime: false`. Direct API calls to JSON2Video returned auth errors.

**Root cause:** `.env` had two entries for `JSON2VIDEO_API_KEY` — the placeholder on line 22 and the real key on line 28. `python-dotenv` uses the **first** occurrence, so the placeholder won (`your-json2video-api-key`). The server printed "✓ configured" anyway because a non-empty string is truthy.

**Fix:** Removed the duplicate placeholder line. `.env` now has one clean entry:
```
JSON2VIDEO_API_KEY=2CcHHheoC8loYYgL6TuAnpmgDJAhPfG9C7fwpdpY
```

**Prevention:** Only one entry per key in `.env`. If you need to update a key, edit the existing line — don't append a new one.

---

## [2026-02-XX] n8n generating "undefined" chapter content

**Symptom:** Perplexity received a prompt with "undefined" instead of the scripture text. Output scenes described "undefined chapter" content.

**Root cause:** The `Bible Chapter Text Input` Set node in n8n had `{{ $json.body.text }}` typed into the **field NAME** box instead of the **field VALUE** box. This created a weirdly-named field, and the downstream JS expression `$('Bible Chapter Text Input').item.json.inputText` returned `undefined`.

**Fix:** In the Set node:
- Field NAME = `inputText` (literal text, not an expression)
- Field VALUE = `{{ $json.body.text }}` (expression mode ON)

**Prevention:** In n8n Set nodes, always double-check which box (name vs value) you're typing expressions into. The expression toggle must be ON for the VALUE, not the NAME.

---

## Archive note

When the app is fully in production (YouTube auto-upload working, stable for 30+ days), move this file to:
`workflows/biblical-cinematic/archive/ERRORS-build-phase.md`
