# AGENTS.md

## Quick start

```bash
# CLI (no deps)
python3 "ia_en_python.py"

# Web (Flask)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
# http://localhost:5001
```

## Running tests

```bash
python3 -m unittest discover -v          # all
python3 -m unittest test_chatpy -v       # core matching/quiz logic
python3 -m unittest tests.test_base_donnees -v  # accounts/SQLite
python3 -m unittest tests.test_lacunes -v       # gap report
python3 -m unittest tests.test_i18n -v          # translation catalogue
```

Run after any change to `ia_en_python.py`. Tests use `unittest` (stdlib only, no pytest dependency). All tests that write files redirect to temp dirs via `tests/__init__.py` — they never touch the real `chatpy.db`, `.chatpy_history.json`, or `conversations.json`.

## Architecture

| File | Role |
|------|------|
| `ia_en_python.py` | Core chatbot — matching, quiz, suggestions, all shared by CLI and web. **Zero external deps.** |
| `app.py` | Flask backend — routes, OAuth, session management |
| `base_donnees.py` + `schema.sql` | SQLite accounts DB (`chatpy.db`) |
| `conversations.py` | Server-side conversation history (`conversations.json`) |
| `comptes.py` | Password hashing, validation, lockout logic |
| `lacunes.py` | Reads `questions_sans_reponse.json`, diagnoses FAQ gaps |
| `faq.json` | FAQ knowledge base (nested `{category: {question: answer}}`) |
| `aide_concepts.json` | Detailed concept explanations (`aide <sujet>`) |
| `chat.html` + `chat.js` | Real chat UI (not the landing page demo) |
| `compte.html` + `compte.js` | User settings page |
| `Index.html` + `script.js` | Landing page + signup modal |
| `preferences.js` | All user settings in `localStorage` (`chatpy.prefs.v1`) |
| `i18n.js` | Interface translation (6 languages). Bot always answers in French. |
| `nav-compte.js` | Account area of nav bar, single `/api/moi` call for the page |
| `animations.js` | Landing page scroll reveals, stat counters (Index.html only) |

## Gotchas

- **Single gunicorn worker is mandatory** (`Procfile` has `--workers 1`). JSON stores are guarded by `threading.Lock` which only works within one process. Raising `--workers` corrupts data.
- **Port 5001**, not 5000 (macOS AirPlay uses 5000).
- **`CHATPY_COOKIE_SECURE`** must be `0` locally (HTTP). Setting it to `1` locally kills all sessions.
- **New CSS/JS/image files** must be added to the `FICHIERS_PUBLICS` allow-list in `app.py` or they 404. Flask's static folder is disabled.
- **`preferences.js` and `i18n.js` load synchronously in `<head>`** (no `defer`). Moving them reintroduces a theme/language flash on load.
- **`CLAUDE.md`** contains comprehensive architecture docs — consult it for deep dives on matching pipeline, OAuth flows, quiz state machine, conversation storage, etc.
- **Bot answers in French only.** Translating the UI (`i18n.js`) does not translate the chatbot.
- **`.env.example` is the committed template.** Any new env var read by code must be added there.
- **OAuth callback URLs** must match exactly in provider consoles. `localhost:5001` for dev.
- **`chatpy.db`** has no password reset. Losing it permanently locks users out. Back up with `python3 base_donnees.py --sql > sauvegarde.sql`.
- **`SESSION_COOKIE_SAMESITE`** must stay `"Lax"` — `"Strict"` breaks OAuth redirect flows.

## Language

The codebase, comments, and all user-facing bot text are in French. Test names and internal comments may mix English.
