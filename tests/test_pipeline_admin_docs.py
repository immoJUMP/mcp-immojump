"""pipeline_create and pipeline_delete must say they need an admin.

Since immo-calc fix/pipeline-create-delete-admin the backend only lets
organisation admins create or delete a whole pipeline -- the same rule that
already applied to phases (statuses), activity templates, import and
copy/move. Every other member (including a bot token whose role carries
deny policies) gets 403 and nothing changes. Before, any member could delete
a pipeline: all properties were detached, phases and templates hard-deleted.

Renaming (pipeline_update with name) stays open to every member.

An agent that does not know this retries or reports a "bug" instead of
asking an admin.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope='module')
def tools():
    from mcp_immojump.server import mcp
    return dict(mcp._tool_manager._tools.items())


@pytest.mark.parametrize('tool_name', ['pipeline_create', 'pipeline_delete'])
def test_pipeline_structure_tools_name_the_admin_rule(tools, tool_name) -> None:
    description = tools[tool_name].description
    for phrase in ('organisation admin', '403'):
        assert phrase in description, f'{tool_name} does not mention {phrase!r}'


def test_pipeline_delete_names_what_is_lost(tools) -> None:
    description = tools['pipeline_delete'].description
    for phrase in ('detached', 'statuses', 'activity templates'):
        assert phrase in description, f'pipeline_delete does not mention {phrase!r}'
