"""Verify server tiers and domain servers register expected tool counts."""


def _tool_count(mcp_instance) -> int:
    return len(mcp_instance._tool_manager._tools)


def _tool_names(mcp_instance) -> set[str]:
    return set(mcp_instance._tool_manager._tools.keys())


# ---------------------------------------------------------------------------
# Tier-based servers (user-facing)
# ---------------------------------------------------------------------------

def test_standard_server_tool_count():
    from mcp_immojump.servers.standard import mcp
    assert _tool_count(mcp) == 87


def test_profi_server_tool_count():
    from mcp_immojump.servers.profi import mcp
    assert _tool_count(mcp) == 129


def test_full_server_tool_count():
    from mcp_immojump.server import mcp
    assert _tool_count(mcp) == 170


def test_standard_is_subset_of_profi():
    from mcp_immojump.servers.standard import mcp as std
    from mcp_immojump.servers.profi import mcp as pro
    std_tools = _tool_names(std)
    pro_tools = _tool_names(pro)
    assert std_tools.issubset(pro_tools), f'Standard has tools not in Profi: {std_tools - pro_tools}'


def test_profi_is_subset_of_full():
    from mcp_immojump.servers.profi import mcp as pro
    from mcp_immojump.server import mcp as full
    pro_tools = _tool_names(pro)
    full_tools = _tool_names(full)
    assert pro_tools.issubset(full_tools), f'Profi has tools not in Full: {pro_tools - full_tools}'


def test_standard_has_core_tools():
    """Standard must include core investor workflow tools."""
    from mcp_immojump.servers.standard import mcp
    names = _tool_names(mcp)
    for tool in ['immobilien_list', 'contacts_create', 'activities_create',
                 'pipeline_list', 'documents_list', 'tags_list',
                 'activity_template_create', 'status_list']:
        assert tool in names, f'Standard missing core tool: {tool}'


def test_standard_excludes_profi_tools():
    """Standard must NOT include deals, tickets, milestones."""
    from mcp_immojump.servers.standard import mcp
    names = _tool_names(mcp)
    for tool in ['deals_list', 'tickets_create', 'milestones_create',
                 'custom_fields_definitions_list', 'email_list']:
        assert tool not in names, f'Standard should not have profi tool: {tool}'


def test_every_tier_includes_connection_test():
    from mcp_immojump.servers.standard import mcp as std
    from mcp_immojump.servers.profi import mcp as pro
    from mcp_immojump.server import mcp as full
    for name, srv in [('standard', std), ('profi', pro), ('full', full)]:
        assert 'connection_test' in _tool_names(srv), f'{name} missing connection_test'


# ---------------------------------------------------------------------------
# Domain-based servers (advanced use)
# ---------------------------------------------------------------------------

def test_properties_server_tool_count():
    from mcp_immojump.servers.properties import mcp
    assert _tool_count(mcp) == 39


def test_crm_server_tool_count():
    from mcp_immojump.servers.crm import mcp
    assert _tool_count(mcp) == 37


def test_pipeline_server_tool_count():
    from mcp_immojump.servers.pipeline import mcp
    assert _tool_count(mcp) == 39


def test_org_server_tool_count():
    from mcp_immojump.servers.org import mcp
    assert _tool_count(mcp) == 58


def test_no_tool_overlap_between_domain_servers():
    """Domain servers should not share tools (except connection_test)."""
    from mcp_immojump.servers.properties import mcp as p
    from mcp_immojump.servers.crm import mcp as c
    from mcp_immojump.servers.pipeline import mcp as pl
    from mcp_immojump.servers.org import mcp as o

    servers = [
        ('properties', _tool_names(p) - {'connection_test'}),
        ('crm', _tool_names(c) - {'connection_test'}),
        ('pipeline', _tool_names(pl) - {'connection_test'}),
        ('org', _tool_names(o) - {'connection_test'}),
    ]
    for idx, (name_a, tools_a) in enumerate(servers):
        for name_b, tools_b in servers[idx + 1:]:
            overlap = tools_a & tools_b
            assert not overlap, f'{name_a} and {name_b} share tools: {overlap}'


def test_domain_servers_cover_all_full_tools():
    """The union of all domain servers must equal the full server."""
    from mcp_immojump.servers.properties import mcp as p
    from mcp_immojump.servers.crm import mcp as c
    from mcp_immojump.servers.pipeline import mcp as pl
    from mcp_immojump.servers.org import mcp as o
    from mcp_immojump.server import mcp as mono

    union = _tool_names(p) | _tool_names(c) | _tool_names(pl) | _tool_names(o)
    mono_names = _tool_names(mono)
    assert union == mono_names, f'Missing: {mono_names - union}, Extra: {union - mono_names}'
