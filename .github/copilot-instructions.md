# Copilot instructions for ChatPy

Purpose: help future AI assistant sessions understand how to run, test, and modify this project. `CLAUDE.md` at the repo root is the detailed reference — read it first; this file is a short summary.

## 1) Run / test

- Chatbot CLI (stdlib only): `python3 "ia_en_python.py"`
- Web backend (Flask): `pip install -r requirements.txt` in a `.venv`, then `python3 app.py` → http://localhost:5001
- Tests (stdlib `unittest`, no extra dependency): `python3 -m unittest test_chatpy -v`
  - Single test: `python3 -m unittest test_chatpy.TestMatchingFAQ.test_correspondance_exacte`
  - Run the suite after any change to `ia_en_python.py`.

## 2) High-level architecture

- `ia_en_python.py` — all chatbot logic, stdlib only.
  - Knowledge lives in JSON data files, **not** in the code: `faq.json` (nested `{category: {question: answer}}`) and `aide_concepts.json`.
  - `chatbot_response(message)`: special commands → exact normalized match → hybrid scored scan (`_score_correspondance`: SequenceMatcher character similarity + significant-word overlap, stop-words in `MOTS_VIDES`) → conversational replies → fallback that logs to `questions_sans_reponse.json`.
  - Quiz: `evaluer_reponse_quiz()` scores `max(full-text similarity, share of user's significant words found in the expected answer)`; thresholds `QUIZ_SEUIL_BONNE`/`QUIZ_SEUIL_PRESQUE`. Terminal loop `mode_quiz()`; web state machine `demarrer_quiz()`/`repondre_quiz()` (state stored in the Flask session by `app.py`).
  - `ChatBot` class: history persisted to `.chatpy_history.json` (atomic writes via `_ecrire_json_atomique`, capped at `HISTORIQUE_MAX_MESSAGES`, mutations under `_verrou_historique`), follow-up suggestions via `self.relations`.
- `app.py` — Flask backend: `/` (landing), `/chat` (real chat UI), `POST /api/chat`. Static files served only from the `FICHIERS_PUBLICS` allow-list — a new asset must be added there or it 404s.
- `Index.html`/`script.js` — landing page; its chat preview is a scripted animation, not the real bot. `chat.html`/`chat.js` — the real web chat.

## 3) Key conventions and tuning knobs

- Matching sensitivity: `SEUIL_CORRESPONDANCE` (answer threshold) and `POIDS_MOTS` (vocabulary vs. spelling weight); words ignored by matching: `MOTS_VIDES`. All at the top of `ia_en_python.py`.
- Normalization (`normaliser_texte`): NFKD → ASCII, punctuation stripped, lowercased. All matching relies on it.
- Runtime JSON files are written atomically (`_ecrire_json_atomique`) and corrupted files are moved to `<name>.corrompu`, never silently overwritten. Keep these guarantees when touching persistence.
- Add FAQ entries in `faq.json`, concepts in `aide_concepts.json`, follow-up suggestions in `ChatBot.relations`.
- Review `questions_sans_reponse.json` (generated at runtime) to find FAQ gaps.

## 4) Other AI assistant configs

- `CLAUDE.md` at the repo root holds the authoritative, detailed project guidance (architecture, pipeline, customization table). Keep both files in sync when the architecture changes.
