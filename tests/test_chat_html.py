"""Tests for the chat.html welcome message update announcing the quiz command."""
import os

CHAT_HTML_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chat.html")


def _read_chat_html():
    with open(CHAT_HTML_PATH, encoding="utf-8") as f:
        return f.read()


def test_chat_html_welcome_message_mentions_quiz_command():
    content = _read_chat_html()
    assert "<code>quiz</code>" in content
    assert "tester vos connaissances" in content


def test_chat_html_welcome_message_still_mentions_help_command():
    content = _read_chat_html()
    assert "<code>help</code>" in content


def test_chat_html_quiz_is_introduced_before_help_in_the_subtitle():
    content = _read_chat_html()
    subtitle_start = content.index("chat-welcome-subtitle")
    quiz_index = content.index("<code>quiz</code>", subtitle_start)
    help_index = content.index("<code>help</code>", subtitle_start)
    assert quiz_index < help_index