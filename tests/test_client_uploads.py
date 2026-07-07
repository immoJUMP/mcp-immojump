"""Client tests for document + image uploads (multipart/form-data)."""

import base64

import httpx

from mcp_immojump.client import ImmojumpAPIClient, ImmojumpCredentials


def _creds():
    return ImmojumpCredentials(base_url='http://localhost:8081', token='tok', organisation_id='org-1')


def _capture_client(handler):
    transport = httpx.MockTransport(handler)
    return ImmojumpAPIClient(_creds(), transport=transport)


def _capture(handler_store):
    def handler(req: httpx.Request) -> httpx.Response:
        handler_store['method'] = req.method
        handler_store['path'] = req.url.path
        handler_store['content_type'] = req.headers.get('content-type', '')
        handler_store['body'] = req.read()
        return httpx.Response(200, json=[{'id': 'new-1'}])
    return handler


def test_documents_upload_path_and_multipart_fields():
    cap = {}
    with _capture_client(_capture(cap)) as client:
        client.documents_upload(
            filename='expose.pdf',
            content=b'%PDF-1.4 fake',
            immobilie_id='imm-1',
        )

    assert cap['method'] == 'POST'
    assert cap['path'] == '/api/documents/documents/bulk-upload'
    assert 'multipart/form-data' in cap['content_type']
    body = cap['body']
    # file part uses the backend's expected `files[]` field name
    assert b'name="files[]"' in body
    assert b'expose.pdf' in body
    assert b'%PDF-1.4 fake' in body
    # form fields
    assert b'name="immobilien_id"' in body
    assert b'imm-1' in body
    assert b'name="organisation_id"' in body
    assert b'org-1' in body


def test_documents_upload_allow_duplicate_flag():
    cap = {}
    with _capture_client(_capture(cap)) as client:
        client.documents_upload(filename='a.pdf', content=b'x', allow_duplicate_upload=True)
    body = cap['body']
    assert b'name="allow_duplicate_upload"' in body
    assert b'true' in body


def test_documents_upload_accepts_base64():
    cap = {}
    raw = b'hello-doc-bytes'
    with _capture_client(_capture(cap)) as client:
        client.documents_upload(
            filename='note.txt',
            content_base64=base64.b64encode(raw).decode(),
            immobilie_id='imm-9',
        )
    assert raw in cap['body']


def test_image_upload_path_and_multipart_fields():
    cap = {}
    with _capture_client(_capture(cap)) as client:
        client.image_upload(
            filename='photo.jpg',
            content=b'\xff\xd8\xff\xe0jpegdata',
            immobilie_id='imm-1',
            content_type='image/jpeg',
        )

    assert cap['method'] == 'POST'
    assert cap['path'] == '/api/images/upload-direct'
    assert 'multipart/form-data' in cap['content_type']
    body = cap['body']
    # image endpoint expects the field name `file`
    assert b'name="file"' in body
    assert b'photo.jpg' in body
    assert b'image/jpeg' in body
    assert b'name="immobilie_id"' in body
    assert b'imm-1' in body


def test_image_upload_guesses_content_type_from_filename():
    cap = {}
    with _capture_client(_capture(cap)) as client:
        client.image_upload(filename='pic.png', content=b'\x89PNG', immobilie_id='imm-1')
    assert b'image/png' in cap['body']


def test_documents_upload_returns_documents_under_key():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{'id': 'doc-1'}])
    with _capture_client(handler) as client:
        result = client.documents_upload(filename='a.pdf', content=b'x', immobilie_id='imm-1')
    assert result['documents'] == [{'id': 'doc-1'}]
    assert 'duplicates' not in result


def test_documents_upload_surfaces_skip_headers():
    import json as _json

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[],
            headers={
                'X-Upload-Duplicate-Files': _json.dumps([{'fileName': 'expose.pdf'}]),
                'X-Upload-Empty-Files': _json.dumps(['leer.pdf']),
                'X-Upload-Failed-Files': _json.dumps([{'fileName': 'kaputt.pdf', 'message': 'Invalid PDF'}]),
            },
        )
    with _capture_client(handler) as client:
        result = client.documents_upload(filename='expose.pdf', content=b'x', immobilie_id='imm-1')
    assert result['documents'] == []
    assert result['duplicates'][0]['fileName'] == 'expose.pdf'
    assert result['skipped_empty'] == ['leer.pdf']
    assert result['failed'][0]['message'] == 'Invalid PDF'
