from .._shared import _call_with_client, _ok, _require_dict, _require_list


def register(mcp):
    @mcp.tool()
    def contacts_list(
        token=None,
        organisation_id=None,
        page=1,
        per_page=25,
        search=None,
        base_url=None,
    ):
        """List contacts with pagination and optional text search.

        Returns contacts with name, email, phone, company, status, tags.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_list(
                page=int(page), per_page=int(per_page), search=search,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_get(
        contact_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get full details for a single contact by UUID."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_get(contact_id=contact_id),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_create(
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a new contact.

        Common fields: first_name, last_name, email, phone, mobile,
        company, position, address, notes, tags.
        """

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_create(data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_update(
        contact_id,
        data,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Update an existing contact (full replace)."""

        payload = _require_dict(field_name='data', value=data)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_update(contact_id=contact_id, data=payload),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_update_status(
        contact_id,
        status_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Change the pipeline status of a contact.

        status_id: integer ID of the target status.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_update_status(contact_id=contact_id, status_id=status_id),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_delete(
        contact_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete a single contact permanently."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_delete(contact_id=contact_id),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_count(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Return the total number of contacts for the organisation."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_count(),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_bulk_delete(
        contact_ids,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete multiple contacts at once.

        contact_ids: list of contact UUIDs to delete.
        """

        ids = _require_list(field_name='contact_ids', value=contact_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_bulk_delete(contact_ids=ids),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_get_immobilien(
        contact_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List properties linked to a contact."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_get_immobilien(contact_id=contact_id),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_get_activities(
        contact_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List activities linked to a contact."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_get_activities(contact_id=contact_id),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_merge_logs(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """View merge history -- shows previous contact merge operations."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_merge_logs(),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_merge_restore(
        merge_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Restore a previously merged contact (undo merge)."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_merge_restore(merge_id=merge_id),
        )
        return _ok(result)

    # ------------------------------------------------------------------
    # Contact import (existing tools, migrated from server.py)
    # ------------------------------------------------------------------

    @mcp.tool()
    def contacts_import_preview(
        source_type,
        token=None,
        organisation_id=None,
        source_text=None,
        file_path=None,
        sheet_name=None,
        mapping_overrides=None,
        smart=True,
        base_url=None,
    ):
        """Preview contact import using dry_run mode.

        source_type: csv, xlsx, pdf, image, or text.
        Provide source_text for inline data or file_path for a local file.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_import_unified(
                source_type=source_type,
                dry_run=True,
                smart=smart,
                source_text=source_text,
                file_path=file_path,
                sheet_name=sheet_name,
                mapping_overrides=mapping_overrides,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_import_start(
        source_type,
        token=None,
        organisation_id=None,
        source_text=None,
        file_path=None,
        sheet_name=None,
        mapping_overrides=None,
        smart=True,
        base_url=None,
    ):
        """Start asynchronous contact import job.

        Returns a job_id to track progress via contacts_job_status.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_import_unified(
                source_type=source_type,
                dry_run=False,
                smart=smart,
                source_text=source_text,
                file_path=file_path,
                sheet_name=sheet_name,
                mapping_overrides=mapping_overrides,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_job_status(
        job_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Read import job status."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_job_status(job_id=job_id),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_job_resume(
        job_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Resume a failed/cancelled import job."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_job_resume(job_id=job_id),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_job_cancel(
        job_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Request cancellation for an import job."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_job_cancel(job_id=job_id),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_duplicates_preview(
        token=None,
        organisation_id=None,
        by='email,phone,mobile,name',
        min_count=2,
        limit_groups=200,
        ignore_generic_names=True,
        base_url=None,
    ):
        """Preview duplicate-contact groups.

        by: comma-separated match criteria (email, phone, mobile, name).
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_duplicates_preview(
                by=by,
                min_count=min_count,
                limit_groups=limit_groups,
                ignore_generic_names=ignore_generic_names,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def contacts_merge_apply(
        primary_id,
        duplicate_ids,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Execute contact merge for confirmed duplicates.

        primary_id: the contact to keep.
        duplicate_ids: list of contacts to merge into primary.
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.contacts_merge_apply(primary_id=primary_id, duplicate_ids=duplicate_ids),
        )
        return _ok(result)
