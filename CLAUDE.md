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
Configuration lives in `.env` (git-ignored), loaded by `load_dotenv()` at the top of `app.py`; `.env.example` is the committed template listing every variable with empty values — **any new variable the code reads must be added there**, or a fresh clone has no way to know it exists. Shell variables win over `.env`, so a deployment can impose its own values.
The Werkzeug debugger allows arbitrary code execution, so it is off by default; set `CHATPY_DEBUG=1` to enable it for local development only. `CHATPY_SECRET_KEY` signs the session cookie that carries quiz state *and the logged-in user*; without it a random key is generated per process, so restarting the server drops any quiz in progress and logs everyone out. `CHATPY_COOKIE_SECURE=1` restricts that cookie to https — correct in production, but it must stay `0` locally or the browser rejects the cookie over http and no session ever holds.
A `.venv` is recommended over installing Flask system-wide, especially on macOS with Homebrew Python (PEP 668 blocks system-wide `pip install` there). `.vscode/settings.json` points `python.defaultInterpreterPath` at `.venv/bin/python` so the IDE picks it up automatically. Port 5001 (not 5000) is used because macOS's AirPlay Receiver commonly occupies 5000.
`app.py` imports the shared `bot` instance from `ia_en_python.py`, so the CLI and the web chat use the exact same matching logic and conversation state (`.chatpy_history.json`). The `/chat` page (`chat.html` + `chat.js`) is a real, working chat UI — unlike the animated demo on the landing page (see below). It's linked from the nav (`Index.html`) and reachable without logging in — the signup/login modal on `Index.html` now has working Google and GitHub sign-in (see below); its email/password form and the Apple/Yahoo buttons remain decorative. Chat access requires no login. `/compte` (`compte.html` + `compte.js`) is the user area: the connected profile, the display settings (interface language, theme, animations, text size), and a **Chatbot** card (answer sensitivity, follow-up suggestions, thumbs, typing indicator).

**Landing page alone (static, no server required):**
Open `Index.html` directly in a browser, or serve locally:
```bash
python3 -m http.server 8080
# Then open http://localhost:8080/Index.html
```
Note: the `chat-preview` box on the landing page hero is a scripted animation cycling through canned example conversations (`script.js`) — it is not connected to the real chatbot.

**Gap report (stdlib only — reads `questions_sans_reponse.json`, tells you what to add to `faq.json`):**
```bash
python3 lacunes.py             # report
python3 lacunes.py --tout      # no 10-per-section cap
python3 lacunes.py --nettoyer  # drop entries the FAQ now answers
```
See `lacunes.py` under Architecture below.

**Tests (stdlib `unittest`, no dependencies):**
```bash
python3 -m unittest test_chatpy -v
python3 -m unittest tests.test_lacunes -v
python3 -m unittest tests.test_i18n -v
```
Covers normalization, the matching pipeline (typos, rephrasings, the opposite-meaning trap), the two suggestion sources, the gap journal's two counters, quiz scoring, the web quiz state machine, and persistence (atomic writes, history cap, corrupted-file handling). `tests/test_i18n.py` reads `i18n.js` as text (this repo has no JavaScript runtime) to check the translation catalogue: one translation per language per key, placeholders preserved, no key used but undeclared, and the French fallback still present in the HTML. Tests that write redirect the runtime files to a temp dir via `unittest.mock.patch` — they never touch the real `.chatpy_history.json`. Run them after any change to `ia_en_python.py`.

## Architecture

Everything lives in `ia_en_python.py` — no imports outside the standard library (`re`, `os`, `json`, `random`, `datetime`, `unicodedata`, `difflib`).

**Data files (loaded once at import time, not hard-coded in the script):**
- `faq.json` — nested `{category: {question: answer}}`, loaded into `faq_categories`; flattened into `faq` and `norm_vers_original` (normalized question → original question) for lookups.
- `aide_concepts.json` — keyed by topic slug (e.g. `"variable"`, `"fonction"`), each entry has `titre`, `mots_cles`, `definition`, a `niveaux` list (🟢 débutant / 🟡 intermédiaire / 🔴 avancé, each with a `code` sample), plus optional `erreurs_courantes` and `a_retenir`. Powers the `aide <sujet>` command via `_chercher_concept()` / `_formater_concept()`.
- `.chatpy_history.json` — generated at runtime, persists conversation history across sessions (`ChatBot._charger_historique` / `_sauvegarder_historique`). Capped at `HISTORIQUE_MAX_MESSAGES` (oldest dropped), since the whole file is rewritten on every message. **That cap is a cost limit, not a comfort setting**: at ~220 bytes per entry, the former value of 1,000,000 meant rewriting 210 MB on every single message once full. It is 2,000 now (~450 KB). Truncating it costs nobody their conversations — those live in `conversations.json` or in the browser; this journal only feeds the bot's context.
- `comptes.json` — generated at runtime, the email/password accounts: `{"<email>": {id, nom, email, empreinte, cree}}`, where `empreinte` is a scrypt hash and never a password. Git-ignored, and absent from `FICHIERS_PUBLICS` so it is never served.
- `conversations.json` — generated at runtime, the archived conversations of **logged-in users only**, keyed `{"<fournisseur>-<id>": [conversation, …]}`. Managed by `conversations.py`; see the history section below. Git-ignored, like every runtime file.
- `questions_sans_reponse.json` — generated at runtime, records questions worth adding to `faq.json`, with two independent counters per entry: `occurrences` (bumped by `_logger_question_sans_reponse()` when a question fell through every matching stage) and `pouces_bas` (bumped by `signaler_reponse_inutile()` when a user thumbs-downs an answer in the web chat). The second one is the only way to spot a question that *did* match an FAQ entry — just not the right one. Both go through `_incrementer_journal()`; `_vaut_la_peine_d_etre_logguee()` filters out noise (single words, 5000-character pastes) so the journal only holds genuine FAQ gaps.

Both runtime files go through `_ecrire_json_atomique()` (temp file + `os.replace()`) rather than `open(path, 'w')`, which would truncate the file before rewriting it and lose it on a crash or a concurrent write. The Flask server is multi-threaded, so `_verrou_historique` / `_verrou_questions` guard the read-modify-write cycles. A file that fails to parse is moved aside to `<name>.corrompu` instead of being silently overwritten.

Both JSON knowledge files are loaded via `_charger_json()`, which prints a warning and falls back to `{}` on a missing file or invalid JSON rather than crashing.

**`lacunes.py`** turns `questions_sans_reponse.json` into a work list. The raw journal is a flat list of failures, and two very different failures look identical in it: a question the FAQ *already* answers under another wording needs a rewording, while a genuinely absent subject needs an answer written — confusing the two grows the FAQ with duplicates that fix nothing. So each entry is re-scored against the **current** FAQ via `_scanner_faq()` and sorted into four families, printed most-urgent first:

| Diagnosis | Condition | What to do |
|---|---|---|
| `mauvaise_reponse` | score ≥ `SEUIL_CORRESPONDANCE` **and** `pouces_bas` > 0 | the FAQ answered and the user rejected it — a false positive, invisible anywhere else |
| `manquante` | below `SEUIL_PROPOSITION`, or no significant word shared | write a new `faq.json` entry |
| `a_rapprocher` | between the two thresholds **and** a shared significant word | reword the existing entry; don't add one |
| `couverte` | score ≥ `SEUIL_CORRESPONDANCE`, no thumbs-down | the FAQ grew since — stale journal line |

The shared-significant-word requirement mirrors `questions_proches()`: character similarity alone drags unrelated questions into `a_rapprocher` ("dresser un lama" → "décompresser un tuple"), which would send you rewording an entry that has nothing to do with the question.

Entries are diagnosed **before** being clustered (`regrouper()`, greedy, `SEUIL_REGROUPEMENT` = 0.6 — deliberately stricter than `SEUIL_CORRESPONDANCE`, since an over-eager merge hides one whole gap behind another). That order guarantees a cluster never mixes two different fixes, and lets `--nettoyer` decide entry by entry instead of trusting a group's representative. Ranking is `occurrences + 2 × pouces_bas`: a thumbs-down marks a failure the user never saw announced, so it outranks an admitted "je ne comprends pas".

`--nettoyer` is the only writing path, and it removes `couverte` entries only. It re-reads the journal under `_verrou_questions` immediately before writing and deletes just the targeted keys, so a counter bumped by the running Flask server between analysis and write survives. Without `--nettoyer` the tool never touches the file — it does not even move a corrupted journal aside, unlike `_incrementer_journal()`.

**Matching pipeline in `chatbot_response()`:**
1. Special commands checked first: `aide <sujet>`, `help`/`aide`/`?`, `liste`, `liste <catégorie>`, `cherche <mot>`. `COMMANDES_TERMINAL` (`clear`, `historique`) are intercepted by the CLI loop before `chatbot_response()` ever sees them; the branch here exists so the *web* chat answers them with an explanation instead of "I don't understand". `quiz` is handled by both front-ends and so never reaches `chatbot_response()`.
2. Exact match after normalization (`normaliser_texte`).
3. Hybrid scored scan of the whole FAQ via `_score_correspondance()`: a weighted mix of `SequenceMatcher` character similarity and significant-word overlap (stop-words in `MOTS_VIDES` stripped, per-word fuzzy matching so typos still count). Answers when the score ≥ `SEUIL_CORRESPONDANCE` (0.5); shows up to 2 alternates when confidence < 70%. The word-overlap half (`POIDS_MOTS`) exists because character similarity alone confuses near-identical questions with opposite meanings ("supprimer"/"déclarer" une variable) and misses rephrasings ("c'est quoi une liste").
4. Hard-coded conversational replies (greetings, thanks, goodbye, etc.) via `_contient_mot()` — matched against the raw lowercased message, not the accent-stripped normalized form.
5. Fallback `REPONSE_INCOMPRISE` reply, which logs the question to `questions_sans_reponse.json`.

Stage 3 and the fallback both go through `_scanner_faq()`, which scores the whole FAQ once and sorts it. `questions_proches()` reuses it to surface the *near*-misses — questions scoring between `SEUIL_PROPOSITION` (0.3) and the answer threshold — as a "vouliez-vous dire ?" after an unanswered question. It additionally requires at least one significant word in common, because character similarity alone drags in unrelated questions ("dresser un lama" → "décompresser un tuple").

**Sensitivity is per-visitor.** `chatbot_response(message, seuil)` takes the answer threshold as an argument (`None` → `SEUIL_CORRESPONDANCE`), fed from `SENSIBILITES` (`stricte` 0.65 / `normale` 0.5 / `large` 0.38) through `seuil_de_sensibilite()`, which falls back to normal on an unknown name rather than refusing — the setting is a comfort, not a permission. Three consequences worth keeping straight:

- **`questions_proches()` must receive the same `seuil`** (its `seuil=` argument, the band's *upper* bound). Otherwise a question rejected at 60% in strict mode falls into a hole: neither answered nor proposed. Every value in `SENSIBILITES` stays above `SEUIL_PROPOSITION` for the same reason — a threshold below it would close the band entirely.
- **The gap journal is judged at the default threshold, never the visitor's.** A question the FAQ answers perfectly well, left unanswered because *this* visitor asked for `stricte`, is not a gap; logging it would send `lacunes.py` rewording an entry that has nothing wrong with it. The fallback checks `scores[0]` against `SEUIL_CORRESPONDANCE` before calling `_logger_question_sans_reponse()`.
- **Nothing is stored server-side.** `bot` is a singleton shared by the whole site and the CLI, so keeping the setting on it would inflict the last visitor's choice on everyone. It travels with each message instead: `repondre(message, sensibilite=…)` → `/api/chat` body → `chat.js` reading `localStorage`.

**`ChatBot` class** holds session state: conversation history (persisted to `.chatpy_history.json`) and a `relations` dict mapping a question to hand-picked follow-ups.

**Follow-up suggestions key off the FAQ entry that matched, never the typed message.** `chatbot_response()` takes an optional `trace` dict and writes the retained question into `trace["question"]` — filled only by the two branches that draw on the FAQ (exact match, then scored match), so a command, a greeting or a failure leaves it empty. `repondre()` passes a fresh dict and uses it both to pick suggestions and to tell success from failure, replacing an older test that sniffed for `"Confiance:"` in the answer text. It is an out-parameter rather than a richer return type because `chatbot_response(msg) -> str` is the pipeline's entry point for the CLI and ~20 tests; the dict is caller-owned, so nothing is shared between threads.

This is what the matching pipeline is *for*: keying off the raw message meant demanding the exact wording of the `relations` dict, so "qu'est-ce qu'une liste" produced follow-ups while "c'est quoi une liste" produced none.

`obtenir_suggestions()` then resolves in two steps: an exact normalized lookup in `relations` (hand-picked, allowed to cross categories, wins), else the neighbours of the same `faq_categories` entry, walked from the one *after* the current question and wrapping around — otherwise every question in a category would offer the same two. **The fallback is what gives coverage:** `relations` holds 5 entries against 55 FAQ questions, so without it 50 answers would show nothing. Tests assert that every FAQ question yields at least one suggestion, that suggestions are real FAQ questions, and that no `relations` key is misspelled — a typo there would silently never fire, hidden by the fallback.

**Nothing is filtered on already-asked questions.** The former `questions_posees` filter compared normalized text against original question strings and so never matched; fixing the comparison would have been worse, because `bot` is a singleton shared by every visitor and the CLI — the set only grows, and suggestions would fade out for everyone until the server restarts.

`repondre(message, sensibilite=None)` is the single entry point both front-ends share. It returns `{"response", "suggestions", "titre_suggestions"}` — suggestions kept *out* of the answer text so the web chat can render them as clickable buttons. Exactly one source fills them: `obtenir_suggestions()` (related questions, after an answer) or `questions_proches()` (near-misses, after a failure), never both. `traiter_message()` is a thin CLI wrapper that folds them back into the text as a numbered list.

**Quiz.** The scoring rules live in `choisir_question_quiz()` and `evaluer_reponse_quiz()` (thresholds `QUIZ_SEUIL_BONNE` / `QUIZ_SEUIL_PRESQUE`), shared by both front-ends. `evaluer_reponse_quiz()` takes the best of two angles — full-text similarity, or the share of the user's significant words found in the expected answer — because FAQ answers embed code samples nobody reproduces verbatim; answering "append" to "comment ajouter un élément à une liste" counts as correct.
- `mode_quiz()` is the terminal REPL loop, entered via the `quiz` command in the CLI.
- `demarrer_quiz()` / `repondre_quiz(etat, message)` are the web equivalent: a state machine over a plain serializable dict, since each web message is an isolated HTTP request. `app.py` stores that dict in the Flask session cookie, so **each browser gets its own quiz** even though `bot` is a shared singleton. Only the question text and the score travel in the cookie — the expected answer never leaves the server.

While a quiz is active, `/api/chat` treats every message as an answer and bypasses `bot.traiter_message()` entirely, so quiz answers never land in `.chatpy_history.json` or `questions_sans_reponse.json`. `fin`/`exit`/`quitter` ends it early.

**`app.py`** is the Flask web backend. It serves `Index.html` at `/`, the real chat UI (`chat.html`/`chat.js`) at `/chat`, the user area (`compte.html`/`compte.js`) at `/compte`, and two JSON endpoints.

**`/` is for anonymous visitors only.** The landing page is a pitch — it explains the chatbot and plays a scripted demo of it. Once you are signed in that pitch has no audience, so `index()` redirects a session holder to `PAGE_APRES_CONNEXION`. Two consequences that are easy to break:
- **The response is `Cache-Control: no-store`,** on both branches. `/` is the only route whose body depends on the session cookie; a cached redirect would keep bouncing someone who has just signed out, with nothing on screen to explain why, and no way out but clearing the cache.
- **Nav links to `/` would become dead ends,** so `nav-compte.js` rewrites them when `/api/moi` reports a session: the logo points at `/chat`, and the "Accueil" entry is removed rather than left to bounce. It lives there because that file is the only one that asks who is logged in.

Signing out (account dropdown) restores the landing page immediately — the door closes, it is not sealed, and `tests/test_app_accueil.py` guards exactly that. `/compte` is deliberately **not** gated on being logged in: every setting it hosts lives in the browser and has nothing to do with an account — including the chatbot ones, which is why the sensitivity travels in the request body rather than the session. `compte.js` adapts only the identity card from what `/api/moi` answers. It shares the single module-level `bot` instance from `ia_en_python.py`, so web and CLI sessions read/write the same `.chatpy_history.json` — there is no per-user session separation.

- `POST /api/chat` — `{"message": "...", "sensibilite": "stricte|normale|large"}` → `{"response", "suggestions", "titre_suggestions", "feedback_possible", "quiz_actif"}`, from `bot.repondre()`. `sensibilite` is optional (`_lire_sensibilite()` returns `""` when absent, so an older front or the CLI behaves as before) and anything that is not a string is discarded there — `SENSIBILITES` is a dict, and an unhashable value would raise instead of falling back. `feedback_possible` tells the front whether the answer came from the FAQ (thumbs and suggestions make sense) or from the quiz (they don't) — a flag the front cannot derive itself, since the message that *ends* a quiz already reports `quiz_actif: false`.
- `POST /api/feedback` — `{"question": "...", "utile": false}` → records a thumbs-down via `signaler_reponse_inutile()`. A thumbs-up is accepted and ignored, so the front has a single code path.
- `GET|PUT|PATCH|DELETE /api/conversations[/<id>]` — the conversation history, see below.

Request-body validation for both lives in `_lire_message()`.

**Google sign-in (OAuth 2.0 / OpenID Connect).** Server-side authorization-code flow via Authlib, so `GOOGLE_CLIENT_SECRET` never reaches the browser. Authlib is configured from Google's discovery document, which supplies the authorization/token URLs and signing keys — none of it is hard-coded — and it generates the `state` (CSRF) and `nonce` (replay) parameters itself.
- `GET /auth/google` — redirects to Google. Scope is exactly `openid email profile`; anything more triggers Google's app-verification review.
- `GET /auth/google/callback` — exchanges the code, **rejects an account whose `email_verified` is false** (an unverified Google account proves nothing about owning the address), stores `{id, nom, email, photo, fournisseur}` in `session["utilisateur"]`, and redirects to `PAGE_APRES_CONNEXION`. Failures redirect to `/?connexion=echec` or `/?connexion=email_non_verifie` — never with the technical error in the URL, which would land in logs and browser history.

**Where a successful login lands.** `PAGE_APRES_CONNEXION` (`app.py`) is `/chat`, for all three sign-in methods. Signing in is only worth anything here because it brings back your conversations, and those live on `/chat` — leaving people on the landing page cost them one more click to reach where they were already going. The two OAuth callbacks `redirect()` there; the two JSON routes return it as a `redirection` field so the front does not restate the destination (`script.js` navigates to it instead of reloading in place). **Failures still come back to `/`**, because the `?connexion=…` alerts live in `script.js`, which only `Index.html` loads — a failure sent to `/chat` would be silent. That works because a failed sign-in leaves no session, so `index()` still serves the page. The one blind spot: someone *already* signed in who reaches `/auth/google` by hand and fails would be bounced to `/chat` without seeing the alert. Nothing in the UI offers that route, and their existing session is untouched, so it is left alone.

**GitHub sign-in (OAuth 2.0, no OpenID Connect).** Same authorization-code flow and same outcomes; what differs from Google is what drives the code:
- GitHub publishes no discovery document, so `authorize_url` / `access_token_url` / `api_base_url` are hard-coded in the `oauth.register("github", …)` call.
- There is no `id_token`: the identity is read afterwards from the REST API through `_api_github()` (`GET /user`, then `GET /user/emails`). Two extra requests, hence two extra failure modes — a dead network or a token revoked in between both redirect to `/?connexion=echec` rather than half-connecting anyone.
- There is no `email_verified` field. `_email_verifie_github()` picks the primary **verified** address from `/user/emails`, falling back to any other verified one; with none, the login is refused exactly like an unverified Google account. `/user` alone is not enough — GitHub emails are private by default and come back `null` there.
- Scope is `read:user user:email` — the broader `user` scope would also grant *write* access to the profile.
- `GET /auth/github` and `GET /auth/github/callback`, mirroring the Google routes. The session entry carries `fournisseur: "google" | "github"`, since both providers number their accounts independently and nothing else would tell Google user 42 from GitHub user 42.

**Email + password accounts (`comptes.py`).** The third sign-in method, and the only one that needs no configuration at all — it works on a fresh clone, unlike Google and GitHub. Accounts live in `comptes.json` as scrypt hashes via `werkzeug.security` (already a Flask dependency, so nothing was added to `requirements.txt`).
- `POST /auth/inscription` — `{email, mot_de_passe, confirmation, nom, rester_connecte}` → creates the account and opens the session. `POST /auth/connexion` — same minus `confirmation`/`nom`. Both answer JSON so the modal never reloads the page to show an error.
- **Two things it deliberately does not do, both for the same reason — there is no SMTP server:** addresses are never verified, and there is no password reset. That first point is a real asymmetry with Google and GitHub, whose unverified accounts are *rejected*; an address typed here proves nothing, which is why local accounts are tagged `fournisseur: "local"` — so a future privilege can require a verified one. The second point is why signup asks for the password twice: a typo would lock someone out permanently.
- **Account enumeration is guarded on two channels.** Wrong password and unknown address return the byte-identical message, and an unknown address is still checked against a throwaway hash (`_empreinte_factice()`) so the response takes just as long — without it, an instant reply would say "nobody is registered here". Measured at 71 ms vs 72 ms.
- `MAX_MOT_DE_PASSE` is a *ceiling* as much as a floor: scrypt over a multi-megabyte string would tie the server up for seconds, so one request could stall it. On login the password is truncated rather than rejected — it is wrong either way, and hashing it in full is precisely the denial of service being avoided.
- Failed logins are counted per address (`TENTATIVES_MAX`, `BLOCAGE_SECONDES`). This lives in memory: it resets on restart and is not shared across processes. Enough to blunt a dictionary attack from a browser; not a substitute for a rate limiter in front of the server.
- Signup *does* admit that an address is already registered. Hiding it would need an email round trip to disambiguate, which is exactly what is unavailable — and a vague message would send someone in circles who simply forgot they had signed up.

**Shared by both providers:**
- `POST /auth/logout` — POST only: in GET, a third-party `<img src="/auth/logout">` would sign visitors out unnoticed. Shared by both providers.
- `GET /api/moi` — `{"connecte": bool, "oauth_disponible": bool, ...}`. The front cannot read the identity itself (the cookie is HttpOnly), so it asks. `oauth_disponible` means *at least one* provider is configured.

The identity is **session-only** — there is no user table. `.chatpy_history.json` and `questions_sans_reponse.json` stay shared across all visitors: the bot's own context and the FAQ gap journal are global, and making them per-user would mean breaking the module-level `bot` singleton. What logging in gives you is the conversation history described below — `conversations.json`, partitioned per account and served only to its owner. Keep the two apart when reasoning about privacy: a logged-in user's *archived conversations* are theirs alone, but every question asked still lands in the one shared history file that feeds the bot.

`SESSION_COOKIE_SAMESITE` must stay `"Lax"`: `"Strict"` drops the cookie on the redirect back from the provider and the flow dies on a `mismatching_state`.

The two providers are independent: `GOOGLE_CONFIGURE` and `GITHUB_CONFIGURE` each gate their own routes (503 when the matching `*_CLIENT_ID`/`*_CLIENT_SECRET` pair is empty — the state of any fresh clone), and `OAUTH_CONFIGURE` is just their `or`, used for the `CHATPY_SECRET_KEY` requirement and `/api/moi`. Nothing crashes at import, so the site stays fully usable with one provider configured, or none. The redirect URIs are `http://localhost:5001/auth/google/callback` and `http://localhost:5001/auth/github/callback`; each must match its console entry character for character (Google Cloud console / GitHub *Settings → Developer settings → OAuth Apps*), or the flow fails with `redirect_uri_mismatch`.

The signup modal's email/password form is **live**, not decorative: one `<form id="formCompte">` serves both sign-in and sign-up, with the class `form--connexion` hiding the fields that only registration needs (name, password confirmation). `script.js` swaps the labels, the submit text and the `autocomplete` attribute (`current-password` ↔ `new-password`, or the browser's password manager offers the wrong thing), then posts JSON and, on success, navigates to the `redirection` the server returned (`/chat`) rather than reloading in place. The Apple and Yahoo buttons remain decorative. The modal's focus trap recomputes its focusable list on every Tab rather than caching it at open time, because switching to sign-up adds two fields a cached list would skip.

`<a class="btn google">` and `<a class="btn github">` in `Index.html` point at `/auth/google` and `/auth/github` — a navigation, not a form submit, hence `<a>` and not `<button>`. `nav-compte.js` fills `#navCompte` from `/api/moi`; `script.js` keeps only what is specific to the landing page — the `/?connexion=…` alerts (which name no provider, since both flows share those codes) and the signup modal. The modal exists on `Index.html` alone, so the "Se connecter" links on `/chat` and `/compte` point at `/?inscription=1`, which `script.js` turns into an `openSignupModal()` call rather than duplicating the markup on three pages. The `[data-action="start"]` buttons open that modal only while nobody is logged in; once `/api/moi` reports a session, `adapterAppelsALAction()` relabels them from their `data-label-connecte` attribute and sends them to `/chat` instead. Since `/` now redirects a session holder away, that branch is a safety net rather than the normal path — it still fires on a page the browser served from its back-forward cache, or in a tab left open while another one signed in. The flag is read *inside* the click handler, not captured when the listeners are attached, because `/api/moi` answers well after that point. The rest of the signup modal (email/password, Apple, Yahoo) is still decorative.

Flask's automatic static folder is disabled (`static_folder=None`). Assets are served one by one from the `FICHIERS_PUBLICS` allow-list, because the project root also holds source code and the runtime conversation logs — serving the directory wholesale would expose them. **A new CSS/JS/image file referenced by a page must be added to `FICHIERS_PUBLICS` or it will 404.**

## Conversation history

`/chat` keeps a list of past conversations in a collapsible side panel. **Storage is hybrid, and that is the central design decision:** a logged-in user's conversations go to the server (so they follow them from one device to the next — which is what having an account is *for*), while a visitor without an account keeps theirs in `localStorage`, exactly as before. Nothing about the anonymous experience regressed.

**`conversations.py`** owns the server side, separate from `ia_en_python.py` on purpose. `.chatpy_history.json` cannot serve this feature and never will: it is a flat log shared by every visitor *and* the CLI, with no timestamps and no user attribution, so there is no way to tell which lines belong to whom. It feeds the bot's context; it is not anyone's history. `conversations.json` is partitioned per account instead:

```
{"google-42": [{id, titre, cree, maj, quiz_actif, messages: [...]}, ...]}
```

The provider is part of the key — Google and GitHub number their accounts independently, so `google-42` and `github-42` are different people. It reuses `ia._ecrire_json_atomique` and `ia._mettre_de_cote` (the same convention `lacunes.py` follows), and takes `_verrou` around every read-modify-write, since two tabs saving at once would otherwise have the second overwrite the first.

Everything arriving from the browser is rebuilt field by field in `nettoyer_conversation()` rather than trusted: types, sizes, and the message list are all re-derived, unknown messages are dropped instead of failing the whole request, and the id must match a strict alphabet because it becomes a dict key. Caps (`MAX_CONVERSATIONS`, `MAX_MESSAGES`, `MAX_LONGUEUR_TEXTE`) exist because the whole file is rewritten on every save.

**Routes** (`app.py`) are all gated by `_cle_ou_401()`. The storage key is derived from `session["utilisateur"]` and **never** from a request parameter — accepting a client-supplied user id would let anyone read anyone's history. On `PUT`, the id in the URL wins over any id in the body, so a request cannot write somewhere other than where it claims to. `lister()` returns summaries only (`id`, `titre`, `maj`, `nb_messages`): shipping the full text of fifty conversations to draw a list of titles would cost hundreds of kilobytes per page load. Search therefore runs server-side (`?q=`), over titles *and* message bodies, normalised through `ia.normaliser_texte` so accents and case do not matter.

**`chat.js`** hides the split behind one `magasin` interface (`lister`, `obtenir`, `enregistrer`, `renommer`, `supprimer`), with `magasinServeur` and `magasinLocal` behind it. Both are async — including the local one — so no caller ever needs to know which is active. Points worth keeping in mind when editing:

- **`modifie` guards every save.** Without it, merely opening a conversation would rewrite it, push its `maj` forward, and sort the list by *last opened* instead of *last used* — consulting an old conversation would drag it to the top.
- **Saves are debounced (400 ms).** One exchange is a message plus a reply; writing on each would double the requests for a single visible round trip.
- **`quiz_actif` is only restored on the very first load**, never when switching conversations. Quiz state lives in the server's session cookie, not in the conversation, so restoring it on a switch would show a quiz badge the server knows nothing about.
- **Leaving a conversation sends `fin`** if a quiz is running, otherwise the next conversation's first message would be scored as an answer to the previous one's quiz.
- **The old single-conversation key is migrated, not dropped**, under the fixed id `reprise-v1`. Fixed and not random: if clearing the old key ever failed, a random id would re-import a duplicate on every load. Migration only ever reads the key matching the *current* identity — importing a shared browser's anonymous transcript into whoever logged in next would hand someone else's questions to the wrong account.

## Front-end: the shared layer

Four scripts are shared by `Index.html`, `chat.html` and `compte.html`, on top of each page's own script.

**`preferences.js`** — every user setting, display and chatbot alike, stored in `localStorage` under `chatpy.prefs.v1` and declared in one `SCHEMA`. Most are applied as a `data-…` attribute on `<html>`; `SCHEMA` entries with **`attribut: null`** are the ones CSS cannot express, read by the script that needs them through `ChatPyPrefs.lire()`:

| Setting | Values (default first) | Applied by |
|---|---|---|
| `langue` | `auto`, `fr`, `en`, `es`, `de`, `it`, `pt` | `i18n.js` — it writes `lang` on `<html>` and rewrites the text; `attribut: null` because the default-writes-nothing rule must not apply (a document always declares its language) |
| `theme` | `auto`, `clair`, `sombre` | `data-theme` |
| `animations` | `auto`, `reduites` | `data-animations` |
| `taille` | `normale`, `petite`, `grande` | `data-taille` |
| `suggestions` | `visibles`, `masquees` | `data-suggestions` |
| `retours` | `visibles`, `masques` | `data-retours` |
| `saisie` | `animee`, `directe` | `chat.js` — the typing row is *not created*, since hiding it in CSS would leave its avatar holding an empty gap |

**`DUREE_MIN_SAISIE` (550 ms, `chat.js`) is what makes `saisie` mean anything.** The bot talks to no API — it compares strings in memory and `/api/chat` returns in ~3 ms. Without a floor, the three dots are created and removed inside one frame and are never painted, so *both* values of the setting looked identical and it read as broken. The delay is deliberate, applies to nothing but that row, and is skipped entirely under reduced motion (waiting in front of bouncing dots is precisely what that preference asks to avoid) or when `saisie` is `directe`. **If the bot ever gains a slow backend, this floor should go** — it would then be adding latency on top of real latency.
| `sensibilite` | `normale`, `stricte`, `large` | sent to the server on every `/api/chat` message (see above) |

Hiding the suggestion chips and the thumbs in CSS rather than in `chat.js` is deliberate: the setting then applies to messages already on screen and to those restored from an old conversation, with nothing to redraw. The blocks stay in the DOM, which costs nothing — they hold no data the page does not already have.

It is loaded **synchronously in `<head>`, before any content and without `defer`**: those attributes have to exist before the first paint, or the page renders one frame in the wrong theme and visibly flips. Moving this tag, deferring it, or pushing it to the end of `<body>` reintroduces that flash. Each setting's default value removes its attribute rather than writing it, so plain CSS and the `prefers-color-scheme` / `prefers-reduced-motion` media queries take over — that is precisely what "auto" means here. Unknown values fall back to the default instead of writing an attribute the CSS cannot interpret. The module publishes `window.ChatPyPrefs` (`lire`, `definir`, `basculerTheme`, `themeEffectif`) and fires a `chatpy:prefs` event on `document` so the nav toggle and the `/compte` selectors stay in sync without polling each other.

**`i18n.js`** — the interface language, in six languages (`fr` `en` `es` `de` `it` `pt`). Loaded synchronously in `<head>` **immediately after `preferences.js`**, whose `langue` setting it reads; `auto` resolves through `navigator.languages`, falling back to French for any language not covered.

**Only the interface is translated — the bot still answers in French.** `faq.json`, `aide_concepts.json` and the quiz are written in French, and the matching engine leans on a French `MOTS_VIDES` list, so translating the UI does not translate the chatbot. Rather than leave that to be discovered, the chat's welcome screen shows `chat.note_langue` outside French ("ChatPy answers in French — ask your Python questions in French"); that key's *French* translation is deliberately empty, which is the one exception to "no entry may be blank". For the same reason, the two example chips that send a real French sentence keep their French labels — the label is the text that goes to the bot, and translating it would make the bubble show a question the visitor never wrote. The three chips that send a *command* (`aide …`, `quiz`, `help`) do get translated labels.

**French is the source, and it stays written in the HTML.** Every translated element keeps its French text as its content and carries a key: `data-i18n` (textContent), `data-i18n-attr="placeholder:cle;aria-label:autre"` (attributes), `data-i18n-html` (the hero `<h1>` alone, whose `<span>` carries the gradient). Without JavaScript the page therefore renders in French, complete — the same principle as `animations.js` hiding nothing from the HTML. The catalogue repeats French only so that switching *back* to it has something to write over the translation in place.

`TEXTES` is keyed by string, each entry an array in `LANGUES` order — one line per key showing all six languages side by side, which is the only layout where a missing translation is visible at a glance. A short array does not throw: the missing position falls back to French, and `tests/test_i18n.py` is what turns that silence into a failure (it also checks that `{jeton}` placeholders survive translation, and that every key used in a page or script exists). An unknown key renders as the key itself — `nav.deconnexion` on screen names its own culprit, where an empty string would just erase a button.

Changing language **rewrites the page in place** rather than reloading: `i18n.js` re-applies the catalogue and then fires `chatpy:langue` on `document`, which each page script uses to redo what it built itself — `script.js` re-runs `appliquerMode()` (the modal writes its own labels), `compte.js` re-places the segment cursors (translated labels have different widths) and redraws the identity card, and `chat.js` rebuilds the visible bubbles from the conversation data, since `renderAI` output carries no keys. Two states must survive that rebuild: the running quiz (it lives in the server's session cookie) and the `modifie` flag (losing it would cancel a pending save).

**The brief veil.** Translating needs a parsed document, so the earliest possible moment is `DOMContentLoaded` — by which the browser may already have painted in French. Instead of that flicker, `body` is hidden while there is genuinely something to rewrite (language ≠ `fr`), *from JavaScript only*: with no JS the class is never set and nothing is ever hidden. A 1200 ms timer lifts the veil regardless, because a page left permanently invisible would be far worse than a flicker.

`i18n.js` **must stay in `FICHIERS_PUBLICS`** — a 404 there shows raw keys across all three pages, so `tests/test_i18n.py` asserts it is served, and that each page loads it in `<head>` after `preferences.js`.

**Server-side messages are translated too, from a second catalogue** (`comptes.MESSAGES`, keyed by code then language). The sign-in modal's refusals (invalid address, password too short, too many attempts) are written by the server, which cannot know a setting that lives in `localStorage` — so `script.js` sends `langue` in the request body and `comptes.normaliser_langue()` falls back to French for anything absent or unknown, since a display comfort must never block an otherwise valid signup. Duplicating the catalogue is the deliberate cost: returning error *codes* for the front to translate would make every other caller of the API (curl, a test, a script) read meaningless responses. **`identifiants_incorrects` is a single code on purpose** — unknown address and wrong password must return byte-identical text in *every* language, or a translation would leak what French hides; a test checks it.

**`nav-compte.js`** — the account area of the nav bar. It performs the single `/api/moi` call for the whole page and publishes it as `window.ChatPyMoi`, a promise that **always resolves** (a failed fetch yields `{connecte: false}`), so `chat.js`, `compte.js` and `script.js` consume it instead of each issuing their own request. Logged out it only inserts the theme toggle and leaves the HTML's own login control alone — which is why a page opened without the server still works. Logged in it swaps that control for an avatar button and a dropdown (chat, account, sign out), and rewrites the nav's links to `/` (see `index()` above). It also exports `window.ChatPyAvatar`, the photo-with-fallback-to-initial helper, since the same avatar is drawn at three sizes across the site.

**`animations.js`** — scroll reveals, stat counters, the cursor-following card glow, and the nav that condenses past 40px. It is loaded by `Index.html` only; `/chat` animates from CSS plus its own `mouvementReduit()` in `chat.js`, a copy of the same two-trigger rule (explicit `/compte` choice first, then the system's `prefers-reduced-motion`). Two rules govern this file:
- **Nothing is hidden by the HTML.** The `.reveal` class (opacity 0) is added *by the script* just before observing the element. Without JavaScript nothing is concealed, instead of the usual failure mode where a broken script leaves a blank page.
- **The hero's entrance animation is not here — it is in CSS** (`.hero > *`). This script runs at `DOMContentLoaded`, potentially after the first paint, so animating the hero from JS would show it, blank it, then fade it back in. A CSS animation is honoured from the first frame.

The stat figures carry their final value as text in `Index.html` and the target in `data-compteur` / `data-suffixe` / `data-decimales`; the script only replaces the text while counting, so no-JS and reduced-motion both show the correct number.

**Theming.** `style.css` defines every colour as a token on `:root` (dark, the default identity), with the light palette repeated in two places: `@media (prefers-color-scheme: light)` scoped to `:root:not([data-theme="sombre"])`, and `:root[data-theme="clair"]` so an explicit choice beats the system in both directions. **The two light blocks must stay identical** — a token added to one and not the other silently breaks one of the two paths. No colour belongs anywhere else in the file, with one deliberate exception: the bot's reply bubble stays a white island in both themes (it holds code samples, notes and badges calibrated on white), so its internals are hard-coded and only `--bulle-contour` changes, to detach it from a white panel in light mode. The hero's SVG grid and gradients are repainted from CSS (`.grid-bg path`, `.stop-fond`, `.stop-lueur`) because a CSS rule outranks an SVG presentation attribute — the attributes stay in the markup as a fallback.

Motion is cut by two independent triggers: the system's `prefers-reduced-motion`, and the explicit choice in `/compte`. Both are handled in CSS *and* consulted in `animations.js`, because the script does things CSS cannot undo (counting numbers). The system trigger needs its own `@media` block so it still works when JavaScript does not run.

## Deployment

`python3 app.py` is the Werkzeug **development** server and must not face the internet. The committed `Procfile` runs `gunicorn --workers 1 --threads 8`.

**The single worker is load-bearing, not a performance choice.** Every JSON store in this project (`comptes.json`, `conversations.json`, `.chatpy_history.json`, `questions_sans_reponse.json`) is guarded by a `threading.Lock`, which serialises threads *within one process* and does nothing across processes. Two gunicorn workers can interleave a read-modify-write on `comptes.json` and silently drop an account; `comptes._tentatives` (the brute-force lockout) would likewise be counted per worker, multiplying the allowed attempts by the worker count. Raising `--workers` requires replacing the JSON files with a real database first — there is no smaller fix.

**`CHATPY_PROXIES`** enables `ProxyFix` and defaults to `0`. Behind a reverse proxy it must be set, or `url_for(..., _external=True)` builds the callback URL from the internal connection and both OAuth flows die on `redirect_uri_mismatch`. It is opt-in because `X-Forwarded-*` are just claims: with no proxy rewriting them, any visitor could send `X-Forwarded-Host: attacker.example` and redirect the OAuth flow to their own domain. Production also needs a fixed `CHATPY_SECRET_KEY`, `CHATPY_COOKIE_SECURE=1`, `CHATPY_DEBUG` unset, and the production callback URLs registered in both provider consoles.

`comptes.json` is the only copy of every account, and there is no password reset — losing it locks users out permanently. It needs a backup; so does `conversations.json`.

## Key Customization Points

| Goal | Where |
|------|-------|
| Add/edit FAQ entries | `faq.json` |
| Add/edit "aide <sujet>" concept explanations | `aide_concepts.json` |
| Add follow-up suggestions | `self.relations` in `ChatBot.__init__()` — keys and values must be exact FAQ questions (a test enforces it); anything not listed falls back to category neighbours |
| Change the follow-up fallback | `_voisines_de_categorie()` in `ia_en_python.py` |
| Adjust match sensitivity | `SEUIL_CORRESPONDANCE` (answer threshold) and `POIDS_MOTS` (vocabulary vs. spelling weight) constants at the top of `ia_en_python.py` |
| What the per-visitor sensitivity slider does | `SENSIBILITES` in `ia_en_python.py` — every value must stay above `SEUIL_PROPOSITION` |
| Words ignored during matching | `MOTS_VIDES` frozenset at the top of `ia_en_python.py` |
| Limit suggestions shown | the two `[:2]` slices in `obtenir_suggestions()` ; `limite` arg of `questions_proches()` |
| Tune "vouliez-vous dire ?" strictness | `SEUIL_PROPOSITION` constant at the top of `ia_en_python.py` |
| Review unanswered questions to grow the FAQ | `python3 lacunes.py` (reads `questions_sans_reponse.json`, generated at runtime) |
| Weight of a thumbs-down vs. a plain failure in the gap report | `POIDS_POUCE_BAS` in `lacunes.py` |
| How aggressively the gap report merges rephrasings | `SEUIL_REGROUPEMENT` in `lacunes.py` |
| Any colour, in either theme | the token blocks at the top of `style.css` — never in the rules below them |
| Add a user setting | `SCHEMA` in `preferences.js`, a `.segments[data-pref]` group in `compte.html` (or a `select.reglage-select[data-pref]` past three or four values — `compte.js` drives both), and either a `:root[data-…]` rule in `style.css` or `attribut: null` plus a `ChatPyPrefs.lire()` read in the script concerned |
| Edit any interface text, in any language | the one line for its key in `TEXTES` (`i18n.js`) — never in the HTML, which only holds the French fallback |
| Add an interface language | `LANGUES` and `NOMS_LANGUES` in `i18n.js`, one translation at the same position in *every* `TEXTES` line, `SCHEMA.langue` in `preferences.js`, an `<option>` in `compte.html`, plus `LANGUES` and every `MESSAGES` entry in `comptes.py` |
| Wording of the server's sign-in refusals | `MESSAGES` in `comptes.py` — keep `identifiants_incorrects` identical across both failure paths |
| What the chat says about the bot being French-only | `chat.note_langue` in `i18n.js` (its French entry is empty on purpose) |
| Which elements appear on scroll, and the stagger between them | `GROUPES` at the top of `animations.js` |
| Chat motion (message entrance, typing dots, chip cascade, send pulse) | the `.msg-row` / `.typing-indicator` / `chipIn` / `envoiPulse` rules in `style.css`; the JS half (`DUREE_MIN_SAISIE`, `defilerEnBas`) is in `chat.js` |
| Speed/feel of every transition | `--ressort` (easing curve) in `style.css` |
| Entries in the account dropdown | `creerMenuCompte()` in `nav-compte.js` |
| Password rules, lockout after failed logins | `MIN_MOT_DE_PASSE`, `TENTATIVES_MAX`, `BLOCAGE_SECONDES` in `comptes.py` |
| How long "rester connecté" lasts | `PERMANENT_SESSION_LIFETIME` in `app.py` |
| Where a successful login lands | `PAGE_APRES_CONNEXION` in `app.py` — the three sign-in methods and `index()` all read it |
| Whether the landing page stays open to signed-in users | the `session.get("utilisateur")` test in `index()` (`app.py`), plus `adapterLiensAccueil()` in `nav-compte.js` for the nav links |
| How many conversations are kept | `MAX_CONVERSATIONS` in `conversations.py` (server) and `MAX_CONVERSATIONS_LOCALES` in `chat.js` (browser — far lower, localStorage caps around 5 MB per domain) |
| How conversations are titled | `_titre_par_defaut()` in `conversations.py` and `titreDeduit()` in `chat.js` — both truncate the first question asked; keep them in step |
| Date groupings in the history panel | `groupeDe()` in `chat.js` |
| Width and breakpoint of the history panel | `.historique` and the `max-width: 860px` block in `style.css` |
| Stat figures on the landing page | the `data-compteur` / `data-suffixe` / `data-decimales` attributes in `Index.html` (keep the text content in sync — it is the no-JS fallback) |
