from .._shared import _call_with_client, _ok, _require_dict, _require_list


def register(mcp):
    @mcp.tool()
    def tags_list(
        token,
        organisation_id,
        entity_type=None,
        base_url=None,
    ):
        """List tags for the organisation.

        - entity_type: optional filter (e.g. immobilie, contact, deal).
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.tags_list(entity_type=entity_type),
        )
        return _ok(result)

    @mcp.tool()
    def tags_create(
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Create a new tag.

        data: {"name": "...", "color": "#hex", "entity_type": "immobilie"}.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.tags_create(data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def tags_update(
        tag_id,
        data,
        token,
        organisation_id,
        base_url=None,
    ):
        """Update a tag (name, color)."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.tags_update(tag_id=tag_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def tags_delete(
        tag_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Delete a tag. Removes it from all tagged entities."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.tags_delete(tag_id=tag_id),
        )
        return _ok(result)

    @mcp.tool()
    def tags_get_entity(
        entity_type,
        entity_id,
        token,
        organisation_id,
        base_url=None,
    ):
        """Get tags assigned to an entity.

        entity_type: immobilie, contact, deal, etc.
        entity_id: the entity's UUID.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.tags_get_entity(entity_type=entity_type, entity_id=entity_id),
        )
        return _ok(result)

    @mcp.tool()
    def tags_update_entity(
        entity_type,
        entity_id,
        tag_ids,
        token,
        organisation_id,
        base_url=None,
    ):
        """Set the tags for an entity (replaces existing tags).

        entity_type: immobilie, contact, deal, etc.
        entity_id: the entity's UUID.
        tag_ids: list of tag UUIDs to assign (replaces all existing tags).
        """

        ids = _require_list(field_name='tag_ids', value=tag_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.tags_update_entity(
                entity_type=entity_type, entity_id=entity_id, tag_ids=ids,
            ),
        )
        return _ok(result)
