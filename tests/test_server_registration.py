"""Verify each domain server registers the expected number of tools."""


def _tool_count(mcp_instance) -> int:
    return len(mcp_instance._tool_manager._tools)


def _tool_names(mcp_instance) -> set[str]:
    return set(mcp_instance._tool_manager._tools.keys())


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


def test_investor_server_tool_count():
    from mcp_immojump.servers.investor import mcp
    assert _tool_count(mcp) == 27


def test_monolithic_server_tool_count():
    from mcp_immojump.server import mcp
    assert _tool_count(mcp) == 196


def test_every_server_includes_connection_test():
    from mcp_immojump.servers.properties import mcp as p
    from mcp_immojump.servers.crm import mcp as c
    from mcp_immojump.servers.pipeline import mcp as pl
    from mcp_immojump.servers.org import mcp as o
    from mcp_immojump.servers.investor import mcp as i

    for name, srv in [('properties', p), ('crm', c), ('pipeline', pl), ('org', o), ('investor', i)]:
        assert 'connection_test' in _tool_names(srv), f'{name} missing connection_test'


def test_no_tool_overlap_between_servers():
    """Domain servers should not share tools (except connection_test)."""
    from mcp_immojump.servers.properties import mcp as p
    from mcp_immojump.servers.crm import mcp as c
    from mcp_immojump.servers.pipeline import mcp as pl
    from mcp_immojump.servers.org import mcp as o
    from mcp_immojump.servers.investor import mcp as i

    servers = [
        ('properties', _tool_names(p) - {'connection_test'}),
        ('crm', _tool_names(c) - {'connection_test'}),
        ('pipeline', _tool_names(pl) - {'connection_test'}),
        ('org', _tool_names(o) - {'connection_test'}),
        ('investor', _tool_names(i) - {'connection_test'}),
    ]
    for idx, (name_a, tools_a) in enumerate(servers):
        for name_b, tools_b in servers[idx + 1:]:
            overlap = tools_a & tools_b
            assert not overlap, f'{name_a} and {name_b} share tools: {overlap}'


def test_domain_servers_cover_all_monolithic_tools():
    """The union of all domain servers must equal the monolithic server."""
    from mcp_immojump.servers.properties import mcp as p
    from mcp_immojump.servers.crm import mcp as c
    from mcp_immojump.servers.pipeline import mcp as pl
    from mcp_immojump.servers.org import mcp as o
    from mcp_immojump.servers.investor import mcp as i
    from mcp_immojump.server import mcp as mono

    union = _tool_names(p) | _tool_names(c) | _tool_names(pl) | _tool_names(o) | _tool_names(i)
    mono_names = _tool_names(mono)
    assert union == mono_names, f'Missing: {mono_names - union}, Extra: {union - mono_names}'
