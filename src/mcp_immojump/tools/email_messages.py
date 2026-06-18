from .._shared import _call_with_client, _ok, _require_dict, _require_list, _require_text, destructive_op, read_only, write_op


def _normalize_emails(value):
    """Normalize email parameter to list, accepting string or list.
    
    Handles:
    - None -> None
    - string (single email or JSON array) -> list
    - list -> list (normalized)
    """
    if value is None:
        return None
    if isinstance(value, str):
        # Try to parse as JSON array first (e.g., "[\"a@b.com\"]")
        try:
            import json
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(v).strip().lower() for v in parsed if str(v).strip()]
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        # Single email as plain string
        if value.strip():
            return [value.strip().lower()]
        return []
    if isinstance(value, list):
        return [str(v).strip().lower() for v in value if str(v).strip()]
    raise ValueError("Must be a string or list of email addresses")


def register(mcp):
    @mcp.tool(annotations=read_only())
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

    @mcp.tool(annotations=read_only())
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

    @mcp.tool(annotations=read_only())
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

    @mcp.tool(annotations=write_op())
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

    @mcp.tool(annotations=write_op())
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

    @mcp.tool(annotations=write_op())
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

    @mcp.tool(annotations=write_op(idempotent=True))
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

    @mcp.tool(annotations=write_op())
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

    @mcp.tool(annotations=read_only())
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

    @mcp.tool(annotations=write_op())
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

    @mcp.tool(annotations=write_op())
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

    @mcp.tool(annotations=destructive_op())
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

    @mcp.tool(annotations=read_only())
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

    @mcp.tool(annotations=read_only())
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

    @mcp.tool(annotations=write_op())
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

    @mcp.tool(annotations=write_op())
    def email_account_send(
        account_id,
        subject,
        body_html,
        to,
        cc=None,
        bcc=None,
        signature_id=None,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Send an email via an organisation email account.

        Requires an active OrganisationEmailAccount with SMTP configuration
        in the backend. The account_id must belong to the specified organisation.

        Parameters:
        - account_id: UUID of the organisation email account
        - subject: Email subject line
        - body_html: HTML content of the email
        - to: List of recipient email addresses (or single string)
        - cc: Optional list of CC recipients (or single string)
        - bcc: Optional list of BCC recipients (or single string)
        - signature_id: Optional UUID of email signature to append
        """
        subject_str = _require_text(field_name='subject', value=subject)
        body_str = _require_text(field_name='body_html', value=body_html)
        account_id_str = _require_text(field_name='account_id', value=account_id)

        # Normalize email parameters (accept both string and list)
        to_list = _normalize_emails(to)
        cc_list = _normalize_emails(cc) if cc is not None else None
        bcc_list = _normalize_emails(bcc) if bcc is not None else None

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_account_send(
                account_id=account_id_str,
                subject=subject_str,
                body_html=body_str,
                to=to_list,
                cc=cc_list,
                bcc=bcc_list,
                signature_id=signature_id,
            ),
        )
        return _ok(result)

    @mcp.tool(annotations=write_op())
    def email_account_send_with_template(
        account_id,
        subject,
        body_html,
        to,
        cc=None,
        bcc=None,
        contact_ids=None,
        template_id=None,
        variables=None,
        signature_id=None,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Send an email via an organisation email account with optional template and variables.

        This is an extended version that supports communication templates and
        variable substitution. Note: file attachments are not yet supported
        via the MCP interface.

        Parameters:
        - account_id: UUID of the organisation email account
        - subject: Email subject line (can be overridden by template)
        - body_html: HTML content (can be overridden by template)
        - to: List of recipient email addresses (or single string)
        - cc: Optional list of CC recipients (or single string)
        - bcc: Optional list of BCC recipients (or single string)
        - contact_ids: Optional list of contact UUIDs to associate
        - template_id: Optional UUID of communication template
        - variables: Optional dict of template variables
        - signature_id: Optional UUID of email signature to append
        """
        subject_str = _require_text(field_name='subject', value=subject)
        body_str = _require_text(field_name='body_html', value=body_html)
        account_id_str = _require_text(field_name='account_id', value=account_id)

        # Normalize email parameters (accept both string and list)
        to_list = _normalize_emails(to)
        cc_list = _normalize_emails(cc) if cc is not None else None
        bcc_list = _normalize_emails(bcc) if bcc is not None else None

        def _normalize_uuid_list(values):
            if values is None:
                return None
            if isinstance(values, str):
                try:
                    import json
                    parsed = json.loads(values)
                    if isinstance(parsed, list):
                        return [str(v).strip() for v in parsed if str(v).strip()]
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
                if values.strip():
                    return [values.strip()]
                return []
            if isinstance(values, list):
                return [str(v).strip() for v in values if str(v).strip()]
            raise ValueError("contact_ids must be a string or list of UUIDs")

        variables_dict = None
        if variables:
            variables_dict = _require_dict(field_name='variables', value=variables)

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.email_account_send_with_attachments(
                account_id=account_id_str,
                subject=subject_str,
                body_html=body_str,
                to=to_list,
                cc=cc_list,
                bcc=bcc_list,
                contact_ids=_normalize_uuid_list(contact_ids),
                template_id=template_id,
                variables=variables_dict,
                signature_id=signature_id,
            ),
        )
        return _ok(result)
