"""pipeline_update and status_update must name the backend's structural rules.

Since immo-calc#1854 the backend guards two structural changes:

- Changing a pipeline's entity_type needs an organisation admin and only
  works while every status of the pipeline already has the new type (empty
  pipeline, or repairing one whose statuses were created for that type).
  Otherwise PUT /api/pipelines/pipelines/<id> answers 400 and changes nothing.
  Before, any member could switch the type; every status of the pipeline then
  stopped being assignable.
- PUT /api/statuses/statuses/<id> with pipeline_id only moves a status into a
  pipeline of the same organisation and the same entity type (400 otherwise).

An agent that does not know this retries the type switch or tries to move
statuses across organisations instead of creating a new pipeline.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope='module')
def tools():
    from mcp_immojump.server import mcp
    return dict(mcp._tool_manager._tools.items())


def test_pipeline_update_names_the_entity_type_rules(tools) -> None:
    description = tools['pipeline_update'].description
    for phrase in ('entity_type', 'admin', 'every status', '400', 'new pipeline'):
        assert phrase in description, f'pipeline_update does not mention {phrase!r}'


def test_status_update_names_the_pipeline_move_rules(tools) -> None:
    description = tools['status_update'].description
    for phrase in ('pipeline_id', 'same organisation', 'same entity type', '400'):
        assert phrase in description, f'status_update does not mention {phrase!r}'
