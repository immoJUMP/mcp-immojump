"""Contact and tag tools must name the fields and values the backend accepts.

Customer report (JTBH, 2026-10-09): contacts_create advertised "position" and
"tags"; the backend answered "Unknown field" for both. There is no position
field (the function of a contact lives in "role"), and tags are set via
"tag_ids". contacts_update promised a full replace although the backend PUT
is partial. tags_update_entity named "contact" and "deal" as entity types;
the route only knows immobilie, contacts and activities.

immo-calc now also accepts "tags" and the singular "contact"/"activity", but
the descriptions name the canonical forms so older backends keep working.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope='module')
def tools():
    from mcp_immojump.server import mcp
    return dict(mcp._tool_manager._tools.items())


def test_contacts_create_names_the_backend_fields(tools) -> None:
    description = tools['contacts_create'].description
    for field in ('first_name', 'last_name', 'email', 'role', 'company', 'tag_ids', 'status_id'):
        assert field in description, f'contacts_create does not name {field}'


def test_contacts_create_no_longer_advertises_position(tools) -> None:
    description = tools['contacts_create'].description
    assert 'company, position' not in description
    assert 'There is no "position" field' in description


def test_contacts_create_points_to_custom_fields_tool(tools) -> None:
    assert 'custom_fields_values_set' in tools['contacts_create'].description


def test_contacts_update_is_described_as_partial(tools) -> None:
    description = tools['contacts_update'].description
    assert 'full replace' not in description
    assert 'Omitted fields may be cleared' not in description
    assert 'unchanged' in description


@pytest.mark.parametrize('tool_name', ['tags_get_entity', 'tags_update_entity'])
def test_tag_entity_tools_name_the_routes_entity_types(tools, tool_name) -> None:
    description = tools[tool_name].description
    for value in ('immobilie', 'contacts', 'activities'):
        assert value in description, f'{tool_name} does not name {value}'
    assert 'deal' not in description


def test_custom_fields_values_set_names_the_400_for_unknown_ids(tools) -> None:
    """immo-calc lehnt unbekannte Feld-IDs seit 13.10.2026 mit 400 ab (vorher still verworfen)."""
    description = tools['custom_fields_values_set'].description
    assert 'UNKNOWN_CUSTOM_FIELD' in description
    assert 'custom_fields_definitions_list' in description
