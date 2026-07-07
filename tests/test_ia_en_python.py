"""Tests for the changes introduced in this PR:

- ``mode_quiz(nb_questions_max=10)`` in ``ia_en_python.py`` now:
    * accepts a configurable question count instead of looping forever,
    * avoids asking the exact same question twice in a row (when more
      than one question is available),
    * prints a "(n/nb_questions_max)" progress indicator for each
      question.
- ``.chatpy_history.json`` gained two new entries (an assistant goodbye
  message followed by a user "au revoir" message) and must remain a
  valid history file respecting the schema used by
  ``ChatBot._charger_historique``.

Run with:
    python -m unittest tests.test_ia_en_python
    python -m unittest tests.test_ia_en_python.ModeQuizTests.test_default_nb_questions_max_is_ten
"""
import io
import inspect
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ia_en_python  # noqa: E402


HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".chatpy_history.json",
)


class ModeQuizTests(unittest.TestCase):
    """Tests for the updated mode_quiz() behaviour."""

    def setUp(self):
        # Isolate tests from the real FAQ content loaded at import time.
        self._faq_backup = ia_en_python.faq
        ia_en_python.faq = {
            "Q1": "Reponse un",
            "Q2": "Reponse deux",
            "Q3": "Reponse trois",
        }

    def tearDown(self):
        ia_en_python.faq = self._faq_backup

    def _run_quiz(self, nb_questions_max=None, inputs=None, choices=None):
        """Helper running mode_quiz with mocked input/random.choice, capturing stdout."""
        inputs = inputs or []
        buffer = io.StringIO()
        with patch("builtins.input", side_effect=inputs):
            patcher = patch("ia_en_python.random.choice", side_effect=choices) if choices is not None else None
            if patcher:
                patcher.start()
            try:
                with redirect_stdout(buffer):
                    if nb_questions_max is None:
                        ia_en_python.mode_quiz()
                    else:
                        ia_en_python.mode_quiz(nb_questions_max)
            finally:
                if patcher:
                    patcher.stop()
        return buffer.getvalue()

    def test_default_nb_questions_max_is_ten(self):
        """The new nb_questions_max parameter must default to 10."""
        default = inspect.signature(ia_en_python.mode_quiz).parameters["nb_questions_max"].default
        self.assertEqual(default, 10)

    def test_loop_stops_after_nb_questions_max(self):
        """The quiz must ask exactly nb_questions_max questions, not loop forever."""
        output = self._run_quiz(
            nb_questions_max=2,
            inputs=["Reponse un", "Reponse deux"],
            choices=[("Q1", "Reponse un"), ("Q2", "Reponse deux")],
        )
        self.assertIn("(1/2)", output)
        self.assertIn("(2/2)", output)
        self.assertNotIn("(3/2)", output)
        self.assertIn("Score final : 2/2", output)

    def test_custom_nb_questions_max_used_in_banner_and_prompts(self):
        output = self._run_quiz(nb_questions_max=1, inputs=["Reponse un"])
        self.assertIn("1 questions", output)
        self.assertIn("(1/1)", output)

    def test_early_exit_with_fin_before_any_answer(self):
        """Typing 'fin' immediately must stop the loop with zero questions answered."""
        output = self._run_quiz(nb_questions_max=5, inputs=["fin"])
        self.assertIn("Aucune question répondue.", output)
        self.assertNotIn("Score final", output)

    def test_early_exit_with_fin_after_some_answers(self):
        """The question for turn 2 is displayed (prompt happens before the
        'fin' check) but must not be scored: only 1 question is counted."""
        output = self._run_quiz(
            nb_questions_max=5,
            inputs=["Reponse un", "fin"],
            choices=[("Q1", "Reponse un"), ("Q2", "Reponse deux")],
        )
        self.assertIn("(1/5)", output)
        self.assertIn("(2/5)", output)
        self.assertEqual(output.count("💡 Réponse attendue"), 1)
        self.assertIn("Score final : 1/1", output)

    def test_zero_nb_questions_max_asks_nothing(self):
        """Boundary case: nb_questions_max=0 must not prompt for any input."""
        output = self._run_quiz(nb_questions_max=0, inputs=[])
        self.assertIn("Aucune question répondue.", output)
        self.assertNotIn("📝 Votre réponse", output)

    def test_does_not_repeat_same_question_twice_in_a_row(self):
        """When more than one question exists, the same question must not be
        asked on two consecutive turns (the new derniere_question guard)."""
        q1 = ("Q1", "Reponse un")
        q2 = ("Q2", "Reponse deux")
        # First draw returns Q1; second draw also returns Q1 (would repeat) so
        # the anti-repeat while loop must draw again, landing on Q2.
        output = self._run_quiz(
            nb_questions_max=2,
            inputs=["Reponse un", "Reponse deux"],
            choices=[q1, q1, q2],
        )
        self.assertIn("(1/2) Q1 ?", output)
        self.assertIn("(2/2) Q2 ?", output)

    def test_single_question_available_does_not_hang(self):
        """With only one question, the anti-repeat guard (len(questions) > 1)
        must not spin forever even though the same question is drawn twice."""
        ia_en_python.faq = {"UniqueQ": "UniqueA"}
        output = self._run_quiz(nb_questions_max=2, inputs=["UniqueA", "UniqueA"])
        self.assertIn("(1/2) UniqueQ ?", output)
        self.assertIn("(2/2) UniqueQ ?", output)
        self.assertIn("Score final : 2/2", output)

    def test_scoring_thresholds_still_reported_correctly(self):
        """Sanity check that scoring/labels still work correctly alongside the
        new bounded loop (correct vs wrong answers)."""
        output = self._run_quiz(
            nb_questions_max=2,
            inputs=["Reponse un", "totalement incorrect xyz"],
            choices=[("Q1", "Reponse un"), ("Q2", "Reponse deux")],
        )
        self.assertIn("✅ Bonne réponse", output)
        self.assertIn("❌ Pas tout à fait", output)
        self.assertIn("Score final : 1/2", output)


class ChatpyHistoryFileTests(unittest.TestCase):
    """Validates the schema of .chatpy_history.json, which this PR extended
    with two new entries (assistant goodbye + user 'au revoir')."""

    @classmethod
    def setUpClass(cls):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            cls.history = json.load(f)

    def test_history_file_is_a_list(self):
        self.assertIsInstance(self.history, list)
        self.assertGreater(len(self.history), 0)

    def test_every_entry_has_expected_schema(self):
        for entry in self.history:
            self.assertIsInstance(entry, dict)
            self.assertIn("role", entry)
            self.assertIn("message", entry)
            self.assertIn(entry["role"], ("assistant", "utilisateur"))
            self.assertIsInstance(entry["message"], str)

    def test_history_file_is_loadable_by_chatbot(self):
        """The file must be consumable by ChatBot._charger_historique without error."""
        bot = ia_en_python.ChatBot.__new__(ia_en_python.ChatBot)
        bot.historique = []
        bot._charger_historique()
        self.assertEqual(bot.historique, self.history)

    def test_appended_goodbye_exchange_present(self):
        """This PR appended an assistant goodbye reply followed by a user
        'au revoir' message; both must be present with the correct roles."""
        pairs = list(zip(self.history, self.history[1:]))
        found = any(
            first["role"] == "assistant"
            and "Au revoir" in first["message"]
            and second["role"] == "utilisateur"
            and second["message"].strip().lower() == "au revoir"
            for first, second in pairs
        )
        self.assertTrue(found, "Expected an assistant goodbye followed by a user 'au revoir' entry")


if __name__ == "__main__":
    unittest.main()