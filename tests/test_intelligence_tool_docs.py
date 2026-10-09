"""The property-intelligence routes answer a wrong value only with a generic 400
("Bitte gültige Einstellungen angeben."), so the tool descriptions must name the
accepted keys and values (immo-calc modules/routes/property_intelligence_routes.py)."""

from mcp.server.fastmcp import FastMCP

from mcp_immojump.tools import immobilien


def _tools():
    server = FastMCP('docs')
    immobilien.register(server)
    return server._tool_manager._tools


def test_settings_tool_names_keys_and_values():
    description = _tools()['property_intelligence_settings'].description
    for needle in ('profile_id', 'phase', '"initial"', '"purchase"', 'checklist', 'extra_categories',
                   'target_yield', '1 to 15', 'not_relevant', 'grundbuch', 'hausgeldabrechnung'):
        assert needle in description, needle


def test_decide_tool_names_the_note_limit():
    description = _tools()['property_intelligence_decide'].description
    assert 'note' in description
    assert '2000' in description


def test_patch_tool_does_not_claim_a_text_status_is_rejected():
    description = _tools()['immobilien_patch'].description
    assert 'STATUS_VIA_PUT' in description
    assert 'dropped with a' in description
