"""End-to-end tests simulating real investor scenarios via MCP.

These tests call the LIVE MCP server at mcp.immojump.de (or localhost)
and exercise the same tool calls that ChatGPT/Claude would make.
Each test maps to a concrete example from the customer-facing blog post.

Run with: pytest tests/test_e2e_investor_scenarios.py -v --e2e
Skip in CI (no --e2e flag): these tests are skipped by default.
"""

import json
import os
import time

import httpx
import pytest

MCP_URL = os.getenv('MCP_TEST_URL', 'https://mcp.immojump.de/mcp')
TOKEN = os.getenv('MCP_TEST_TOKEN', '')
ORG_ID = os.getenv('MCP_TEST_ORG_ID', '')

pytestmark = pytest.mark.skipif(
    not os.getenv('MCP_E2E'),
    reason='Set MCP_E2E=1 MCP_TEST_TOKEN=... MCP_TEST_ORG_ID=... to run',
)


class MCPClient:
    """Minimal MCP client for testing."""

    def __init__(self, url: str, token: str, org_id: str):
        self.url = url
        self.token = token
        self.org_id = org_id
        self.session_id = None
        self._id = 0
        self.client = httpx.Client(timeout=30)

    def _headers(self):
        h = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'Authorization': f'Bearer {self.token}',
            'X-Organisation-Id': self.org_id,
        }
        if self.session_id:
            h['Mcp-Session-Id'] = self.session_id
        return h

    def initialize(self):
        self._id += 1
        resp = self.client.post(self.url, headers=self._headers(), json={
            'jsonrpc': '2.0', 'id': self._id, 'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'e2e-test', 'version': '1.0'},
            },
        })
        assert resp.status_code == 200
        # Extract session ID from header
        self.session_id = resp.headers.get('mcp-session-id')
        # Parse SSE response
        return self._parse_sse(resp.text)

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        self._id += 1
        resp = self.client.post(self.url, headers=self._headers(), json={
            'jsonrpc': '2.0', 'id': self._id,
            'method': 'tools/call',
            'params': {'name': name, 'arguments': arguments or {}},
        })
        assert resp.status_code == 200
        return self._parse_sse(resp.text)

    def _parse_sse(self, text: str) -> dict:
        for line in text.split('\n'):
            if line.startswith('data: '):
                return json.loads(line[6:])
        raise ValueError(f'No data line in SSE response: {text[:200]}')

    def tool_result(self, resp: dict) -> dict:
        """Extract the tool result from an MCP response."""
        content = resp.get('result', {}).get('content', [])
        for item in content:
            if item.get('type') == 'text':
                return json.loads(item['text'])
        return {}

    def close(self):
        self.client.close()


@pytest.fixture(scope='module')
def mcp():
    client = MCPClient(MCP_URL, TOKEN, ORG_ID)
    client.initialize()
    yield client
    client.close()


# ---------------------------------------------------------------------------
# Alltag als Investor
# ---------------------------------------------------------------------------

class TestAlltag:
    def test_portfolio_count(self, mcp):
        """'Wie viele Immobilien habe ich im Portfolio?'"""
        resp = mcp.call_tool('immobilien_count')
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        assert isinstance(result['result']['count'], int)
        print(f"  → {result['result']['count']} Immobilien")

    def test_create_contact(self, mcp):
        """'Erstelle einen Kontakt: Thomas Müller, 0221-12345, mueller@immo.de'"""
        resp = mcp.call_tool('contacts_create', {
            'data': {
                'first_name': 'Thomas',
                'last_name': 'Müller-E2E-Test',
                'phone': '0221-12345',
                'email': 'mueller-e2e@test.example.com',
                'company': 'E2E Test Makler',
            },
        })
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        contact = result['result']
        # Response may have 'contact' wrapper or direct fields
        if 'contact' in contact:
            contact = contact['contact']
        assert 'id' in contact
        print(f"  → Kontakt erstellt: {contact.get('id')}")
        self.__class__._contact_id = contact.get('id')

    def test_create_activity_for_besichtigung(self, mcp):
        """'Ich hatte eine Besichtigung. Erstelle mir eine Aktivität dazu.'"""
        resp = mcp.call_tool('activities_create', {
            'data': {
                'title': 'Besichtigung Berliner Str. 42',
                'type': 'BESICHTIGUNG',
                'description': 'Besichtigung mit Makler Müller. Objekt ist interessant.',
                'status': 'Abgeschlossen',
                'priority': 'Mittel',
            },
        })
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        print(f"  → Aktivität erstellt: {result['result'].get('id')}")
        self.__class__._activity_id = result['result'].get('id')

    def test_search_immobilien(self, mcp):
        """'Zeig mir alle Objekte unter 200.000€'"""
        resp = mcp.call_tool('immobilien_search', {
            'search': 'Berlin',
            'per_page': 5,
        })
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        print(f"  → {len(result['result'].get('items', []))} Ergebnisse")

    def test_pipeline_overview(self, mcp):
        """'Zeig mir meine Pipelines'"""
        resp = mcp.call_tool('pipeline_list')
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        pipelines = result['result']
        assert isinstance(pipelines, list)
        for p in pipelines[:3]:
            print(f"  → {p['name']}: {p.get('status_count', '?')} Phasen, {p.get('active_items_count', '?')} Items")

    def test_deals_by_status(self, mcp):
        """'Welche Deals sind im Notartermin?'"""
        resp = mcp.call_tool('deals_list', {'per_page': 5})
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        print(f"  → Deals geladen")

    def test_create_ticket(self, mcp):
        """'Erstelle ein Ticket: Mieterwechsel in WE3'"""
        resp = mcp.call_tool('tickets_create', {
            'data': {
                'title': 'E2E Test: Mieterwechsel WE3',
                'description': 'Mieterwechsel in WE3, Berliner Str. 42',
                'priority': 'medium',
            },
        })
        result = mcp.tool_result(resp)
        # tickets_create may set organisation_id automatically from header
        assert result['ok'] is True
        ticket = result['result']
        assert 'id' in ticket
        print(f"  → Ticket erstellt: {ticket.get('id')}")
        self.__class__._ticket_id = ticket.get('id')


# ---------------------------------------------------------------------------
# Ankauf & Due Diligence
# ---------------------------------------------------------------------------

class TestAnkauf:
    def test_create_immobilie(self, mcp):
        """'Lege ein neues Objekt an: MFH, Aachen, Roermonder Str. 15, 380k'"""
        resp = mcp.call_tool('immobilien_create', {
            'data': {
                'title': 'E2E Test MFH Aachen',
                'strasse': 'Roermonder Str.',
                'hausnummer': '15',
                'plz': '52072',
                'ort': 'Aachen',
                'kaufpreis': 380000,
                'immobilie_type': 'MFH',
            },
        })
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        immo = result['result']
        assert 'id' in immo
        print(f"  → Immobilie erstellt: {immo['id']}")
        self.__class__._immo_id = immo['id']

    def test_create_milestone(self, mcp):
        """'Erstelle einen Milestone: Notartermin am 15.06.2026'"""
        immo_id = getattr(self.__class__, '_immo_id', None)
        if not immo_id:
            pytest.skip('No immobilie from previous test')
        resp = mcp.call_tool('milestones_create', {
            'immobilie_id': immo_id,
            'data': {
                'type': 'NOTAR_BEURKUNDUNG',
                'date': '2026-06-15',
                'title': 'E2E Test Notartermin',
            },
        })
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        print(f"  → Milestone erstellt")

    def test_overdue_activities(self, mcp):
        """'Was steht als nächstes an? Zeig mir überfällige Aufgaben.'"""
        resp = mcp.call_tool('activities_statistics')
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        stats = result['result']
        print(f"  → Überfällig: {stats.get('overdue', 0)}, Diese Woche: {stats.get('due_week', 0)}")

    def test_valuation_providers(self, mcp):
        """'Fordere eine Bewertung an' — first check providers"""
        resp = mcp.call_tool('valuation_providers')
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        print(f"  → Bewertungs-Provider geladen")

    def test_document_list(self, mcp):
        """'Analysiere das Dokument...' — list docs for an existing property"""
        # Use immobilien_list to get a property that might have documents
        resp = mcp.call_tool('immobilien_list', {'per_page': 1})
        result = mcp.tool_result(resp)
        items = result['result'].get('items', [])
        if not items:
            pytest.skip('No immobilien available')
        immo_id = items[0]['id']
        resp2 = mcp.call_tool('documents_list', {'immobilie_id': immo_id, 'per_page': 5})
        result2 = mcp.tool_result(resp2)
        assert result2['ok'] is True
        print(f"  → Dokumente für {immo_id} geladen")

    def test_duplicate_immobilie(self, mcp):
        """'Dupliziere das Objekt als Vergleichsrechnung'"""
        immo_id = getattr(self.__class__, '_immo_id', None)
        if not immo_id:
            pytest.skip('No immobilie from previous test')
        resp = mcp.call_tool('immobilien_duplicate', {'immobilie_id': immo_id})
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        print(f"  → Duplikat erstellt: {result['result'].get('id')}")
        self.__class__._dup_id = result['result'].get('id')


# ---------------------------------------------------------------------------
# Team & Organisation
# ---------------------------------------------------------------------------

class TestTeam:
    def test_organisation_members(self, mcp):
        """'Lade meinen Partner ein' — first check members"""
        resp = mcp.call_tool('organisation_members', {'org_id': ORG_ID})
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        print(f"  → Mitglieder geladen")

    def test_feed_create_post(self, mcp):
        """'Schreib im Team-Feed: Objekt in Aachen ist raus.'"""
        resp = mcp.call_tool('feed_create_post', {
            'data': {
                'text': 'E2E Test: Objekt in Aachen ist raus, zu teuer.',
            },
        })
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        print(f"  → Feed-Post erstellt")

    def test_email_list(self, mcp):
        """'Zeig mir meine ungelesenen E-Mails'"""
        resp = mcp.call_tool('email_list', {'per_page': 5})
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        print(f"  → E-Mails geladen")

    def test_contacts_search(self, mcp):
        """'Suche in meinen Kontakten nach allen Maklern in Köln'"""
        resp = mcp.call_tool('contacts_list', {'search': 'Köln', 'per_page': 5})
        result = mcp.tool_result(resp)
        assert result['ok'] is True
        print(f"  → Kontakte durchsucht")


# ---------------------------------------------------------------------------
# Cleanup — delete test data
# ---------------------------------------------------------------------------

class TestCleanup:
    def test_delete_test_activity(self, mcp):
        aid = getattr(TestAlltag, '_activity_id', None)
        if aid:
            resp = mcp.call_tool('activities_delete', {'activity_id': aid})
            print(f"  → Aktivität gelöscht: {aid}")

    def test_delete_test_contact(self, mcp):
        cid = getattr(TestAlltag, '_contact_id', None)
        if cid:
            resp = mcp.call_tool('contacts_delete', {'contact_id': cid})
            print(f"  → Kontakt gelöscht: {cid}")

    def test_delete_test_ticket(self, mcp):
        tid = getattr(TestAlltag, '_ticket_id', None)
        if tid:
            resp = mcp.call_tool('tickets_delete', {'ticket_id': tid})
            print(f"  → Ticket gelöscht: {tid}")

    def test_delete_test_duplicate(self, mcp):
        did = getattr(TestAnkauf, '_dup_id', None)
        if did:
            resp = mcp.call_tool('immobilien_delete', {'immobilie_id': did})
            print(f"  → Duplikat gelöscht: {did}")

    def test_delete_test_immobilie(self, mcp):
        iid = getattr(TestAnkauf, '_immo_id', None)
        if iid:
            resp = mcp.call_tool('immobilien_delete', {'immobilie_id': iid})
            print(f"  → Immobilie gelöscht: {iid}")
