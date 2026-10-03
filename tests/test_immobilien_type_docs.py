"""Property tools must name the property types the backend accepts.

``type`` is free text from the model's point of view. Without the allowed
codes in the tool description, agents guessed "Wohnung" — and
POST /api/v2/immobilien failed with HTTP 500 at the database enum. The
backend now answers 400 with ``valid_values``; the description saves the
round trip.
"""

from __future__ import annotations

import pytest

PROPERTY_TYPE_CODES = ('ETW', 'EFH', 'MFH', 'WGH', 'GEW', 'Sonstiges')


@pytest.fixture(scope='module')
def tools():
    from mcp_immojump.server import mcp
    return dict(mcp._tool_manager._tools.items())


@pytest.mark.parametrize('tool_name', ['immobilien_create', 'immobilien_patch'])
def test_property_write_tools_name_every_allowed_type(tools, tool_name) -> None:
    description = tools[tool_name].description
    missing = [code for code in PROPERTY_TYPE_CODES if code not in description]
    assert not missing, f'{tool_name} does not name the property types {missing}'


def test_create_tells_the_model_that_property_data_goes_into_daten(tools) -> None:
    """POST reads name, type, daten and status_id; other top-level keys are dropped."""
    assert 'daten' in tools['immobilien_create'].description
