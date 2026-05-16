"""Unit tests for the feed message-payload normalizer.

The org-feed backend reads ``message`` from the JSON body. Earlier MCP
docstrings instructed callers to send ``text`` instead, which silently
produced empty posts. The client now aliases ``text`` -> ``message`` for
backwards compatibility. These tests pin the helper's exact behavior
without going through HTTP, complementing the wire-level tests in
``test_client_org.py``.
"""

import pytest

from mcp_immojump.client import _normalize_feed_message_payload


def test_canonical_message_passes_through_unchanged():
    payload = _normalize_feed_message_payload({'message': 'hi'})
    assert payload == {'message': 'hi'}


def test_legacy_text_is_aliased_to_message():
    payload = _normalize_feed_message_payload({'text': 'hi'})
    assert payload['message'] == 'hi'
    # The legacy key is preserved; the backend ignores unknown keys and we
    # don't want to silently rewrite payload shapes for the caller.
    assert payload['text'] == 'hi'


def test_explicit_message_wins_over_text():
    payload = _normalize_feed_message_payload({'message': 'canonical', 'text': 'legacy'})
    assert payload['message'] == 'canonical'
    assert payload['text'] == 'legacy'


def test_empty_string_message_is_replaced_by_non_empty_text():
    payload = _normalize_feed_message_payload({'message': '', 'text': 'fallback'})
    assert payload['message'] == 'fallback'


def test_whitespace_only_message_is_replaced_by_non_empty_text():
    payload = _normalize_feed_message_payload({'message': '   ', 'text': 'fallback'})
    assert payload['message'] == 'fallback'


def test_whitespace_only_text_does_not_overwrite_anything():
    payload = _normalize_feed_message_payload({'text': '   '})
    assert 'message' not in payload


def test_non_string_message_falls_back_to_text():
    """Defensive: a non-string message (e.g. None) should still get aliased from text."""
    payload = _normalize_feed_message_payload({'message': None, 'text': 'fallback'})
    assert payload['message'] == 'fallback'


def test_non_string_text_is_ignored():
    """If `text` is a non-string truthy value (list, int), don't promote it."""
    payload = _normalize_feed_message_payload({'text': 123})
    assert 'message' not in payload


def test_extra_fields_are_preserved():
    payload = _normalize_feed_message_payload({
        'message': 'hi',
        'channel_id': 'ch-1',
        'title': 't',
        'context_type': 'immobilie',
        'context_id': 'imm-1',
        'meta': {'k': 'v'},
    })
    assert payload['message'] == 'hi'
    assert payload['channel_id'] == 'ch-1'
    assert payload['title'] == 't'
    assert payload['context_type'] == 'immobilie'
    assert payload['context_id'] == 'imm-1'
    assert payload['meta'] == {'k': 'v'}


def test_does_not_mutate_input_dict():
    original = {'text': 'hi'}
    _normalize_feed_message_payload(original)
    assert original == {'text': 'hi'}


def test_none_input_returns_empty_dict():
    assert _normalize_feed_message_payload(None) == {}  # type: ignore[arg-type]


def test_empty_dict_input_returns_empty_dict():
    assert _normalize_feed_message_payload({}) == {}


@pytest.mark.parametrize('message', ['hi', 'a' * 5000, 'Mehrzeilig\nzweite Zeile', '👋 Hallo'])
def test_message_content_is_unchanged(message: str):
    """Aliasing must never modify the actual message content (no trimming, escaping, truncation)."""
    payload = _normalize_feed_message_payload({'message': message})
    assert payload['message'] == message
