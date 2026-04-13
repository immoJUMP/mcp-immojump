"""Minimal OAuth 2.1 authorization server for MCP.

Wraps immoJUMP's existing API token in an OAuth flow so that
MCP clients like ChatGPT (which require OAuth) can authenticate.

Flow:
1. Client hits MCP endpoint without token → 401 with WWW-Authenticate
2. Client discovers auth server via /.well-known/oauth-protected-resource
3. Client opens /oauth/authorize in browser → user enters API token + org
4. Server redirects back with authorization code
5. Client exchanges code for access_token via /oauth/token (with PKCE)
6. access_token = base64({api_token}:{org_id}) — used in subsequent requests
"""

from __future__ import annotations

import base64
import hashlib
import html
import logging
import os
import secrets
import time
from typing import Any
from urllib.parse import urlencode

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Route

logger = logging.getLogger(__name__)

# Auth codes expire after 5 minutes, keyed by code → {token, org_id, code_challenge, expires, redirect_uri, client_id}
_auth_codes: dict[str, dict[str, Any]] = {}

# Registered clients from DCR, keyed by client_id → {redirect_uris, ...}
_registered_clients: dict[str, dict[str, Any]] = {}

# Cleanup stale codes every request (simple, no background thread needed)
_CODE_TTL = 300  # 5 minutes


def _cleanup_codes() -> None:
    now = time.time()
    expired = [k for k, v in _auth_codes.items() if v['expires'] < now]
    for k in expired:
        del _auth_codes[k]


def _get_server_url(request: Request) -> str:
    """Derive the public server URL from the request."""
    url = os.getenv('IMMOJUMP_MCP_PUBLIC_URL', '').strip()
    if url:
        return url.rstrip('/')
    # Fallback: construct from request
    scheme = request.headers.get('x-forwarded-proto', request.url.scheme)
    host = request.headers.get('x-forwarded-host', request.url.hostname or 'localhost')
    port = request.url.port
    if port and port not in (80, 443):
        return f'{scheme}://{host}:{port}'
    return f'{scheme}://{host}'


def _encode_access_token(api_token: str, org_id: str) -> str:
    """Encode API token + org_id into a single access_token string."""
    return base64.urlsafe_b64encode(f'{api_token}:{org_id}'.encode()).decode()


def decode_access_token(access_token: str) -> tuple[str, str] | None:
    """Decode access_token back to (api_token, org_id). Returns None on failure."""
    try:
        decoded = base64.urlsafe_b64decode(access_token.encode()).decode()
        if ':' not in decoded:
            return None
        # Org ID is always a UUID (36 chars) at the end after the last ':'
        last_colon = decoded.rfind(':')
        if last_colon <= 0:
            return None
        api_token = decoded[:last_colon]
        org_id = decoded[last_colon + 1:]
        if not api_token or not org_id:
            return None
        return api_token, org_id
    except Exception:
        return None


def _verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    """Verify PKCE S256 challenge."""
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return secrets.compare_digest(expected, code_challenge)


# ---------------------------------------------------------------------------
# OAuth Endpoints
# ---------------------------------------------------------------------------

async def protected_resource_metadata(request: Request) -> JSONResponse:
    """RFC 9728: OAuth 2.0 Protected Resource Metadata."""
    server_url = _get_server_url(request)
    return JSONResponse({
        'resource': server_url,
        'authorization_servers': [server_url],
        'scopes_supported': ['immojump'],
        'bearer_methods_supported': ['header'],
    })


async def authorization_server_metadata(request: Request) -> JSONResponse:
    """RFC 8414: OAuth 2.0 Authorization Server Metadata."""
    server_url = _get_server_url(request)
    return JSONResponse({
        'issuer': server_url,
        'authorization_endpoint': f'{server_url}/oauth/authorize',
        'token_endpoint': f'{server_url}/oauth/token',
        'registration_endpoint': f'{server_url}/oauth/register',
        'response_types_supported': ['code'],
        'grant_types_supported': ['authorization_code'],
        'code_challenge_methods_supported': ['S256'],
        'scopes_supported': ['immojump'],
        'token_endpoint_auth_methods_supported': ['none'],
        'client_id_metadata_document_supported': True,
    })


async def authorize(request: Request) -> Response:
    """Authorization endpoint — shows form or processes submission."""
    if request.method == 'GET':
        # Extract OAuth params
        client_id = request.query_params.get('client_id', '')
        redirect_uri = request.query_params.get('redirect_uri', '')
        state = request.query_params.get('state', '')
        code_challenge = request.query_params.get('code_challenge', '')
        code_challenge_method = request.query_params.get('code_challenge_method', '')
        scope = request.query_params.get('scope', '')

        if not redirect_uri:
            return HTMLResponse('<h1>Fehler: redirect_uri fehlt</h1>', status_code=400)
        if code_challenge_method and code_challenge_method != 'S256':
            return HTMLResponse('<h1>Fehler: Nur S256 PKCE wird unterstützt</h1>', status_code=400)

        # Render login form
        form_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>immoJUMP verbinden</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #f5f7fa; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; padding: 20px; }}
        .card {{ background: white; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.1);
                padding: 40px; max-width: 440px; width: 100%; }}
        .logo {{ text-align: center; margin-bottom: 24px; font-size: 28px; font-weight: 700; color: #1a1a2e; }}
        .logo span {{ color: #4361ee; }}
        .subtitle {{ text-align: center; color: #666; margin-bottom: 32px; font-size: 15px; line-height: 1.5; }}
        label {{ display: block; font-weight: 600; margin-bottom: 6px; color: #333; font-size: 14px; }}
        input {{ width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 10px;
                font-size: 15px; transition: border-color 0.2s; margin-bottom: 20px; }}
        input:focus {{ outline: none; border-color: #4361ee; }}
        .hint {{ font-size: 12px; color: #888; margin-top: -16px; margin-bottom: 20px; }}
        button {{ width: 100%; padding: 14px; background: #4361ee; color: white; border: none;
                border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer;
                transition: background 0.2s; }}
        button:hover {{ background: #3451d1; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #aaa; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">immo<span>JUMP</span></div>
        <p class="subtitle">Verbinde deine KI-App mit deinem immoJUMP-Konto.<br>
        Du brauchst deinen API-Token und deine Organisation-ID.</p>
        <form method="POST" action="/oauth/authorize">
            <input type="hidden" name="client_id" value="{html.escape(client_id)}">
            <input type="hidden" name="redirect_uri" value="{html.escape(redirect_uri)}">
            <input type="hidden" name="state" value="{html.escape(state)}">
            <input type="hidden" name="code_challenge" value="{html.escape(code_challenge)}">
            <input type="hidden" name="scope" value="{html.escape(scope)}">

            <label for="api_token">API-Token</label>
            <input type="password" id="api_token" name="api_token"
                   placeholder="eyJhbGci..." required>
            <p class="hint">Einstellungen → API-Zugang → Token generieren</p>

            <label for="org_id">Organisation-ID</label>
            <input type="text" id="org_id" name="org_id"
                   placeholder="abc12345-de67-89ab-cdef-..." required>
            <p class="hint">Sichtbar in der URL: immojump.de/o/<strong>deine-id</strong>/...</p>

            <button type="submit">Verbinden</button>
        </form>
        <p class="footer">Deine Daten werden nur für diese Verbindung verwendet.</p>
    </div>
</body>
</html>"""
        return HTMLResponse(form_html)

    # POST: process form submission
    form = await request.form()
    api_token = str(form.get('api_token', '')).strip()
    org_id = str(form.get('org_id', '')).strip()
    redirect_uri = str(form.get('redirect_uri', '')).strip()
    state = str(form.get('state', '')).strip()
    code_challenge = str(form.get('code_challenge', '')).strip()
    client_id = str(form.get('client_id', '')).strip()

    if not api_token or not org_id:
        return HTMLResponse('<h1>Fehler: Token und Organisation-ID sind erforderlich</h1>', status_code=400)
    if not redirect_uri:
        return HTMLResponse('<h1>Fehler: redirect_uri fehlt</h1>', status_code=400)

    # Validate redirect_uri against registered client (if DCR was used)
    if client_id and client_id in _registered_clients:
        registered = _registered_clients[client_id]
        if registered['redirect_uris'] and redirect_uri not in registered['redirect_uris']:
            return HTMLResponse('<h1>Fehler: redirect_uri stimmt nicht mit der Registrierung überein</h1>', status_code=400)

    # Validate token against immoJUMP API (best-effort)
    import httpx
    try:
        base_url = os.getenv('IMMOJUMP_BASE_URL', 'https://immojump.de')
        resp = httpx.get(
            f'{base_url}/api/contacts/count',
            params={'organisation_id': org_id},
            headers={'Authorization': f'Bearer {api_token}', 'X-Organisation-Id': org_id},
            timeout=10,
        )
        if resp.status_code == 401:
            return HTMLResponse(
                '<h1>Ungültiger Token</h1><p>Bitte prüfe deinen API-Token und versuche es erneut.</p>'
                '<p><a href="javascript:history.back()">Zurück</a></p>',
                status_code=400,
            )
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        pass  # Backend unreachable — skip validation, will fail on actual tool calls

    # Generate auth code
    _cleanup_codes()
    code = secrets.token_urlsafe(32)
    _auth_codes[code] = {
        'api_token': api_token,
        'org_id': org_id,
        'code_challenge': code_challenge,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'expires': time.time() + _CODE_TTL,
    }

    # Redirect back to client
    params = {'code': code}
    if state:
        params['state'] = state
    separator = '&' if '?' in redirect_uri else '?'
    return RedirectResponse(f'{redirect_uri}{separator}{urlencode(params)}', status_code=302)


async def token(request: Request) -> JSONResponse:
    """Token endpoint — exchange auth code for access_token."""
    _cleanup_codes()

    # Accept both form and JSON
    content_type = request.headers.get('content-type', '')
    if 'json' in content_type:
        body = await request.json()
    else:
        form = await request.form()
        body = dict(form)

    grant_type = body.get('grant_type', '')
    code = body.get('code', '')
    code_verifier = body.get('code_verifier', '')
    redirect_uri = body.get('redirect_uri', '')

    if grant_type != 'authorization_code':
        return JSONResponse({'error': 'unsupported_grant_type'}, status_code=400)

    if code not in _auth_codes:
        return JSONResponse({'error': 'invalid_grant', 'error_description': 'Code expired or invalid'}, status_code=400)

    code_data = _auth_codes.pop(code)

    # Verify PKCE if challenge was provided
    if code_data['code_challenge']:
        if not code_verifier:
            return JSONResponse({'error': 'invalid_grant', 'error_description': 'code_verifier required'}, status_code=400)
        if not _verify_pkce(code_verifier, code_data['code_challenge']):
            return JSONResponse({'error': 'invalid_grant', 'error_description': 'PKCE verification failed'}, status_code=400)

    # Verify redirect_uri matches
    if redirect_uri and redirect_uri != code_data['redirect_uri']:
        return JSONResponse({'error': 'invalid_grant', 'error_description': 'redirect_uri mismatch'}, status_code=400)

    # Issue access token (encodes api_token:org_id)
    access_token = _encode_access_token(code_data['api_token'], code_data['org_id'])

    return JSONResponse({
        'access_token': access_token,
        'token_type': 'bearer',
        'scope': 'immojump',
        'expires_in': 86400,  # 24 hours
    })


async def register(request: Request) -> JSONResponse:
    """RFC 7591: Dynamic Client Registration.

    Accepts any registration request and returns a client_id.
    Our auth flow doesn't validate client_id — the user authenticates
    with their immoJUMP API token, not with client credentials.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    # Use provided client_name or generate one
    client_name = body.get('client_name', 'MCP Client')
    client_id = body.get('client_id') or f'immojump-{secrets.token_hex(8)}'
    redirect_uris = body.get('redirect_uris', [])

    _registered_clients[client_id] = {
        'client_name': client_name,
        'redirect_uris': redirect_uris,
    }

    return JSONResponse({
        'client_id': client_id,
        'client_name': client_name,
        'redirect_uris': redirect_uris,
        'grant_types': ['authorization_code'],
        'response_types': ['code'],
        'token_endpoint_auth_method': 'none',
    }, status_code=201)


# ---------------------------------------------------------------------------
# ASGI App factory
# ---------------------------------------------------------------------------

def create_oauth_routes() -> list[Route]:
    """Return Starlette routes for the OAuth endpoints."""
    return [
        Route('/.well-known/oauth-protected-resource', protected_resource_metadata, methods=['GET']),
        Route('/.well-known/oauth-authorization-server', authorization_server_metadata, methods=['GET']),
        Route('/oauth/authorize', authorize, methods=['GET', 'POST']),
        Route('/oauth/token', token, methods=['POST']),
        Route('/oauth/register', register, methods=['POST']),
    ]
