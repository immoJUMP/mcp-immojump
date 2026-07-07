from .._shared import _call_with_client, _ok, write_op


def register(mcp):
    @mcp.tool(annotations=write_op())
    def image_upload(
        filename,
        immobilie_id,
        content_base64=None,
        file_path=None,
        content_type=None,
        token=None,
        organisation_id=None,
        base_url=None,
    ):
        """Upload an image for a property (stored in object storage).

        Provide the image either as `content_base64` (base64-encoded bytes) or
        as a local `file_path`. `filename` sets the stored name.
        - immobilie_id: the property the image belongs to (required)
        - content_type: e.g. image/jpeg, image/png (guessed from the filename
          when omitted)
        """

        result = _call_with_client(
            base_url=base_url,
            token=token,
            organisation_id=organisation_id,
            callback=lambda client: client.image_upload(
                filename=filename,
                immobilie_id=immobilie_id,
                content_base64=content_base64,
                file_path=file_path,
                content_type=content_type,
            ),
        )
        return _ok(result)
