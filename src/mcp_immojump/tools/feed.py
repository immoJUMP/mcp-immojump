from .._app import mcp, _call_with_client, _ok, _require_dict


@mcp.tool()
def feed_list(
    token,
    organisation_id,
    cursor=None,
    channel_id=None,
    limit=25,
    base_url=None,
):
    """List organisation feed posts with cursor-based pagination.

    - cursor: pagination cursor from previous response
    - channel_id: filter by channel
    """

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_list(
            cursor=cursor, channel_id=channel_id, limit=int(limit),
        ),
    )
    return _ok(result)


@mcp.tool()
def feed_by_context(
    context_type,
    context_id,
    token,
    organisation_id,
    base_url=None,
):
    """Get feed posts for a specific context (property, contact, deal).

    - context_type: immobilie, contact, deal, etc.
    - context_id: the entity UUID
    """

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_by_context(
            context_type=context_type, context_id=context_id,
        ),
    )
    return _ok(result)


@mcp.tool()
def feed_create_post(
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Create a new feed post.

    data: {"text": "...", "channel_id": "..."} (optional: mentions, attachments).
    """

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_create_post(data=payload),
    )
    return _ok(result)


@mcp.tool()
def feed_edit_post(
    event_id,
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Edit an existing feed post."""

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_edit_post(event_id=event_id, data=payload),
    )
    return _ok(result)


@mcp.tool()
def feed_toggle_reaction(
    event_id,
    emoji,
    token,
    organisation_id,
    base_url=None,
):
    """Toggle an emoji reaction on a feed post."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_toggle_reaction(event_id=event_id, emoji=emoji),
    )
    return _ok(result)


@mcp.tool()
def feed_list_comments(
    event_id,
    token,
    organisation_id,
    base_url=None,
):
    """List comments on a feed post."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_list_comments(event_id=event_id),
    )
    return _ok(result)


@mcp.tool()
def feed_add_comment(
    event_id,
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Add a comment to a feed post.

    data: {"text": "..."}.
    """

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_add_comment(event_id=event_id, data=payload),
    )
    return _ok(result)


@mcp.tool()
def feed_edit_comment(
    comment_id,
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Edit a comment on a feed post."""

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_edit_comment(comment_id=comment_id, data=payload),
    )
    return _ok(result)


@mcp.tool()
def feed_delete_comment(
    comment_id,
    token,
    organisation_id,
    base_url=None,
):
    """Delete a comment from a feed post."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_delete_comment(comment_id=comment_id),
    )
    return _ok(result)


@mcp.tool()
def feed_comment_object(
    data,
    token,
    organisation_id,
    base_url=None,
):
    """Comment on a specific object (property, contact, deal).

    data: {"context_type": "immobilie", "context_id": "...", "text": "..."}.
    """

    payload = _require_dict(field_name='data', value=data)
    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_comment_object(data=payload),
    )
    return _ok(result)


@mcp.tool()
def feed_channels(
    token,
    organisation_id,
    base_url=None,
):
    """List feed channels for the organisation."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_channels(),
    )
    return _ok(result)


@mcp.tool()
def feed_create_channel(
    name,
    token,
    organisation_id,
    base_url=None,
):
    """Create a new feed channel."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_create_channel(name=name),
    )
    return _ok(result)


@mcp.tool()
def feed_rename_channel(
    channel_id,
    name,
    token,
    organisation_id,
    base_url=None,
):
    """Rename a feed channel."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_rename_channel(channel_id=channel_id, name=name),
    )
    return _ok(result)


@mcp.tool()
def feed_delete_channel(
    channel_id,
    token,
    organisation_id,
    base_url=None,
):
    """Delete a feed channel."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.feed_delete_channel(channel_id=channel_id),
    )
    return _ok(result)
