from .._shared import _call_with_client, _ok, _require_list


def register(mcp):
    @mcp.tool()
    def email_list(
        token=None,
        organisation_id=None,
        folder=None,
        page=1,
        per_page=25,
        search=None,
        base_url=None,
    ):
        """List email messages with pagination and optional filters.

        - folder: filter by folder name
        - search: free-text search in subject/body
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_list(
                folder=folder, page=int(page), per_page=int(per_page), search=search,
            ),
        )
        return _ok(result)

    @mcp.tool()
    def email_get(
        message_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get full details for a single email message."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_get(message_id=message_id),
        )
        return _ok(result)

    @mcp.tool()
    def email_thread(
        thread_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get all messages in an email thread."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_thread(thread_id=thread_id),
        )
        return _ok(result)

    @mcp.tool()
    def email_mark_read(
        message_ids,
        token=None,
        organisation_id=None,
        read=True,
        base_url=None,
    ):
        """Mark messages as read or unread.

        message_ids: list of message IDs.
        read: true to mark as read, false to mark as unread.
        """

        ids = _require_list(field_name='message_ids', value=message_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_mark_read(message_ids=ids, read=bool(read)),
        )
        return _ok(result)

    @mcp.tool()
    def email_mark_starred(
        message_ids,
        token=None,
        organisation_id=None,
        starred=True,
        base_url=None,
    ):
        """Star or unstar email messages.

        message_ids: list of message IDs.
        starred: true to star, false to unstar.
        """

        ids = _require_list(field_name='message_ids', value=message_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_mark_starred(message_ids=ids, starred=bool(starred)),
        )
        return _ok(result)

    @mcp.tool()
    def email_archive(
        message_ids,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Archive email messages."""

        ids = _require_list(field_name='message_ids', value=message_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_archive(message_ids=ids),
        )
        return _ok(result)

    @mcp.tool()
    def email_trash(
        message_ids,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Move email messages to trash."""

        ids = _require_list(field_name='message_ids', value=message_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_trash(message_ids=ids),
        )
        return _ok(result)

    @mcp.tool()
    def email_move(
        message_ids,
        folder,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Move email messages to a specific folder."""

        ids = _require_list(field_name='message_ids', value=message_ids)
        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_move(message_ids=ids, folder=folder),
        )
        return _ok(result)

    @mcp.tool()
    def email_folders(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """List email folders."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_folders(),
        )
        return _ok(result)

    @mcp.tool()
    def email_create_folder(
        name,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Create a new email folder."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_create_folder(name=name),
        )
        return _ok(result)

    @mcp.tool()
    def email_rename_folder(
        folder_id,
        name,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Rename an email folder."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_rename_folder(folder_id=folder_id, name=name),
        )
        return _ok(result)

    @mcp.tool()
    def email_delete_folder(
        folder_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Delete an email folder."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_delete_folder(folder_id=folder_id),
        )
        return _ok(result)

    @mcp.tool()
    def email_search(
        query,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Search email messages by query string."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_search(query=query),
        )
        return _ok(result)

    @mcp.tool()
    def email_by_contact(
        contact_id,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Get all emails associated with a contact."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_by_contact(contact_id=contact_id),
        )
        return _ok(result)

    @mcp.tool()
    def email_sync(
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Trigger email synchronisation with the mail provider."""

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_sync(),
        )
        return _ok(result)
