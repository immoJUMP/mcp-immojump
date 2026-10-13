"""Property tools must call the living area by the name the backend routes.

PATCH /api/v2/immobilien/<id> writes ``qm`` (and the rents) into the property's
unit, because the calculation reads the units. The patch description used to
advertise ``{"kaufpreis": 350000, "wohnflaeche": 85}``; ``wohnflaeche`` ended up
in ``daten.wohnflaeche``, which the calculation never reads (finding
2026-10-13). immo-calc now also reads ``wohnflaeche`` as ``qm``, but the
description names the canonical key so older backends keep working.
"""

from __future__ import annotations

import re

import pytest

AREA_FIELD_ALIAS = re.compile(r'\bwohnflaeche\b')


@pytest.fixture(scope='module')
def tools():
    from mcp_immojump.server import mcp
    return dict(mcp._tool_manager._tools.items())


@pytest.mark.parametrize('tool_name', ['immobilien_create', 'immobilien_patch'])
def test_property_write_tools_name_qm_for_the_living_area(tools, tool_name) -> None:
    description = tools[tool_name].description
    assert '"qm"' in description, f'{tool_name} does not name qm'
    assert not AREA_FIELD_ALIAS.search(description), f'{tool_name} still advertises wohnflaeche'


def test_patch_says_area_and_rents_go_into_the_unit(tools) -> None:
    description = tools['immobilien_patch'].description
    for field in ('qm', 'ist_miete', 'soll_miete'):
        assert field in description, f'immobilien_patch does not name {field}'
    assert 'units_update' in description
