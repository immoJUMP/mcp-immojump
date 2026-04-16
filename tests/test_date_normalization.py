"""Thorough tests for date/datetime normalization across all domains.

The backend expects DateTime(tz) columns as full ISO datetime strings and
Date columns as "YYYY-MM-DD".  LLMs commonly send date-only strings like
"2026-04-23" for datetime fields or full datetimes for date-only fields.

The client must normalize these before forwarding to the API.
"""

import json

import httpx

from mcp_immojump.client import (
    ImmojumpAPIClient,
    ImmojumpCredentials,
    _normalize_datetime,
    _normalize_date_only,
    _normalize_payload_dates,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _creds():
    return ImmojumpCredentials(
        base_url='http://localhost:8081', token='tok', organisation_id='org-1',
    )


def _capture_client(handler):
    transport = httpx.MockTransport(handler)
    return ImmojumpAPIClient(_creds(), transport=transport)


def _json_capture():
    """Return (captured_dict, handler) — handler stores request JSON in captured['json']."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured['json'] = json.loads(req.read())
        return httpx.Response(200, json={})

    return captured, handler


# ═══════════════════════════════════════════════════════════════════════════
# Unit tests for normalization helpers
# ═══════════════════════════════════════════════════════════════════════════


class TestNormalizeDatetime:
    """_normalize_datetime: date-only -> midnight UTC, ISO -> UTC, passthrough."""

    def test_date_only_expanded(self):
        assert _normalize_datetime('2026-04-23') == '2026-04-23T00:00:00+00:00'

    def test_iso_with_z_suffix(self):
        assert _normalize_datetime('2026-04-23T09:00:00Z') == '2026-04-23T09:00:00+00:00'

    def test_iso_with_offset(self):
        assert _normalize_datetime('2026-04-23T11:00:00+02:00') == '2026-04-23T09:00:00+00:00'

    def test_iso_without_tz_gets_utc(self):
        assert _normalize_datetime('2026-04-23T09:00:00') == '2026-04-23T09:00:00+00:00'

    def test_none_passthrough(self):
        assert _normalize_datetime(None) is None

    def test_empty_string_passthrough(self):
        assert _normalize_datetime('') == ''

    def test_whitespace_passthrough(self):
        assert _normalize_datetime('   ') == '   '

    def test_non_string_passthrough(self):
        assert _normalize_datetime(12345) == 12345

    def test_unparseable_passthrough(self):
        assert _normalize_datetime('not-a-date') == 'not-a-date'

    def test_already_utc_iso(self):
        val = '2026-12-31T23:59:59+00:00'
        assert _normalize_datetime(val) == val


class TestNormalizeDateOnly:
    """_normalize_date_only: keeps YYYY-MM-DD, truncates full datetimes."""

    def test_date_only_kept(self):
        assert _normalize_date_only('2026-04-23') == '2026-04-23'

    def test_datetime_truncated(self):
        assert _normalize_date_only('2026-04-23T09:00:00Z') == '2026-04-23'

    def test_datetime_with_offset_truncated(self):
        # For date-only fields the user's local date matters, not UTC conversion.
        # "2026-04-23T01:00:00+02:00" means "April 23rd" to the user.
        assert _normalize_date_only('2026-04-23T01:00:00+02:00') == '2026-04-23'

    def test_none_passthrough(self):
        assert _normalize_date_only(None) is None

    def test_empty_string_passthrough(self):
        assert _normalize_date_only('') == ''

    def test_non_string_passthrough(self):
        assert _normalize_date_only(42) == 42

    def test_unparseable_passthrough(self):
        assert _normalize_date_only('nope') == 'nope'


class TestNormalizePayloadDates:
    """_normalize_payload_dates: in-place normalization of multiple fields."""

    def test_datetime_fields_normalized(self):
        payload = {'due_date': '2026-04-23', 'title': 'Test'}
        _normalize_payload_dates(payload, datetime_fields=('due_date',))
        assert payload['due_date'] == '2026-04-23T00:00:00+00:00'
        assert payload['title'] == 'Test'

    def test_date_fields_normalized(self):
        payload = {'start_date': '2026-04-23T09:00:00Z', 'amount': 100}
        _normalize_payload_dates(payload, date_fields=('start_date',))
        assert payload['start_date'] == '2026-04-23'
        assert payload['amount'] == 100

    def test_missing_fields_ignored(self):
        payload = {'title': 'Test'}
        _normalize_payload_dates(payload, datetime_fields=('due_date',), date_fields=('start_date',))
        assert payload == {'title': 'Test'}

    def test_mixed_fields(self):
        payload = {'due_date': '2026-05-01', 'start_date': '2026-05-01T00:00:00Z'}
        _normalize_payload_dates(
            payload,
            datetime_fields=('due_date',),
            date_fields=('start_date',),
        )
        assert payload['due_date'] == '2026-05-01T00:00:00+00:00'
        assert payload['start_date'] == '2026-05-01'


# ═══════════════════════════════════════════════════════════════════════════
# Integration tests: each domain's client methods normalize correctly
# ═══════════════════════════════════════════════════════════════════════════


# ── Activities (already fixed, regression tests) ──

class TestActivitiesDateNormalization:

    def test_create_date_only(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.activities_create(data={'title': 'T', 'due_date': '2026-04-23'})
        assert captured['json']['due_date'] == '2026-04-23T00:00:00+00:00'

    def test_create_iso_z(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.activities_create(data={'title': 'T', 'due_date': '2026-04-23T14:30:00Z'})
        assert captured['json']['due_date'] == '2026-04-23T14:30:00+00:00'

    def test_create_no_due_date(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.activities_create(data={'title': 'T'})
        assert 'due_date' not in captured['json']

    def test_create_for_property_date_only(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.activities_create_for_property(
                immobilie_id='imm-1', data={'title': 'B', 'due_date': '2026-06-15'},
            )
        assert captured['json']['due_date'] == '2026-06-15T00:00:00+00:00'

    def test_update_date_only(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.activities_update(activity_id='a-1', data={'due_date': '2026-05-01'})
        assert captured['json']['due_date'] == '2026-05-01T00:00:00+00:00'


# ── Tickets ──

class TestTicketsDateNormalization:

    def test_create_date_only(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.tickets_create(data={'title': 'Bug', 'due_date': '2026-04-30'})
        assert captured['json']['due_date'] == '2026-04-30T00:00:00+00:00'

    def test_create_iso(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.tickets_create(data={'title': 'Bug', 'due_date': '2026-04-30T16:00:00+02:00'})
        assert captured['json']['due_date'] == '2026-04-30T14:00:00+00:00'

    def test_create_no_due_date(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.tickets_create(data={'title': 'Bug'})
        assert 'due_date' not in captured['json']

    def test_update_date_only(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.tickets_update(ticket_id='t-1', data={'due_date': '2026-05-15'})
        assert captured['json']['due_date'] == '2026-05-15T00:00:00+00:00'

    def test_update_preserves_other_fields(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.tickets_update(ticket_id='t-1', data={'title': 'Updated', 'due_date': '2026-05-15'})
        assert captured['json']['title'] == 'Updated'
        assert captured['json']['due_date'] == '2026-05-15T00:00:00+00:00'


# ── Deals ──

class TestDealsDateNormalization:

    def test_create_date_only(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.deals_create(data={'name': 'Deal', 'expected_close_date': '2026-06-01'})
        assert captured['json']['expected_close_date'] == '2026-06-01T00:00:00+00:00'

    def test_create_iso_z(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.deals_create(data={'name': 'Deal', 'expected_close_date': '2026-06-01T12:00:00Z'})
        assert captured['json']['expected_close_date'] == '2026-06-01T12:00:00+00:00'

    def test_create_no_date(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.deals_create(data={'name': 'Deal'})
        assert 'expected_close_date' not in captured['json']

    def test_update_date_only(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.deals_update(deal_id='d-1', data={'expected_close_date': '2026-07-15'})
        assert captured['json']['expected_close_date'] == '2026-07-15T00:00:00+00:00'


# ── Loans (Date-only columns — opposite problem) ──

class TestLoansDateNormalization:

    def test_create_date_only_kept(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.loans_create(data={'start_date': '2026-01-01', 'amount': 100000})
        assert captured['json']['start_date'] == '2026-01-01'

    def test_create_datetime_truncated_to_date(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.loans_create(data={'start_date': '2026-01-01T09:00:00Z', 'amount': 100000})
        assert captured['json']['start_date'] == '2026-01-01'

    def test_create_amortization_start_date(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.loans_create(data={
                'start_date': '2026-01-01',
                'amortization_start_date': '2026-07-01T00:00:00+02:00',
                'amount': 100000,
            })
        assert captured['json']['start_date'] == '2026-01-01'
        # For date-only fields, the input date part is preserved (user intent)
        assert captured['json']['amortization_start_date'] == '2026-07-01'

    def test_create_no_dates(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.loans_create(data={'amount': 100000})
        assert 'start_date' not in captured['json']
        assert 'amortization_start_date' not in captured['json']

    def test_update_date_only_kept(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.loans_update(loan_id='l-1', data={'start_date': '2026-02-01'})
        assert captured['json']['start_date'] == '2026-02-01'

    def test_update_datetime_truncated(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.loans_update(loan_id='l-1', data={'start_date': '2026-02-01T12:00:00Z'})
        assert captured['json']['start_date'] == '2026-02-01'

    def test_update_both_date_fields(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.loans_update(loan_id='l-1', data={
                'start_date': '2026-02-01T00:00:00Z',
                'amortization_start_date': '2026-08-01',
            })
        assert captured['json']['start_date'] == '2026-02-01'
        assert captured['json']['amortization_start_date'] == '2026-08-01'


# ── Milestones ──

class TestMilestonesDateNormalization:

    def test_create_date_field_date_only(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.milestones_create(immobilie_id='imm-1', data={
                'name': 'Notartermin', 'date': '2026-05-01',
            })
        assert captured['json']['date'] == '2026-05-01T00:00:00+00:00'

    def test_create_date_field_iso(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.milestones_create(immobilie_id='imm-1', data={
                'name': 'Notartermin', 'date': '2026-05-01T10:00:00+02:00',
            })
        assert captured['json']['date'] == '2026-05-01T08:00:00+00:00'

    def test_create_completed_at_date_only(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.milestones_create(immobilie_id='imm-1', data={
                'name': 'Abnahme', 'date': '2026-05-01', 'completed_at': '2026-05-02',
            })
        assert captured['json']['completed_at'] == '2026-05-02T00:00:00+00:00'

    def test_create_no_completed_at(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.milestones_create(immobilie_id='imm-1', data={
                'name': 'Termin', 'date': '2026-05-01',
            })
        assert 'completed_at' not in captured['json']

    def test_update_date_only(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.milestones_update(milestone_id='m-1', data={'date': '2026-06-01'})
        assert captured['json']['date'] == '2026-06-01T00:00:00+00:00'

    def test_update_completed_at(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.milestones_update(milestone_id='m-1', data={
                'completed_at': '2026-06-02T15:30:00Z',
            })
        assert captured['json']['completed_at'] == '2026-06-02T15:30:00+00:00'

    def test_update_both_fields(self):
        captured, handler = _json_capture()
        with _capture_client(handler) as client:
            client.milestones_update(milestone_id='m-1', data={
                'date': '2026-06-01',
                'completed_at': '2026-06-05',
            })
        assert captured['json']['date'] == '2026-06-01T00:00:00+00:00'
        assert captured['json']['completed_at'] == '2026-06-05T00:00:00+00:00'


# ═══════════════════════════════════════════════════════════════════════════
# Edge cases: ensure original data dict is NOT mutated
# ═══════════════════════════════════════════════════════════════════════════

class TestNoMutation:
    """Client methods must not mutate the caller's data dict."""

    def test_activities_create_no_mutation(self):
        _, handler = _json_capture()
        original = {'title': 'T', 'due_date': '2026-04-23'}
        with _capture_client(handler) as client:
            client.activities_create(data=original)
        assert original['due_date'] == '2026-04-23'

    def test_deals_update_no_mutation(self):
        _, handler = _json_capture()
        original = {'expected_close_date': '2026-06-01'}
        with _capture_client(handler) as client:
            client.deals_update(deal_id='d-1', data=original)
        assert original['expected_close_date'] == '2026-06-01'

    def test_loans_create_no_mutation(self):
        _, handler = _json_capture()
        original = {'start_date': '2026-01-01T09:00:00Z', 'amount': 100000}
        with _capture_client(handler) as client:
            client.loans_create(data=original)
        assert original['start_date'] == '2026-01-01T09:00:00Z'

    def test_milestones_create_no_mutation(self):
        _, handler = _json_capture()
        original = {'name': 'M', 'date': '2026-05-01', 'completed_at': '2026-05-02'}
        with _capture_client(handler) as client:
            client.milestones_create(immobilie_id='imm-1', data=original)
        assert original['date'] == '2026-05-01'
        assert original['completed_at'] == '2026-05-02'

    def test_tickets_update_no_mutation(self):
        _, handler = _json_capture()
        original = {'due_date': '2026-05-15'}
        with _capture_client(handler) as client:
            client.tickets_update(ticket_id='t-1', data=original)
        assert original['due_date'] == '2026-05-15'
