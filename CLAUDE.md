# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ChatPy is a Python FAQ chatbot (CLI) paired with a static landing page. It answers questions about Python using fuzzy string matching and a confidence score system. There is no database, no server, and no external dependencies beyond the Python standard library.

## Running the Project

**Chatbot CLI:**
```bash
python3 "ia_en_python.py"
```

**Landing page (static, no server required):**
Open `Index.html` directly in a browser, or serve locally:
```bash
python3 -m http.server 8080
# Then open http://localhost:8080/Index.html
```

## Architecture

Everything lives in `ia_en_python.py` — no imports outside the standard library (`re`, `os`, `unicodedata`, `difflib`).

**Matching pipeline in `chatbot_response()`:**
1. Exact match after normalization (`normaliser_texte`)
2. Fuzzy match via `difflib.get_close_matches` (cutoff 0.6)
3. `SequenceMatcher` similarity scan (threshold 0.5)
4. Hard-coded conversational replies (greetings, thanks, etc.)

**`ChatBot` class** holds session state: conversation history, previously asked questions, and a `relations` dict that maps a question to follow-up suggestions shown after a response.

**`faq_categories`** (inside `chatbot_response`) is the only knowledge source — a nested dict of `{category: {question: answer}}`. It is rebuilt on every call.

## Key Customization Points

| Goal | Where |
|------|-------|
| Add/edit FAQ entries | `faq_categories` dict in `chatbot_response()` |
| Add follow-up suggestions | `self.relations` dict in `ChatBot.__init__()` |
| Adjust match sensitivity | `cutoff=0.6` (fuzzy) and `if sim > 0.5` (similarity) |
| Limit suggestions shown | `[:2]` slice in `obtenir_suggestions()` |
