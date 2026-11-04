"""Minimal OAuth 2.1 authorization server for MCP.

Wraps immoJUMP's existing API token in an OAuth flow so that
MCP clients like ChatGPT (which require OAuth) can authenticate.

Flow:
1. Client hits MCP endpoint without token → 401 with WWW-Authenticate
2. Client discovers auth server via /.well-known/oauth-protected-resource
3. Client opens /oauth/authorize in browser → user enters API token + org
4. Server redirects back with authorization code
5. Client exchanges code for access_token + refresh_token via /oauth/token (PKCE)
6. Before the access token runs out the client trades the refresh_token for a
   new pair — no user needed, which is what ChatGPT's scheduled tasks rely on.

Stateless by design: codes, client registrations, access and refresh tokens
are sealed (Fernet = AES-CBC + HMAC-SHA256) with ``IMMOJUMP_MCP_OAUTH_SECRET``.
Any pod with the same secret can read them, so a rollout or a second pod
mid-flow no longer loses anything, and the API token never appears in clear
in anything handed to the client.

Who may receive a code: registration is open (DCR without authentication,
client_id metadata documents are not fetched), so a client_id vouches for
nothing. The redirect_uri itself must point to a trusted origin — the AI apps
we serve, loopback for desktop and CLI clients, or an origin from
``IMMOJUMP_MCP_OAUTH_REDIRECT_ORIGINS``. PKCE S256 is required.

Without the secret the server keeps the old behaviour (base64 access token,
no refresh grant) and logs an error: clients then have to log in again after
``expires_in``.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import logging
import os
import secrets
import time
from typing import Any
from urllib.parse import urlencode, urlparse

import httpx
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Route

logger = logging.getLogger(__name__)

_SECRET_ENV = 'IMMOJUMP_MCP_OAUTH_SECRET'
_MIN_SECRET_LENGTH = 32

# Everything this server seals starts with this, so the middleware can tell a
# sealed access token (→ 401 when expired) from a raw immoJUMP API token.
_SEALED_PREFIX = 'ijm1.'

_CODE_TTL = 300  # 5 minutes
_ACCESS_TTL = 24 * 3600
_REFRESH_TTL = 90 * 24 * 3600  # sliding: every refresh issues a new one
_CLIENT_TTL = 10 * 365 * 24 * 3600  # registrations practically never expire

_LEGACY_EXPIRES_IN = 86400

_READ_ONLY_TOKEN_PREFIX = 'ijr_'

_REDIRECT_ORIGINS_ENV = 'IMMOJUMP_MCP_OAUTH_REDIRECT_ORIGINS'

# Origins (scheme://host[:port]) whose callbacks may receive a code. Every
# entry is a client seen on the hosted server or documented by its vendor:
# ChatGPT (also Codex web), Claude.ai/Desktop/mobile (claude.com announced),
# Cursor (custom scheme and its cloud agents).
_DEFAULT_REDIRECT_ORIGINS: frozenset[str] = frozenset({
    'https://chatgpt.com',
    'https://chat.openai.com',
    'https://claude.ai',
    'https://claude.com',
    'https://www.cursor.com',
    'cursor://anysphere.cursor-mcp',
})

# RFC 8252 §7.3: native apps listen on a loopback port of their choice.
_LOOPBACK_HOSTS: frozenset[str] = frozenset({'localhost', '127.0.0.1', '::1'})

# Fernet tokens are not single-use by themselves. Within one pod a code can
# be redeemed once; across pods PKCE and the 5-minute lifetime have to do.
_used_codes: dict[str, float] = {}

_fernet: MultiFernet | None = None
_persistent_secret = False

# Security headers applied to every HTML response rendered by this module.
# The authorize page accepts a user-entered API token, so it must never be
# embeddable (clickjacking), must disable referrer leakage, and must not be
# cached (the read-only confirmation carries the token in a hidden field).
_LOGIN_SECURITY_HEADERS = {
    'X-Frame-Options': 'DENY',
    'Content-Security-Policy': "default-src 'self'; style-src 'unsafe-inline'; frame-ancestors 'none'",
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
    'Cache-Control': 'no-store',
}

# RFC 6749 §5.1: token responses must not be cached.
_TOKEN_HEADERS = {'Cache-Control': 'no-store', 'Pragma': 'no-cache'}


# ---------------------------------------------------------------------------
# Sealing
# ---------------------------------------------------------------------------

def _derive_key(secret: str) -> Fernet:
    digest = hashlib.sha256(b'mcp-immojump-oauth-v1|' + secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _keys() -> MultiFernet:
    """Comma-separated secrets: the first seals, all of them unseal (rotation)."""
    global _fernet, _persistent_secret
    if _fernet is not None:
        return _fernet
    configured = [s.strip() for s in os.getenv(_SECRET_ENV, '').split(',') if s.strip()]
    usable = [s for s in configured if len(s) >= _MIN_SECRET_LENGTH]
    if len(usable) != len(configured):
        logger.error('%s: Schlüssel unter %d Zeichen werden ignoriert.', _SECRET_ENV, _MIN_SECRET_LENGTH)
    if usable:
        _fernet = MultiFernet([_derive_key(s) for s in usable])
        _persistent_secret = True
    else:
        # Codes and client registrations still work within this process;
        # access tokens fall back to the legacy format and there is no refresh.
        _fernet = MultiFernet([Fernet(Fernet.generate_key())])
        _persistent_secret = False
        logger.error(
            '%s ist nicht gesetzt: kein refresh_token, Clients müssen sich nach %d s neu '
            'anmelden, und ein Neustart mitten im Login verliert den Code.',
            _SECRET_ENV, _LEGACY_EXPIRES_IN,
        )
    return _fernet


def _refresh_supported() -> bool:
    _keys()
    return _persistent_secret


def _reset_keys_for_tests() -> None:
    global _fernet, _persistent_secret
    _fernet = None
    _persistent_secret = False
    _used_codes.clear()


def _seal(typ: str, data: dict[str, Any]) -> str:
    payload = json.dumps({'typ': typ, **data}, separators=(',', ':')).encode()
    return _SEALED_PREFIX + _keys().encrypt_at_time(payload, int(time.time())).decode()


def _unseal(value: str, typ: str, ttl: int) -> dict[str, Any] | None:
    if not isinstance(value, str) or not value.startswith(_SEALED_PREFIX):
        return None
    try:
        raw = _keys().decrypt_at_time(
            value[len(_SEALED_PREFIX):].encode(), ttl=ttl, current_time=int(time.time()),
        )
    except InvalidToken:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get('typ') != typ:
        return None
    return data


def is_sealed_token(value: str) -> bool:
    return value.startswith(_SEALED_PREFIX)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    """Legacy access token: base64 of ``api_token:org_id`` — readable by anyone."""
    return base64.urlsafe_b64encode(f'{api_token}:{org_id}'.encode()).decode()


def decode_access_token(access_token: str) -> tuple[str, str] | None:
    """Decode access_token back to (api_token, org_id). Returns None on failure.

    Sealed tokens are checked for integrity and lifetime. Legacy base64 tokens
    are still accepted so existing connections keep working: whoever holds
    one already holds the API token, which works directly via headers anyway.
    """
    if is_sealed_token(access_token):
        data = _unseal(access_token, 'access', _ACCESS_TTL)
        if not data:
            return None
        return data['t'], data['o']
    try:
        decoded = base64.urlsafe_b64decode(access_token.encode()).decode()
    except (ValueError, UnicodeDecodeError):
        return None
    # Org ID is always a UUID at the end after the last ':'
    last_colon = decoded.rfind(':')
    if last_colon <= 0:
        return None
    api_token = decoded[:last_colon]
    org_id = decoded[last_colon + 1:]
    if not api_token or not org_id:
        return None
    return api_token, org_id


def _verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    """Verify PKCE S256 challenge."""
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return secrets.compare_digest(expected, code_challenge)


def _origin(parsed: Any) -> str:
    host = parsed.hostname or ''
    if ':' in host:
        host = f'[{host}]'
    return f'{parsed.scheme}://{host}' + (f':{parsed.port}' if parsed.port else '')


def _redirect_origins() -> frozenset[str]:
    extra = os.getenv(_REDIRECT_ORIGINS_ENV, '')
    configured = {o.strip().rstrip('/').lower() for o in extra.split(',') if o.strip()}
    return _DEFAULT_REDIRECT_ORIGINS | frozenset(configured)


def _is_trusted_redirect(redirect_uri: str) -> bool:
    """True if a code may be sent to redirect_uri — whatever the client_id says."""
    try:
        parsed = urlparse(redirect_uri)
        parsed.port  # raises on a malformed port
    except ValueError:
        return False
    if not parsed.scheme or not parsed.hostname or parsed.fragment:
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    if parsed.scheme in ('http', 'https') and parsed.hostname in _LOOPBACK_HOSTS:
        return True
    return _origin(parsed) in _redirect_origins()


def _redirect_not_registered(client_id: str, redirect_uri: str) -> bool:
    """True if client_id is one of our registrations and doesn't list redirect_uri.

    Only narrows: whether the redirect is trusted at all is decided by
    ``_is_trusted_redirect`` for every client_id.
    """
    registration = _unseal(client_id, 'client', _CLIENT_TTL)
    if not registration:
        return False
    allowed = registration.get('ru') or []
    return bool(allowed) and redirect_uri not in allowed


def _backend_rejects_token(api_token: str, org_id: str) -> bool:
    """Ask immoJUMP whether the API token is still valid (best effort).

    Only an explicit 401 counts as rejection; an unreachable backend must not
    lock users out — tool calls will surface that error themselves.
    """
    base_url = os.getenv('IMMOJUMP_BASE_URL', 'https://immojump.de')
    try:
        resp = httpx.get(
            f'{base_url}/api/contacts/count',
            params={'organisation_id': org_id},
            headers={'Authorization': f'Bearer {api_token}', 'X-Organisation-Id': org_id},
            timeout=10,
        )
    except (httpx.HTTPError, OSError) as exc:
        logger.warning('Token-Prüfung gegen %s nicht möglich: %s', base_url, exc)
        return False
    return resp.status_code == 401


def _issue_tokens(api_token: str, org_id: str, client_id: str) -> JSONResponse:
    if not _refresh_supported():
        return JSONResponse({
            'access_token': _encode_access_token(api_token, org_id),
            'token_type': 'bearer',
            'scope': 'immojump',
            'expires_in': _LEGACY_EXPIRES_IN,
        }, headers=_TOKEN_HEADERS)
    return JSONResponse({
        'access_token': _seal('access', {'t': api_token, 'o': org_id}),
        'token_type': 'bearer',
        'scope': 'immojump',
        'expires_in': _ACCESS_TTL,
        'refresh_token': _seal('refresh', {'t': api_token, 'o': org_id, 'cid': client_id}),
    }, headers=_TOKEN_HEADERS)


def _grant_error(error: str, description: str) -> JSONResponse:
    return JSONResponse(
        {'error': error, 'error_description': description}, status_code=400, headers=_TOKEN_HEADERS,
    )


def _redirect_error(oauth_params: dict[str, str]) -> HTMLResponse | None:
    """Reasons not to show the form or issue a code, checked on GET and POST."""
    redirect_uri = oauth_params['redirect_uri']
    if not redirect_uri:
        return _html_error('Fehler: redirect_uri fehlt')
    if not _is_trusted_redirect(redirect_uri):
        logger.warning('OAuth: Rücksprung nicht freigegeben: %r', redirect_uri[:200])
        return _html_error(
            f'Fehler: Rücksprung zu {_return_host(redirect_uri)} ist nicht freigegeben. '
            'immoJUMP verbindet sich nur mit bekannten KI-Apps.'
        )
    if _redirect_not_registered(oauth_params['client_id'], redirect_uri):
        return _html_error('Fehler: redirect_uri stimmt nicht mit der Registrierung überein')
    if not oauth_params['code_challenge']:
        return _html_error('Fehler: PKCE (code_challenge) ist erforderlich')
    return None


def _html_error(message: str) -> HTMLResponse:
    return HTMLResponse(
        f'<h1>{html.escape(message)}</h1>', status_code=400, headers=_LOGIN_SECURITY_HEADERS,
    )


def _grant_types() -> list[str]:
    if _refresh_supported():
        return ['authorization_code', 'refresh_token']
    return ['authorization_code']


# ---------------------------------------------------------------------------
# Authorize page
# ---------------------------------------------------------------------------

_PAGE_STYLE = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #f5f7fa; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; padding: 20px; }
        .card { background: white; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.1);
                padding: 40px; max-width: 440px; width: 100%; }
        .logo { text-align: center; margin-bottom: 24px; font-size: 28px; font-weight: 700; color: #1a1a2e; }
        .logo span { color: #4361ee; }
        .subtitle { text-align: center; color: #666; margin-bottom: 24px; font-size: 15px; line-height: 1.5; }
        .note { background: #f0f4ff; border-radius: 10px; padding: 12px 16px; margin-bottom: 24px;
                font-size: 14px; line-height: 1.5; color: #333; }
        .note.warn { background: #fff6e5; }
        label { display: block; font-weight: 600; margin-bottom: 6px; color: #333; font-size: 14px; }
        input { width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 10px;
                font-size: 15px; transition: border-color 0.2s; margin-bottom: 20px; }
        input:focus { outline: none; border-color: #4361ee; }
        .hint { font-size: 12px; color: #888; margin-top: -16px; margin-bottom: 20px; }
        button { width: 100%; padding: 14px; background: #4361ee; color: white; border: none;
                 border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer;
                 transition: background 0.2s; }
        button:hover { background: #3451d1; }
        button.secondary { background: white; color: #4361ee; border: 2px solid #4361ee; margin-top: 12px; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #aaa; }
"""


def _page(body: str) -> HTMLResponse:
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>immoJUMP verbinden</title>
    <style>{_PAGE_STYLE}</style>
</head>
<body>
    <div class="card">
        <div class="logo">immo<span>JUMP</span></div>
{body}
    </div>
</body>
</html>""", headers=_LOGIN_SECURITY_HEADERS)


def _hidden(fields: dict[str, str]) -> str:
    return '\n'.join(
        f'            <input type="hidden" name="{name}" value="{html.escape(value)}">'
        for name, value in fields.items()
    )


def _return_host(redirect_uri: str) -> str:
    return urlparse(redirect_uri).hostname or redirect_uri


def _return_target(redirect_uri: str) -> str:
    """Where the code goes, as the user should read it on the login page."""
    host = _return_host(redirect_uri)
    if host in _LOOPBACK_HOSTS:
        # Any local program can listen there; the client_id proves nothing.
        return 'einem <strong>Programm auf diesem Computer</strong>'
    return f'<strong>{html.escape(host)}</strong>'


def _login_form(oauth_params: dict[str, str]) -> HTMLResponse:
    target = _return_target(oauth_params['redirect_uri'])
    return _page(f"""
        <p class="subtitle">Verbinde deine KI-App mit deinem immoJUMP-Konto.<br>
        Danach geht es zurück zu {target}.</p>
        <p class="note">Den Zugangsschlüssel legst du in immoJUMP unter
        <strong>Einstellungen → Schnittstellen-Zugang → Zugänge für andere</strong> an.
        Soll die KI Objekte, Kontakte oder Deals auch <strong>anlegen oder ändern</strong>,
        wähle dort <strong>„Lesen und ändern“</strong>. Mit „Nur lesen“ kann sie nur abfragen.</p>
        <form method="POST" action="/oauth/authorize">
{_hidden(oauth_params)}

            <label for="api_token">Zugangsschlüssel</label>
            <input type="password" id="api_token" name="api_token"
                   placeholder="ijw_…" autocomplete="off" required>
            <p class="hint">Beginnt mit ijw_ (lesen und ändern) oder ijr_ (nur lesen).</p>

            <label for="org_id">Organisations-ID</label>
            <input type="text" id="org_id" name="org_id"
                   placeholder="abc12345-de67-89ab-cdef-…" required>
            <p class="hint">Steht ebenfalls unter Einstellungen → Schnittstellen-Zugang.</p>

            <button type="submit">Verbinden</button>
        </form>
        <p class="footer">Dein Schlüssel wird nur für diese Verbindung verwendet.</p>""")


def _read_only_confirmation(oauth_params: dict[str, str], api_token: str, org_id: str) -> HTMLResponse:
    return _page(f"""
        <p class="note warn"><strong>Dieser Schlüssel darf nur lesen.</strong><br>
        Die KI kann damit Objekte, Kontakte und Deals abfragen, aber nichts anlegen
        oder ändern — auch nicht in geplanten Aufgaben. Dafür brauchst du einen Zugang mit
        <strong>„Lesen und ändern“</strong> (Einstellungen → Schnittstellen-Zugang →
        Zugänge für andere).</p>
        <form method="GET" action="/oauth/authorize">
{_hidden(oauth_params)}
            <button type="submit">Anderen Schlüssel eingeben</button>
        </form>
        <form method="POST" action="/oauth/authorize">
{_hidden({**oauth_params, 'api_token': api_token, 'org_id': org_id, 'confirm_read_only': '1'})}
            <button type="submit" class="secondary">Trotzdem nur lesend verbinden</button>
        </form>""")


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
        'grant_types_supported': _grant_types(),
        'code_challenge_methods_supported': ['S256'],
        'scopes_supported': ['immojump'],
        'token_endpoint_auth_methods_supported': ['none'],
        'client_id_metadata_document_supported': True,
    })


async def authorize(request: Request) -> Response:
    """Authorization endpoint — shows form or processes submission."""
    if request.method == 'GET':
        params = request.query_params
        oauth_params = {
            'client_id': params.get('client_id', ''),
            'redirect_uri': params.get('redirect_uri', ''),
            'state': params.get('state', ''),
            'code_challenge': params.get('code_challenge', ''),
            'code_challenge_method': params.get('code_challenge_method', ''),
            'scope': params.get('scope', ''),
        }

        error = _redirect_error(oauth_params)
        if error:
            return error
        if oauth_params['code_challenge_method'] != 'S256':
            return _html_error('Fehler: Nur PKCE mit S256 wird unterstützt')
        return _login_form(oauth_params)

    # POST: process form submission
    form = await request.form()
    api_token = str(form.get('api_token', '')).strip()
    org_id = str(form.get('org_id', '')).strip()
    oauth_params = {
        'client_id': str(form.get('client_id', '')).strip(),
        'redirect_uri': str(form.get('redirect_uri', '')).strip(),
        'state': str(form.get('state', '')).strip(),
        'code_challenge': str(form.get('code_challenge', '')).strip(),
        # Missing on forms rendered before this version; codes are verified
        # as S256 either way, so only a wrong value is refused.
        'code_challenge_method': str(form.get('code_challenge_method', 'S256')).strip() or 'S256',
        'scope': str(form.get('scope', '')).strip(),
    }
    redirect_uri = oauth_params['redirect_uri']

    if not api_token or not org_id:
        return _html_error('Fehler: Zugangsschlüssel und Organisations-ID sind erforderlich')
    error = _redirect_error(oauth_params)
    if error:
        return error
    if oauth_params['code_challenge_method'] != 'S256':
        return _html_error('Fehler: Nur PKCE mit S256 wird unterstützt')

    if api_token.startswith(_READ_ONLY_TOKEN_PREFIX) and form.get('confirm_read_only') != '1':
        return _read_only_confirmation(oauth_params, api_token, org_id)

    if _backend_rejects_token(api_token, org_id):
        return HTMLResponse(
            '<h1>Ungültiger Zugangsschlüssel</h1>'
            '<p>Bitte prüfe deinen Zugangsschlüssel und versuche es erneut.</p>',
            status_code=400,
            headers=_LOGIN_SECURITY_HEADERS,
        )

    code = _seal('code', {
        't': api_token,
        'o': org_id,
        'cc': oauth_params['code_challenge'],
        'ru': redirect_uri,
        'cid': oauth_params['client_id'],
    })

    # Redirect back to client
    query = {'code': code}
    if oauth_params['state']:
        query['state'] = oauth_params['state']
    separator = '&' if '?' in redirect_uri else '?'
    return RedirectResponse(f'{redirect_uri}{separator}{urlencode(query)}', status_code=302)


def _redeem_once(code: str) -> bool:
    """Single use per pod; False if this code was already redeemed here."""
    now = time.time()
    for key in [k for k, expires in _used_codes.items() if expires < now]:
        del _used_codes[key]
    key = hashlib.sha256(code.encode()).hexdigest()
    if key in _used_codes:
        return False
    _used_codes[key] = now + _CODE_TTL + 60
    return True


def _exchange_code(body: dict[str, Any]) -> JSONResponse:
    code = str(body.get('code', ''))
    code_verifier = str(body.get('code_verifier', ''))
    redirect_uri = str(body.get('redirect_uri', ''))

    code_data = _unseal(code, 'code', _CODE_TTL)
    if not code_data or not _redeem_once(code):
        return _grant_error('invalid_grant', 'Code expired or invalid')

    # /oauth/authorize only mints codes with a challenge; one without is
    # older than that rule or forged.
    if not code_data['cc']:
        return _grant_error('invalid_grant', 'Code was issued without PKCE')
    if not code_verifier:
        return _grant_error('invalid_grant', 'code_verifier required')
    if not _verify_pkce(code_verifier, code_data['cc']):
        return _grant_error('invalid_grant', 'PKCE verification failed')

    if redirect_uri and redirect_uri != code_data['ru']:
        return _grant_error('invalid_grant', 'redirect_uri mismatch')

    return _issue_tokens(code_data['t'], code_data['o'], code_data['cid'])


def _exchange_refresh_token(body: dict[str, Any]) -> JSONResponse:
    refresh_token = str(body.get('refresh_token', ''))
    if not refresh_token:
        return _grant_error('invalid_request', 'refresh_token required')

    data = _unseal(refresh_token, 'refresh', _REFRESH_TTL)
    if not data:
        return _grant_error('invalid_grant', 'Refresh token expired or invalid')

    client_id = str(body.get('client_id', ''))
    if client_id and data['cid'] and client_id != data['cid']:
        return _grant_error('invalid_grant', 'Refresh token was issued to another client')

    # The access key may have been deleted in immoJUMP since the last login.
    if _backend_rejects_token(data['t'], data['o']):
        return _grant_error('invalid_grant', 'Der Zugangsschlüssel wurde in immoJUMP widerrufen.')

    return _issue_tokens(data['t'], data['o'], data['cid'])


async def token(request: Request) -> JSONResponse:
    """Token endpoint — authorization_code and refresh_token grants."""
    # Accept both form and JSON
    content_type = request.headers.get('content-type', '')
    if 'json' in content_type:
        try:
            body = await request.json()
        except ValueError:
            body = None
    else:
        body = dict(await request.form())
    if not isinstance(body, dict):
        return _grant_error('invalid_request', 'Body must be form-encoded or a JSON object')

    grant_type = body.get('grant_type', '')
    if grant_type == 'authorization_code':
        return _exchange_code(body)
    if grant_type == 'refresh_token' and _refresh_supported():
        return _exchange_refresh_token(body)
    return JSONResponse({'error': 'unsupported_grant_type'}, status_code=400, headers=_TOKEN_HEADERS)


async def register(request: Request) -> JSONResponse:
    """RFC 7591: Dynamic Client Registration.

    Open to anyone, so it only keeps redirect_uris that /oauth/authorize
    would accept anyway (RFC 7591 §3.2.1 lets the server replace requested
    values) and refuses a registration left with none. The issued client_id
    carries them sealed, so the exact-match check on /oauth/authorize works
    on every pod and after restarts. A client_id chosen by the client is
    echoed back for compatibility but cannot be bound to redirect_uris.
    """
    try:
        body = await request.json()
    except ValueError:
        body = {}
    if not isinstance(body, dict):
        body = {}

    client_name = body.get('client_name', 'MCP Client')
    redirect_uris = body.get('redirect_uris', [])
    if not isinstance(redirect_uris, list):
        redirect_uris = []
    trusted = [u for u in redirect_uris if isinstance(u, str) and _is_trusted_redirect(u)]
    if redirect_uris and not trusted:
        return JSONResponse({
            'error': 'invalid_redirect_uri',
            'error_description': 'No redirect_uri points to a trusted origin.',
        }, status_code=400)
    redirect_uris = trusted
    client_id = body.get('client_id') or _seal('client', {'ru': redirect_uris})

    return JSONResponse({
        'client_id': client_id,
        'client_name': client_name,
        'redirect_uris': redirect_uris,
        'grant_types': _grant_types(),
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
