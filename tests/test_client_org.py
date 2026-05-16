"""Client tests for Org domain: organisation, feed, email, custom_fields, user."""

import json

import httpx

from mcp_immojump.client import ImmojumpAPIClient, ImmojumpCredentials


def _creds():
    return ImmojumpCredentials(base_url='http://localhost:8081', token='tok', organisation_id='org-1')


def _capture_client(handler):
    transport = httpx.MockTransport(handler)
    return ImmojumpAPIClient(_creds(), transport=transport)


# ---------------------------------------------------------------------------
# Organisation
# ---------------------------------------------------------------------------

def test_organisation_list_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.organisation_list()

    assert captured['path'] == '/api/organisations'


def test_organisation_members_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.organisation_members(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/members'


def test_organisation_update_member_roles_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.organisation_update_member_roles(org_id='org-1', user_id='u-1', role_ids=['r1', 'r2'])

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/organisations/org-1/members/u-1/roles'
    assert captured['json']['role_ids'] == ['r1', 'r2']


def test_organisation_invite_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.organisation_invite(org_id='org-1', data={'email': 'test@example.com'})

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/organisations/org-1/invites'


def test_organisation_cancel_invite_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.organisation_cancel_invite(org_id='org-1', invite_id='inv-1')

    assert captured['method'] == 'DELETE'
    assert captured['path'] == '/api/organisations/org-1/invites/inv-1'


def test_organisation_roles_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.organisation_roles(org_id='org-1')

    assert captured['path'] == '/api/organisations/org-1/roles'


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------

def test_feed_list_params():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.feed_list(channel_id='ch-1', cursor='abc')

    assert captured['path'] == '/api/organisation-feed'
    assert captured['params']['channel_id'] == 'ch-1'
    assert captured['params']['cursor'] == 'abc'


def test_feed_by_context_uses_type_and_id_query_params():
    """Regression: backend reads `type` and `id`, not `context_type`/`context_id`."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json={'items': [], 'nextCursor': None})

    with _capture_client(handler) as client:
        client.feed_by_context(context_type='immobilie', context_id='imm-1')

    assert captured['method'] == 'GET'
    assert captured['path'] == '/api/organisation-feed/by-context'
    # Backend expects `type`/`id`; sending `context_type`/`context_id` returns 400.
    assert captured['params']['type'] == 'immobilie'
    assert captured['params']['id'] == 'imm-1'
    assert captured['params']['organisation_id'] == 'org-1'
    # Guardrail: the legacy (broken) field names must not be sent.
    assert 'context_type' not in captured['params']
    assert 'context_id' not in captured['params']


def test_feed_by_context_preserves_context_type_values():
    """Each supported entity context_type maps through to the `type` param verbatim."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json={'items': [], 'nextCursor': None})

    for ctx_type in ('immobilie', 'contact', 'deal', 'activity'):
        with _capture_client(handler) as client:
            client.feed_by_context(context_type=ctx_type, context_id='x-1')
        assert captured['params']['type'] == ctx_type
        assert captured['params']['id'] == 'x-1'


def test_feed_create_post_sends_message_and_org():
    """Canonical payload uses `message` — the field the backend reads."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.feed_create_post(data={'message': 'Hello team', 'channel_id': 'ch-1'})

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/organisation-feed/post'
    assert captured['json']['organisation_id'] == 'org-1'
    assert captured['json']['message'] == 'Hello team'
    assert captured['json']['channel_id'] == 'ch-1'


def test_feed_create_post_aliases_legacy_text_to_message():
    """Backwards compat: callers using the legacy `text` field still produce a real post."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.feed_create_post(data={'text': 'Hello team'})

    # Backend reads `message`, so it must be present and equal to the legacy `text`.
    assert captured['json']['message'] == 'Hello team'


def test_feed_create_post_message_wins_over_text_when_both_present():
    """Explicit `message` is authoritative; `text` is only a fallback."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.feed_create_post(data={'message': 'canonical', 'text': 'legacy'})

    assert captured['json']['message'] == 'canonical'
    # `text` is forwarded untouched — backend ignores it, but we don't strip caller data.
    assert captured['json'].get('text') == 'legacy'


def test_feed_create_post_blank_text_does_not_overwrite_blank_message():
    """A whitespace-only `text` must not be promoted into `message`."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.feed_create_post(data={'text': '   '})

    # Aliasing must not turn whitespace into a fake message.
    assert 'message' not in captured['json'] or not (captured['json'].get('message') or '').strip()


def test_feed_create_post_does_not_mutate_caller_dict():
    """Aliasing happens on a copy; the caller's dict must stay intact."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    original = {'text': 'Hello'}
    with _capture_client(handler) as client:
        client.feed_create_post(data=original)

    assert original == {'text': 'Hello'}, 'caller-supplied dict was mutated'
    assert captured['json']['message'] == 'Hello'


def test_feed_create_post_forwards_extra_fields():
    """title, channel_id, context_type/context_id and meta must pass through untouched."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.feed_create_post(data={
            'message': 'body',
            'title': 'subject',
            'channel_id': 'ch-1',
            'context_type': 'immobilie',
            'context_id': 'imm-1',
            'meta': {'tag': 'note'},
        })

    body = captured['json']
    assert body['title'] == 'subject'
    assert body['channel_id'] == 'ch-1'
    assert body['context_type'] == 'immobilie'
    assert body['context_id'] == 'imm-1'
    assert body['meta'] == {'tag': 'note'}


def test_feed_add_comment_aliases_text_and_keeps_path():
    """feed_add_comment shares the same field-name bug; aliasing must apply here too."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.feed_add_comment(event_id='ev-1', data={'text': 'thx'})

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/organisation-feed/ev-1/comments'
    assert captured['json']['message'] == 'thx'
    assert captured['json']['organisation_id'] == 'org-1'


def test_feed_add_comment_accepts_canonical_message():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.feed_add_comment(event_id='ev-1', data={'message': 'thx'})

    assert captured['json']['message'] == 'thx'


def test_feed_comment_object_aliases_text():
    """feed_comment_object POST body shares the field-name bug; aliasing must apply."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.feed_comment_object(data={
            'context_type': 'immobilie',
            'context_id': 'imm-1',
            'text': 'Looks good',
        })

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/organisation-feed/comment-object'
    assert captured['json']['message'] == 'Looks good'
    # Context routing fields stay on the body (this endpoint uses them in JSON, not query).
    assert captured['json']['context_type'] == 'immobilie'
    assert captured['json']['context_id'] == 'imm-1'


def test_feed_toggle_reaction_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.feed_toggle_reaction(event_id='ev-1', emoji='👍')

    assert captured['path'] == '/api/organisation-feed/ev-1/reactions'
    assert captured['json']['emoji'] == '👍'


def test_feed_channels_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.feed_channels()

    assert captured['path'] == '/api/organisation-feed/channels'


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def test_email_list_path_and_params():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.email_list(folder='inbox', search='Rechnung')

    assert captured['path'] == '/api/email-messages'
    assert captured['params']['folder'] == 'inbox'
    assert captured['params']['search'] == 'Rechnung'


def test_email_thread_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.email_thread(thread_id='th-1')

    assert captured['path'] == '/api/email-messages/threads/th-1'


def test_email_mark_read_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.email_mark_read(message_ids=['m1', 'm2'], read=False)

    assert captured['json'] == {'message_ids': ['m1', 'm2'], 'read': False}


def test_email_archive_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.email_archive(message_ids=['m1'])

    assert captured['json'] == {'message_ids': ['m1']}


def test_email_move_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.email_move(message_ids=['m1'], folder='Archive')

    assert captured['json'] == {'message_ids': ['m1'], 'folder': 'Archive'}


def test_email_sync_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.email_sync()

    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/email-messages/sync'


def test_email_by_contact_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json=[])

    with _capture_client(handler) as client:
        client.email_by_contact(contact_id='c-1')

    assert captured['path'] == '/api/email-messages/contact/c-1'


# ---------------------------------------------------------------------------
# Custom Fields
# ---------------------------------------------------------------------------

def test_custom_fields_definitions_list_params():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json={'definitions': []})

    with _capture_client(handler) as client:
        client.custom_fields_definitions_list(model='immobilie')

    assert captured['path'] == '/api/custom-fields/definitions'
    assert captured['params']['model'] == 'immobilie'
    assert captured['params']['organisation_id'] == 'org-1'


def test_custom_fields_definition_create_includes_org():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(201, json={})

    with _capture_client(handler) as client:
        client.custom_fields_definition_create(data={'model': 'contact', 'name': 'VIP', 'type': 'boolean'})

    assert captured['json']['organisation_id'] == 'org-1'
    assert captured['json']['type'] == 'boolean'


def test_custom_fields_definition_update_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.custom_fields_definition_update(definition_id='def-1', data={'name': 'VIP Status'})

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/custom-fields/definitions/def-1'


def test_custom_fields_definition_delete_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.custom_fields_definition_delete(definition_id='def-1')

    assert captured['method'] == 'DELETE'
    assert captured['path'] == '/api/custom-fields/definitions/def-1'


def test_custom_fields_values_get_params():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['params'] = dict(req.url.params)
        return httpx.Response(200, json={'values': {}})

    with _capture_client(handler) as client:
        client.custom_fields_values_get(model='immobilie', target_id='imm-1')

    assert captured['params']['model'] == 'immobilie'
    assert captured['params']['target_id'] == 'imm-1'


def test_custom_fields_values_set_body():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.custom_fields_values_set(
            model='contact', target_id='c-1', values={'def-1': 'hello', 'def-2': 42},
        )

    assert captured['method'] == 'PUT'
    assert captured['json']['model'] == 'contact'
    assert captured['json']['target_id'] == 'c-1'
    assert captured['json']['values'] == {'def-1': 'hello', 'def-2': 42}


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

def test_user_me_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.user_me()

    assert captured['path'] == '/api/user/me'


def test_user_update_profile_path():
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['method'] = req.method
        captured['path'] = req.url.path
        return httpx.Response(200, json={})

    with _capture_client(handler) as client:
        client.user_update_profile(data={'first_name': 'Max'})

    assert captured['method'] == 'PUT'
    assert captured['path'] == '/api/user/profile'
