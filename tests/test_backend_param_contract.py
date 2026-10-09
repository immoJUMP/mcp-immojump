"""Tools must send the keys the immo-calc backend actually reads.

Flask drops unknown JSON keys and query parameters without an error. A tool
that sends ``read`` where the route reads ``is_read`` gets HTTP 200 and does
the opposite of what the agent asked for (the route defaults to True). The
mismatches below come from a review against immo-calc ``modules/routes/``
(09.10.2026); each test pins the exact key the route reads, so a rename on
either side shows up here instead of in a customer's mailbox.

The tests go through the registered MCP tool, not just the client method:
the tool signature is what the agent sees, and a parameter that the client
silently drops is just as wrong as one the backend ignores.
"""

from __future__ import annotations

import inspect
import json

import httpx
import pytest

import mcp_immojump._shared as shared
from mcp_immojump.client import ImmojumpAPIClient


@pytest.fixture(scope='module')
def tools():
    from mcp_immojump.server import mcp

    return {name: tool.fn for name, tool in mcp._tool_manager._tools.items()}


@pytest.fixture()
def wire(monkeypatch):
    """Route every tool call through a MockTransport and record the requests."""
    requests: list[httpx.Request] = []

    def handler(req: httpx.Request) -> httpx.Response:
        requests.append(req)
        return httpx.Response(200, json={'ok': True})

    def client_factory(creds):
        return ImmojumpAPIClient(creds, transport=httpx.MockTransport(handler))

    monkeypatch.setattr(shared, 'ImmojumpAPIClient', client_factory)
    return requests


CREDS = {'token': 'tok', 'organisation_id': 'org-1', 'base_url': 'http://localhost:8081'}


def _only(requests):
    assert len(requests) == 1, [str(r.url) for r in requests]
    return requests[0]


def _body(req: httpx.Request):
    return json.loads(req.read())


def _params(tool_fn):
    return set(inspect.signature(tool_fn).parameters)


# ---------------------------------------------------------------------------
# E-Mail: read/starred flags — wrong key meant "always mark as read/starred"
# ---------------------------------------------------------------------------

def test_email_mark_read_false_sends_is_read_false(tools, wire):
    tools['email_mark_read'](message_ids=['m-1'], read=False, **CREDS)

    req = _only(wire)
    assert req.url.path == '/api/email-messages/mark-read'
    assert _body(req) == {'message_ids': ['m-1'], 'is_read': False}


def test_email_mark_starred_false_sends_is_starred_false(tools, wire):
    tools['email_mark_starred'](message_ids=['m-1'], starred=False, **CREDS)

    req = _only(wire)
    assert req.url.path == '/api/email-messages/mark-starred'
    assert _body(req) == {'message_ids': ['m-1'], 'is_starred': False}


@pytest.mark.parametrize('raw', ['false', 'False', '0', 'no'])
def test_email_flags_parse_string_false(tools, wire, raw):
    """Some MCP clients send booleans as strings; bool('false') is True."""
    tools['email_mark_read'](message_ids=['m-1'], read=raw, **CREDS)
    tools['email_mark_starred'](message_ids=['m-1'], starred=raw, **CREDS)

    assert _body(wire[0])['is_read'] is False
    assert _body(wire[1])['is_starred'] is False


# ---------------------------------------------------------------------------
# E-Mail: template send — /send ignores template, variables and contact_ids
# ---------------------------------------------------------------------------

def test_email_send_with_template_uses_the_route_that_reads_the_template(tools, wire):
    tools['email_account_send_with_template'](
        account_id='acc-1',
        subject='Exposé',
        body_html='<p>Hallo</p>',
        to=['kunde@example.com'],
        contact_ids=['c-1'],
        template_id='tpl-1',
        variables={'vorname': 'Max'},
        signature_id='sig-1',
        **CREDS,
    )

    req = _only(wire)
    assert req.method == 'POST'
    assert req.url.path == '/api/org/email-accounts/acc-1/send-email'
    body = _body(req)
    assert body['template_id'] == 'tpl-1'
    assert body['variables'] == {'vorname': 'Max'}
    assert body['contact_ids'] == ['c-1']
    assert body['html'] == '<p>Hallo</p>'
    assert body['to'] == ['kunde@example.com']
    assert body['signature_id'] == 'sig-1'


def test_email_send_with_template_needs_no_body_when_a_template_renders_it(tools, wire):
    tools['email_account_send_with_template'](
        account_id='acc-1',
        to='kunde@example.com',
        template_id='tpl-1',
        **CREDS,
    )

    body = _body(_only(wire))
    assert body['template_id'] == 'tpl-1'
    assert body['subject'] == ''
    assert body['html'] == ''


def test_email_send_with_template_without_template_still_needs_subject_and_body(tools, wire):
    with pytest.raises(ValueError, match='subject'):
        tools['email_account_send_with_template'](account_id='acc-1', to='kunde@example.com', **CREDS)
    assert wire == []


# ---------------------------------------------------------------------------
# Loans
# ---------------------------------------------------------------------------

def test_loans_list_sends_the_org_filter_the_route_reads(tools, wire):
    tools['loans_list'](**CREDS)

    req = _only(wire)
    assert req.url.path == '/api/loans'
    # orga_id is the filter older backends read; organisation_id feeds the
    # enterprise gate and is the filter name since immo-calc accepts it too.
    assert req.url.params['orga_id'] == 'org-1'
    assert req.url.params['organisation_id'] == 'org-1'


def test_loans_outstanding_sends_immobilie_ids_and_as_of(tools, wire):
    assert 'loan_ids' not in _params(tools['loans_outstanding'])

    tools['loans_outstanding'](immobilie_ids=['i-1', 'i-2'], as_of='2026-12-31', **CREDS)

    req = _only(wire)
    assert req.url.path == '/api/loans/outstanding'
    assert _body(req) == {'immobilie_ids': ['i-1', 'i-2'], 'as_of': '2026-12-31'}


def test_loans_outstanding_without_as_of_leaves_it_to_the_backend(tools, wire):
    tools['loans_outstanding'](immobilie_ids=['i-1'], **CREDS)

    assert _body(_only(wire)) == {'immobilie_ids': ['i-1']}


# ---------------------------------------------------------------------------
# Immobilien search: repeated query parameters, not comma-joined values
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    'status_ids, tag_ids',
    [
        (['s-1', 's-2'], ['t-1']),
        ('s-1,s-2', 't-1'),
        ('["s-1", "s-2"]', '["t-1"]'),
    ],
)
def test_immobilien_search_repeats_status_and_tag_ids(tools, wire, status_ids, tag_ids):
    tools['immobilien_search'](search='Berlin', status_ids=status_ids, tag_ids=tag_ids, **CREDS)

    req = _only(wire)
    assert req.url.path == '/api/v2/immobilien/search'
    assert req.url.params.get_list('status_ids') == ['s-1', 's-2']
    assert req.url.params.get_list('tag_ids') == ['t-1']
    assert req.url.params['search'] == 'Berlin'


# ---------------------------------------------------------------------------
# Activities, contacts, documents
# ---------------------------------------------------------------------------

def test_activities_structure_description_sends_description(tools, wire):
    tools['activities_structure_description'](text='Anruf mit Makler, Rückruf Freitag', **CREDS)

    req = _only(wire)
    assert req.url.path == '/api/activities/structure-description'
    assert _body(req) == {'description': 'Anruf mit Makler, Rückruf Freitag'}


def test_contacts_bulk_delete_sends_ids(tools, wire):
    tools['contacts_bulk_delete'](contact_ids=['c-1', 'c-2'], **CREDS)

    req = _only(wire)
    assert req.url.path == '/api/contacts/bulk-delete'
    assert _body(req) == {'ids': ['c-1', 'c-2']}


def test_contacts_merge_restore_sends_log_id(tools, wire):
    assert 'merge_id' not in _params(tools['contacts_merge_restore'])

    tools['contacts_merge_restore'](log_id='log-1', **CREDS)

    req = _only(wire)
    assert req.url.path == '/api/contacts/merge/restore'
    assert _body(req) == {'log_id': 'log-1'}


def test_documents_rename_sends_new_filename(tools, wire):
    tools['documents_rename'](document_id='doc-1', name='Grundbuch.pdf', **CREDS)

    req = _only(wire)
    assert req.method == 'PUT'
    assert req.url.path == '/api/documents/documents/doc-1/rename'
    assert _body(req) == {'new_filename': 'Grundbuch.pdf'}


def test_documents_list_sends_immobilien_id_and_promises_no_pagination(tools, wire):
    params = _params(tools['documents_list'])
    assert not {'page', 'per_page'} & params

    tools['documents_list'](immobilie_id='i-1', **CREDS)

    req = _only(wire)
    assert req.url.path == '/api/documents/documents'
    assert dict(req.url.params) == {'immobilien_id': 'i-1'}


def test_documents_list_requires_a_property(tools, wire):
    with pytest.raises(ValueError, match='immobilie_id'):
        tools['documents_list'](**CREDS)
    assert wire == []


# ---------------------------------------------------------------------------
# E-Mail folders: addressed by name, there is no folder id
# ---------------------------------------------------------------------------

def test_email_rename_folder_sends_old_and_new_name(tools, wire):
    assert 'folder_id' not in _params(tools['email_rename_folder'])

    tools['email_rename_folder'](old_name='Ankauf', new_name='Ankauf 2026', **CREDS)

    req = _only(wire)
    assert req.url.path == '/api/email-messages/folders/rename'
    assert _body(req) == {'old_name': 'Ankauf', 'new_name': 'Ankauf 2026'}


def test_email_delete_folder_sends_name(tools, wire):
    assert 'folder_id' not in _params(tools['email_delete_folder'])

    tools['email_delete_folder'](name='Ankauf', **CREDS)

    req = _only(wire)
    assert req.url.path == '/api/email-messages/folders/delete'
    assert _body(req) == {'name': 'Ankauf'}
