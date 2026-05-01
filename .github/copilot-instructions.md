# Copilot instructions for ChatPy

Purpose: help future Copilot sessions understand how to run, explore, and modify this project.

1) Build / test / lint

- This repository is a single-file Python CLI app. No build, test or lint config detected.
- Run the chatbot:
  - python3 "ia en python.py"
  - or: python "ia en python.py"
  - Note: the filename contains spaces — quote or escape the path.
- If you add tests, single-test examples to document here:
  - pytest: pytest path/to/test_file.py::test_function
  - unittest (single test): python -m unittest tests.test_module.TestClass.test_method
  - flake8/ruff/black: add commands here when those tools are added.

2) High-level architecture (brief)

- Entrypoint: ia en python.py
  - normaliser_texte(texte): unicode NFKD -> ASCII, strip punctuation, lowercasing.
  - calcul_similarite(a, b): SequenceMatcher ratio (0..1).
  - chatbot_response(message): core lookup and matching logic. It holds the faq_categories dict and implements three matching strategies:
    1. exact normalized match
    2. fuzzy matching with difflib.get_close_matches (cutoff 0.6, n=3)
    3. similarity-based ranking (threshold sim > 0.5)
  - print_colored(text, color, bold=False): ANSI colored output (used by main loop)
  - ChatBot class: manages historique, suggestions (self.relations), questions_posees, and provides methods:
    - ajouter_message / obtenir_contexte / obtenir_suggestions / traiter_message / afficher_historique
  - Main loop: interactive prompt, handles 'historique', special commands (help, liste, au revoir), and prints responses.

3) Key conventions and repo-specific patterns

- Filename with spaces: always quote paths when running ("ia en python.py") or use escaped spaces.
- FAQ store: faq_categories (nested dict). To add Q/A, edit faq_categories in chatbot_response or factor it to a separate data file if the dataset grows.
- Relations (follow-up suggestions): defined in ChatBot.relations. Suggestions are filtered against questions_posees and limited to 2.
- Thresholds and tuning:
  - get_close_matches cutoff is 0.6; similarity fallback uses sim > 0.5. Confidence displayed as int(similarity*100).
  - To change behavior, update those numeric constants in chatbot_response and obtenir_suggestions.
- Normalization: accents removed via NFKD + ASCII ignore; punctuation replaced with spaces. This is relied on across matching code.
- Output formatting: ANSI escape codes are used; some terminals may not render bold/color. print_colored uses a simple mapping — adjust if adding a third-party library (rich, colorama).
- History and deduplication: bot.questions_posees stores normalized questions to avoid suggesting repeated questions.

4) Where to look for changes

- To add tests or package this project, add a pyproject.toml/requirements.txt and update this file with commands to run tests and linters.
- If you refactor to multiple modules, move faq_categories into a dedicated data/module and update README and GUIDE_UTILISATION.md accordingly.

5) Other AI assistant configs

- No CLAUDE.md, AGENTS.md or other assistant rule files found in the project root. If added, include any non-obvious rules here.

---

Short checklist for Copilot sessions

- Start by opening ia en python.py and README.md to understand current Q/A and relations.
- Run the script with quoted filename to reproduce behavior quickly.
- Grep for faq_categories and relations when adding or altering questions/suggestions.
- When adding tests, update this file with exact commands to run single tests.

