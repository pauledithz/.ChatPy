# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ChatPy is a Python FAQ chatbot, usable either as a CLI or through a Flask web backend, paired with a static landing page. It answers questions about Python using fuzzy string matching and a confidence score system. There is no database and no external dependencies beyond the Python standard library, except for Flask (only required for the web backend, not the CLI).

## Running the Project

**Chatbot CLI (no dependencies beyond stdlib):**
```bash
python3 "ia_en_python.py"
```

**Web backend (Flask — serves the landing page, `/chat`, and the `/api/chat` endpoint):**
```bash
python3 -m venv .venv && source .venv/bin/activate   # first time only
pip install -r requirements.txt
python3 app.py
# Then open http://localhost:5001
```
A `.venv` is recommended over installing Flask system-wide, especially on macOS with Homebrew Python (PEP 668 blocks system-wide `pip install` there). `.vscode/settings.json` points `python.defaultInterpreterPath` at `.venv/bin/python` so the IDE picks it up automatically. Port 5001 (not 5000) is used because macOS's AirPlay Receiver commonly occupies 5000.
`app.py` imports the shared `bot` instance from `ia_en_python.py`, so the CLI and the web chat use the exact same matching logic and conversation state (`.chatpy_history.json`). The `/chat` page (`chat.html` + `chat.js`) is a real, working chat UI — unlike the animated demo on the landing page (see below). It's linked from the nav (`Index.html`) and reachable without logging in — the signup/login modal on `Index.html` is decorative (no real authentication) and unrelated to chat access.

**Landing page alone (static, no server required):**
Open `Index.html` directly in a browser, or serve locally:
```bash
python3 -m http.server 8080
# Then open http://localhost:8080/Index.html
```
Note: the `chat-preview` box on the landing page hero is a scripted animation cycling through canned example conversations (`script.js`) — it is not connected to the real chatbot.

## Architecture

Everything lives in `ia_en_python.py` — no imports outside the standard library (`re`, `os`, `json`, `random`, `datetime`, `unicodedata`, `difflib`).

**Data files (loaded once at import time, not hard-coded in the script):**
- `faq.json` — nested `{category: {question: answer}}`, loaded into `faq_categories`; flattened into `faq` and `norm_vers_original` (normalized question → original question) for lookups.
- `aide_concepts.json` — keyed by topic slug (e.g. `"variable"`, `"fonction"`), each entry has `titre`, `mots_cles`, `definition`, a `niveaux` list (🟢 débutant / 🟡 intermédiaire / 🔴 avancé, each with a `code` sample), plus optional `erreurs_courantes` and `a_retenir`. Powers the `aide <sujet>` command via `_chercher_concept()` / `_formater_concept()`.
- `.chatpy_history.json` — generated at runtime, persists conversation history across sessions (`ChatBot._charger_historique` / `_sauvegarder_historique`).
- `questions_sans_reponse.json` — generated at runtime by `_logger_question_sans_reponse()`; records any user question that fell through every matching stage (text, occurrence count, last-seen date), for spotting gaps to fill in `faq.json`.

Both JSON knowledge files are loaded via `_charger_json()`, which prints a warning and falls back to `{}` on a missing file or invalid JSON rather than crashing.

**Matching pipeline in `chatbot_response()`:**
1. Special commands checked first: `aide <sujet>`, `help`/`aide`/`?`, `liste`, `liste <catégorie>`, `cherche <mot>`.
2. Exact match after normalization (`normaliser_texte`).
3. Fuzzy match via `difflib.get_close_matches` (cutoff 0.6).
4. `SequenceMatcher` similarity scan (threshold 0.5), surfacing up to 2 alternate matches when confidence < 70%.
5. Hard-coded conversational replies (greetings, thanks, goodbye, etc.) via `_contient_mot()` — matched against the raw lowercased message, not the accent-stripped normalized form.
6. Fallback "I don't understand" reply, which logs the question to `questions_sans_reponse.json`.

**`ChatBot` class** holds session state: conversation history (persisted to `.chatpy_history.json`), previously asked questions (`questions_posees`), and a `relations` dict that maps a question to follow-up suggestions shown after a response (via `obtenir_suggestions()`).

**`mode_quiz()`** is a standalone REPL loop (entered via the `quiz` command) that picks a random FAQ question, compares the user's typed answer to the stored answer with `SequenceMatcher`, and reports a running score.

**`app.py`** is the Flask web backend. It serves `Index.html` at `/`, the real chat UI (`chat.html`/`chat.js`) at `/chat`, and a `POST /api/chat` endpoint (`{"message": "..."}` → `{"response": "..."}`) that calls `bot.traiter_message()`. It shares the single module-level `bot` instance from `ia_en_python.py`, so web and CLI sessions read/write the same `.chatpy_history.json` — there is no per-user session separation.

## Key Customization Points

| Goal | Where |
|------|-------|
| Add/edit FAQ entries | `faq.json` |
| Add/edit "aide <sujet>" concept explanations | `aide_concepts.json` |
| Add follow-up suggestions | `self.relations` dict in `ChatBot.__init__()` |
| Adjust match sensitivity | `cutoff=0.6` (fuzzy) and `if sim > 0.5` (similarity) in `chatbot_response()` |
| Limit suggestions shown | `[:2]` slice in `obtenir_suggestions()` |
| Review unanswered questions to grow the FAQ | `questions_sans_reponse.json` (generated at runtime) |
