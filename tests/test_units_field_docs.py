"""Unit tools must name the fields the backend actually reads.

POST /api/units/unit/<immobilie_id> and PUT /api/units/unit/<unit_id> read
einheit, livingspace, ist_rent, soll_rent, soll_rent2, rooms, type, note,
order, lease_start_date and last_rent_increase_date. Every other key is
dropped without an error. The descriptions used to advertise name,
wohnflaeche, miete_kalt, miete_ist, zimmer, stockwerk, leerstand and
unit_type — an agent following them got HTTP 201 and a unit with neither
area nor rent, and immobilien_split_units priced every split-off unit at 0.

The unit tools also have to warn about the empty default unit "Einheit 1"
that the backend adds to every new property: split along with the real
units, it becomes a property with purchase price 0.
"""

from __future__ import annotations

import pytest

BACKEND_FIELDS = (
    'einheit',
    'livingspace',
    'ist_rent',
    'soll_rent',
    'soll_rent2',
    'rooms',
    'type',
    'note',
    'order',
    'lease_start_date',
    'last_rent_increase_date',
)
UNIT_TYPES = ('wohnen', 'gewerbe', 'stellplatz', 'garage', 'sonstiges')
# Keys the old description advertised. The backend never read any of them.
IGNORED_KEYS = (
    'wohnflaeche',
    'miete_kalt',
    'miete_ist',
    'zimmer',
    'stockwerk',
    'leerstand',
    'unit_type',
)


@pytest.fixture(scope='module')
def tools():
    from mcp_immojump.server import mcp
    return dict(mcp._tool_manager._tools.items())


@pytest.mark.parametrize('tool_name', ['units_create', 'units_update'])
def test_unit_write_tools_name_every_backend_field(tools, tool_name) -> None:
    description = tools[tool_name].description
    missing = [field for field in BACKEND_FIELDS if field not in description]
    assert not missing, f'{tool_name} does not name the backend fields {missing}'


@pytest.mark.parametrize('tool_name', ['units_create', 'units_update'])
def test_unit_write_tools_name_every_unit_type(tools, tool_name) -> None:
    description = tools[tool_name].description
    missing = [value for value in UNIT_TYPES if value not in description]
    assert not missing, f'{tool_name} does not name the unit types {missing}'


@pytest.mark.parametrize('tool_name', ['units_create', 'units_update'])
def test_unit_write_tools_no_longer_advertise_ignored_keys(tools, tool_name) -> None:
    description = tools[tool_name].description
    advertised = [key for key in IGNORED_KEYS if key in description]
    assert not advertised, f'{tool_name} still advertises ignored keys {advertised}'


def _field_line(description: str, field: str) -> str:
    """The bullet that documents ``field``, including its wrapped continuation lines."""
    lines = description.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith(f'- {field}:'):
            indent = len(line) - len(line.lstrip())
            bullet = [line.strip()]
            for follow in lines[index + 1:]:
                follow_indent = len(follow) - len(follow.lstrip())
                if not follow.strip() or follow_indent <= indent:
                    break
                bullet.append(follow.strip())
            return ' '.join(bullet)
    raise AssertionError(f'no bullet for {field!r}')


@pytest.mark.parametrize('tool_name', ['units_create', 'units_update'])
def test_ist_rent_is_the_monthly_cold_rent(tools, tool_name) -> None:
    """Exposés list cold and warm rent; only the cold rent (Kaltmiete) belongs here."""
    assert 'Kaltmiete' in _field_line(tools[tool_name].description, 'ist_rent')


@pytest.mark.parametrize('tool_name', ['units_create', 'units_update'])
def test_livingspace_explains_split_and_parking(tools, tool_name) -> None:
    """immobilien_split_units shares the purchase price by livingspace, but only over
    residential/commercial area: a garage with m2 gets a share on top of the total."""
    line = _field_line(tools[tool_name].description, 'livingspace')
    assert 'immobilien_split_units' in line
    assert 'garage' in line
    assert 'stellplatz' in line


def test_units_list_warns_about_the_empty_default_unit(tools) -> None:
    """Agents take the IDs for immobilien_split_units from units_list. Every property
    created via immobilien_create carries an empty "Einheit 1" (0 m2); passed along,
    it becomes its own property with purchase price 0."""
    description = tools['units_list'].description
    for term in ('Einheit 1', 'immobilien_create', 'immobilien_split_units', 'units_update',
                 'units_delete'):
        assert term in description, f'units_list does not mention {term}'


def test_units_count_says_whose_units_it_counts(tools) -> None:
    """GET /api/units/units/count counts the units the calling user created, across all
    organisations; it ignores organisation_id and is no per-property count."""
    description = tools['units_count'].description
    assert 'created by' in description
    assert 'organisation_id' in description


def test_units_create_reuses_the_default_unit(tools) -> None:
    """Building an MFH unit by unit must fill "Einheit 1" instead of adding beside it."""
    description = tools['units_create'].description
    assert 'Einheit 1' in description
    assert 'units_update' in description


def test_units_create_order_defaults_to_the_end_of_the_rent_roll(tools) -> None:
    """Without order, POST /api/units/unit/<id> appends the unit after the existing ones
    (max(order)+1, immo-calc PR "neue Einheiten ohne order hinten anhängen"). The old
    "default 0" made agents expect the unit in front of "Einheit 1"."""
    line = _field_line(tools['units_create'].description, 'order')
    assert 'default 0' not in line
    assert 'end' in line
