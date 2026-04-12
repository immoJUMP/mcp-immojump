from .._app import mcp, _call_with_client, _ok


@mcp.tool()
def documents_list(
    token,
    organisation_id,
    immobilie_id=None,
    page=1,
    per_page=25,
    base_url=None,
):
    """List documents, optionally filtered by property.

    - immobilie_id: filter documents for a specific property
    """

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.documents_list(
            immobilie_id=immobilie_id,
            page=int(page),
            per_page=int(per_page),
        ),
    )
    return _ok(result)


@mcp.tool()
def documents_delete(
    document_id,
    token,
    organisation_id,
    base_url=None,
):
    """Delete a document permanently."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.documents_delete(document_id=document_id),
    )
    return _ok(result)


@mcp.tool()
def documents_rename(
    document_id,
    name,
    token,
    organisation_id,
    base_url=None,
):
    """Rename a document."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.documents_rename(document_id=document_id, name=name),
    )
    return _ok(result)


@mcp.tool()
def documents_analyze(
    document_id,
    token,
    organisation_id,
    base_url=None,
):
    """Trigger AI analysis on a document (quick summary)."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.documents_analyze(document_id=document_id),
    )
    return _ok(result)


@mcp.tool()
def documents_analyze_details(
    document_id,
    token,
    organisation_id,
    base_url=None,
):
    """Trigger detailed AI analysis on a document.

    Extracts structured data: costs, units, financial details.
    """

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.documents_analyze_details(document_id=document_id),
    )
    return _ok(result)


@mcp.tool()
def documents_mark_reviewed(
    document_id,
    token,
    organisation_id,
    base_url=None,
):
    """Mark a document as reviewed."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.documents_mark_reviewed(document_id=document_id),
    )
    return _ok(result)


@mcp.tool()
def documents_analysis_results(
    token,
    organisation_id,
    immobilie_id=None,
    document_id=None,
    base_url=None,
):
    """Get AI analysis results for documents.

    Filter by immobilie_id and/or document_id.
    """

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.documents_analysis_results(
            immobilie_id=immobilie_id,
            document_id=document_id,
        ),
    )
    return _ok(result)


@mcp.tool()
def documents_clear_analysis(
    token,
    organisation_id,
    immobilie_id=None,
    base_url=None,
):
    """Clear AI analysis results. Optionally filter by property."""

    result = _call_with_client(
        base_url=base_url,
        token=token,
        organisation_id=organisation_id,
        callback=lambda client: client.documents_clear_analysis(immobilie_id=immobilie_id),
    )
    return _ok(result)
