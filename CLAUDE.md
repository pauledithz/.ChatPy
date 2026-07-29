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
The Werkzeug debugger allows arbitrary code execution, so it is off by default; set `CHATPY_DEBUG=1` to enable it for local development only. `CHATPY_SECRET_KEY` signs the session cookie that carries quiz state; without it a random key is generated per process, so restarting the server drops any quiz in progress.
A `.venv` is recommended over installing Flask system-wide, especially on macOS with Homebrew Python (PEP 668 blocks system-wide `pip install` there). `.vscode/settings.json` points `python.defaultInterpreterPath` at `.venv/bin/python` so the IDE picks it up automatically. Port 5001 (not 5000) is used because macOS's AirPlay Receiver commonly occupies 5000.
`app.py` imports the shared `bot` instance from `ia_en_python.py`, so the CLI and the web chat use the exact same matching logic and conversation state (`.chatpy_history.json`). The `/chat` page (`chat.html` + `chat.js`) is a real, working chat UI — unlike the animated demo on the landing page (see below). It's linked from the nav (`Index.html`) and reachable without logging in — the signup/login modal on `Index.html` is decorative (no real authentication) and unrelated to chat access.

**Landing page alone (static, no server required):**
Open `Index.html` directly in a browser, or serve locally:
```bash
python3 -m http.server 8080
# Then open http://localhost:8080/Index.html
```
Note: the `chat-preview` box on the landing page hero is a scripted animation cycling through canned example conversations (`script.js`) — it is not connected to the real chatbot.

**Tests (stdlib `unittest`, no dependencies):**
```bash
python3 -m unittest test_chatpy -v
```
Covers normalization, the matching pipeline (typos, rephrasings, the opposite-meaning trap), the two suggestion sources, the gap journal's two counters, quiz scoring, the web quiz state machine, and persistence (atomic writes, history cap, corrupted-file handling). Tests that write redirect the runtime files to a temp dir via `unittest.mock.patch` — they never touch the real `.chatpy_history.json`. Run them after any change to `ia_en_python.py`.

## Architecture

Everything lives in `ia_en_python.py` — no imports outside the standard library (`re`, `os`, `json`, `random`, `datetime`, `unicodedata`, `difflib`).

**Data files (loaded once at import time, not hard-coded in the script):**
- `faq.json` — nested `{category: {question: answer}}`, loaded into `faq_categories`; flattened into `faq` and `norm_vers_original` (normalized question → original question) for lookups.
- `aide_concepts.json` — keyed by topic slug (e.g. `"variable"`, `"fonction"`), each entry has `titre`, `mots_cles`, `definition`, a `niveaux` list (🟢 débutant / 🟡 intermédiaire / 🔴 avancé, each with a `code` sample), plus optional `erreurs_courantes` and `a_retenir`. Powers the `aide <sujet>` command via `_chercher_concept()` / `_formater_concept()`.
- `.chatpy_history.json` — generated at runtime, persists conversation history across sessions (`ChatBot._charger_historique` / `_sauvegarder_historique`). Capped at `HISTORIQUE_MAX_MESSAGES` (oldest dropped), since the whole file is rewritten on every message.
- `questions_sans_reponse.json` — generated at runtime, records questions worth adding to `faq.json`, with two independent counters per entry: `occurrences` (bumped by `_logger_question_sans_reponse()` when a question fell through every matching stage) and `pouces_bas` (bumped by `signaler_reponse_inutile()` when a user thumbs-downs an answer in the web chat). The second one is the only way to spot a question that *did* match an FAQ entry — just not the right one. Both go through `_incrementer_journal()`; `_vaut_la_peine_d_etre_logguee()` filters out noise (single words, 5000-character pastes) so the journal only holds genuine FAQ gaps.

Both runtime files go through `_ecrire_json_atomique()` (temp file + `os.replace()`) rather than `open(path, 'w')`, which would truncate the file before rewriting it and lose it on a crash or a concurrent write. The Flask server is multi-threaded, so `_verrou_historique` / `_verrou_questions` guard the read-modify-write cycles. A file that fails to parse is moved aside to `<name>.corrompu` instead of being silently overwritten.

Both JSON knowledge files are loaded via `_charger_json()`, which prints a warning and falls back to `{}` on a missing file or invalid JSON rather than crashing.

**Matching pipeline in `chatbot_response()`:**
1. Special commands checked first: `aide <sujet>`, `help`/`aide`/`?`, `liste`, `liste <catégorie>`, `cherche <mot>`. `COMMANDES_TERMINAL` (`clear`, `historique`) are intercepted by the CLI loop before `chatbot_response()` ever sees them; the branch here exists so the *web* chat answers them with an explanation instead of "I don't understand". `quiz` is handled by both front-ends and so never reaches `chatbot_response()`.
2. Exact match after normalization (`normaliser_texte`).
3. Hybrid scored scan of the whole FAQ via `_score_correspondance()`: a weighted mix of `SequenceMatcher` character similarity and significant-word overlap (stop-words in `MOTS_VIDES` stripped, per-word fuzzy matching so typos still count). Answers when the score ≥ `SEUIL_CORRESPONDANCE` (0.5); shows up to 2 alternates when confidence < 70%. The word-overlap half (`POIDS_MOTS`) exists because character similarity alone confuses near-identical questions with opposite meanings ("supprimer"/"déclarer" une variable) and misses rephrasings ("c'est quoi une liste").
4. Hard-coded conversational replies (greetings, thanks, goodbye, etc.) via `_contient_mot()` — matched against the raw lowercased message, not the accent-stripped normalized form.
5. Fallback `REPONSE_INCOMPRISE` reply, which logs the question to `questions_sans_reponse.json`.

Stage 3 and the fallback both go through `_scanner_faq()`, which scores the whole FAQ once and sorts it. `questions_proches()` reuses it to surface the *near*-misses — questions scoring between `SEUIL_PROPOSITION` (0.3) and `SEUIL_CORRESPONDANCE` (0.5) — as a "vouliez-vous dire ?" after an unanswered question. It additionally requires at least one significant word in common, because character similarity alone drags in unrelated questions ("dresser un lama" → "décompresser un tuple").

**`ChatBot` class** holds session state: conversation history (persisted to `.chatpy_history.json`), previously asked questions (`questions_posees`), and a `relations` dict that maps a question to follow-up suggestions shown after a response (via `obtenir_suggestions()`).

`repondre(message)` is the single entry point both front-ends share. It returns `{"response", "suggestions", "titre_suggestions"}` — suggestions kept *out* of the answer text so the web chat can render them as clickable buttons. Exactly one source fills them: `obtenir_suggestions()` (related questions, after an answer) or `questions_proches()` (near-misses, after a failure), never both. `traiter_message()` is a thin CLI wrapper that folds them back into the text as a numbered list.

**Quiz.** The scoring rules live in `choisir_question_quiz()` and `evaluer_reponse_quiz()` (thresholds `QUIZ_SEUIL_BONNE` / `QUIZ_SEUIL_PRESQUE`), shared by both front-ends. `evaluer_reponse_quiz()` takes the best of two angles — full-text similarity, or the share of the user's significant words found in the expected answer — because FAQ answers embed code samples nobody reproduces verbatim; answering "append" to "comment ajouter un élément à une liste" counts as correct.
- `mode_quiz()` is the terminal REPL loop, entered via the `quiz` command in the CLI.
- `demarrer_quiz()` / `repondre_quiz(etat, message)` are the web equivalent: a state machine over a plain serializable dict, since each web message is an isolated HTTP request. `app.py` stores that dict in the Flask session cookie, so **each browser gets its own quiz** even though `bot` is a shared singleton. Only the question text and the score travel in the cookie — the expected answer never leaves the server.

While a quiz is active, `/api/chat` treats every message as an answer and bypasses `bot.traiter_message()` entirely, so quiz answers never land in `.chatpy_history.json` or `questions_sans_reponse.json`. `fin`/`exit`/`quitter` ends it early.

**`app.py`** is the Flask web backend. It serves `Index.html` at `/`, the real chat UI (`chat.html`/`chat.js`) at `/chat`, and two JSON endpoints. It shares the single module-level `bot` instance from `ia_en_python.py`, so web and CLI sessions read/write the same `.chatpy_history.json` — there is no per-user session separation.

- `POST /api/chat` — `{"message": "..."}` → `{"response", "suggestions", "titre_suggestions", "feedback_possible", "quiz_actif"}`, from `bot.repondre()`. `feedback_possible` tells the front whether the answer came from the FAQ (thumbs and suggestions make sense) or from the quiz (they don't) — a flag the front cannot derive itself, since the message that *ends* a quiz already reports `quiz_actif: false`.
- `POST /api/feedback` — `{"question": "...", "utile": false}` → records a thumbs-down via `signaler_reponse_inutile()`. A thumbs-up is accepted and ignored, so the front has a single code path.

Request-body validation for both lives in `_lire_message()`.

Flask's automatic static folder is disabled (`static_folder=None`). Assets are served one by one from the `FICHIERS_PUBLICS` allow-list, because the project root also holds source code and the runtime conversation logs — serving the directory wholesale would expose them. **A new CSS/JS/image file referenced by a page must be added to `FICHIERS_PUBLICS` or it will 404.**

## Key Customization Points

| Goal | Where |
|------|-------|
| Add/edit FAQ entries | `faq.json` |
| Add/edit "aide <sujet>" concept explanations | `aide_concepts.json` |
| Add follow-up suggestions | `self.relations` dict in `ChatBot.__init__()` |
| Adjust match sensitivity | `SEUIL_CORRESPONDANCE` (answer threshold) and `POIDS_MOTS` (vocabulary vs. spelling weight) constants at the top of `ia_en_python.py` |
| Words ignored during matching | `MOTS_VIDES` frozenset at the top of `ia_en_python.py` |
| Limit suggestions shown | `[:2]` slice in `obtenir_suggestions()` ; `limite` arg of `questions_proches()` |
| Tune "vouliez-vous dire ?" strictness | `SEUIL_PROPOSITION` constant at the top of `ia_en_python.py` |
| Review unanswered questions to grow the FAQ | `questions_sans_reponse.json` (generated at runtime) |
