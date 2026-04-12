from .._shared import _call_with_client, _ok, _require_dict


def register(mcp):
    # ------------------------------------------------------------------
    # Definitions
    # ------------------------------------------------------------------

    @mcp.tool()
    def custom_fields_definitions_list(
        model,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List custom field definitions for a model.

        model: one of contact, activity, deal, immobilie, unit.

        Returns definitions with id, name, type, config, hint, usage_count.
        Field types: text, richtext, number, boolean, date, time, dropdown, relation.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.custom_fields_definitions_list(model=model),
        )
        return _ok(result)

    @mcp.tool()
    def custom_fields_definition_create(
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a custom field definition (admin only).

        Required in data:
        - model: contact, activity, deal, immobilie, or unit
        - name: display name
        - type: text, richtext, number, boolean, date, time, dropdown, or relation

        Optional:
        - config: type-specific settings, e.g.
          - dropdown: {"options": ["A", "B", "C"]}
          - number: {"currency": "EUR", "decimals": 2, "notation": "currency"}
          - relation: {"relation_model": "contact", "multiple": false}
        - hint: helper text shown to users
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.custom_fields_definition_create(data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def custom_fields_definition_update(
        definition_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update a custom field definition (admin only).

        Updatable fields in data: name, config, hint.
        Note: the field type cannot be changed after creation.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.custom_fields_definition_update(
                definition_id=definition_id, data=payload,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def custom_fields_definition_delete(
        definition_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete a custom field definition and all its values (admin only)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.custom_fields_definition_delete(
                definition_id=definition_id,
            ),
        )
        return _ok(result)

    # ------------------------------------------------------------------
    # Views
    # ------------------------------------------------------------------

    @mcp.tool()
    def custom_fields_views_list(
        model,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List custom field views (layout configurations) for a model.

        model: contact, activity, deal, immobilie, or unit.

        Views define how fields are grouped and displayed in the UI.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.custom_fields_views_list(model=model),
        )
        return _ok(result)

    @mcp.tool()
    def custom_fields_view_create(
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a custom field view (layout configuration).

        data:
        - model: contact, activity, deal, immobilie, or unit
        - name: view name
        - visibility: "private" (only you) or "organisation" (all members, admin only)
        - is_default: true to set as default view for this model
        - config: {"groups": [...], "ungrouped_field_ids": [...], "hidden_field_ids": [...]}
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.custom_fields_view_create(data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def custom_fields_view_update(
        view_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update a custom field view."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.custom_fields_view_update(
                view_id=view_id, data=payload,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def custom_fields_view_delete(
        view_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete a custom field view."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.custom_fields_view_delete(view_id=view_id),
        )
        return _ok(result)

    # ------------------------------------------------------------------
    # Values
    # ------------------------------------------------------------------

    @mcp.tool()
    def custom_fields_values_get(
        model,
        target_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get custom field values for a specific entity.

        model: contact, activity, deal, immobilie, or unit.
        target_id: the entity's UUID.

        Returns a dict mapping definition_id -> value.
        Value types depend on the field type:
        - text/richtext -> string
        - number -> float
        - boolean -> bool
        - date -> "YYYY-MM-DD"
        - time -> "HH:MM"
        - dropdown -> string
        - relation -> string or list of strings
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.custom_fields_values_get(
                model=model, target_id=target_id,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def custom_fields_values_set(
        model,
        target_id,
        values,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Set custom field values for a specific entity.

        model: contact, activity, deal, immobilie, or unit.
        target_id: the entity's UUID.
        values: dict mapping definition_id -> value.
          Pass null as value to delete a field value.

        Example:
          {"def-uuid-1": "some text", "def-uuid-2": 42.5, "def-uuid-3": null}
        """

        vals = _require_dict(field_name='values', value=values)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.custom_fields_values_set(
                model=model, target_id=target_id, values=vals,
            ),
        )
        return _ok(result)
