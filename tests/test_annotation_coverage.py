"""Guardrail: every registered MCP tool must carry a valid ToolAnnotations.

Review criteria require `readOnlyHint=True` OR `destructiveHint` on each
tool.  This test fails if anyone reintroduces a bare `@mcp.tool()` without
annotations or forgets to classify a new tool.
"""

from __future__ import annotations

import pytest


def _iter_tools(mcp_instance):
    for name, tool in mcp_instance._tool_manager._tools.items():
        yield name, tool


@pytest.fixture(scope='module')
def full_tools():
    from mcp_immojump.server import mcp
    return list(_iter_tools(mcp))


def test_every_tool_has_annotations(full_tools) -> None:
    missing = [name for name, tool in full_tools if tool.annotations is None]
    assert not missing, f'Tools without annotations: {missing}'


def test_every_tool_has_read_or_destructive_hint(full_tools) -> None:
    offenders = []
    for name, tool in full_tools:
        ann = tool.annotations
        if ann is None:
            offenders.append(name)
            continue
        # readOnlyHint=True OR destructiveHint set (True or False is fine,
        # the rule is "hint present").  Our helpers always set one of them.
        has_read = ann.readOnlyHint is True
        has_destructive = ann.destructiveHint is not None
        if not (has_read or has_destructive):
            offenders.append(name)
    assert not offenders, (
        f'Tools missing readOnlyHint=True or destructiveHint: {offenders}'
    )


def test_read_only_and_destructive_are_mutually_exclusive(full_tools) -> None:
    """A tool marked read-only must not also claim to be destructive."""
    offenders = []
    for name, tool in full_tools:
        ann = tool.annotations
        if ann.readOnlyHint is True and ann.destructiveHint is True:
            offenders.append(name)
    assert not offenders, f'Tools both read-only and destructive: {offenders}'


def test_tool_names_are_within_spec_length(full_tools) -> None:
    # MCP directory review rejects tool names longer than 64 characters.
    too_long = [name for name, _ in full_tools if len(name) > 64]
    assert not too_long, f'Tool names exceed 64 chars: {too_long}'


def test_every_tool_has_description(full_tools) -> None:
    # Review requires human-readable descriptions; empty strings also fail.
    missing = [name for name, tool in full_tools if not (tool.description or '').strip()]
    assert not missing, f'Tools missing description: {missing}'
