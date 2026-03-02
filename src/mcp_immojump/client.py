from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


ALLOWED_BASE_URLS = {
    'http://localhost:8081',
    'https://beta.immojump.de',
    'https://immojump.de',
}


class ImmojumpAPIError(RuntimeError):
    """Raised when the ImmoJUMP API returns an error response."""

    def __init__(self, status_code: int, message: str):
        super().__init__(f'ImmoJUMP API error ({status_code}): {message}')
        self.status_code = status_code
        self.message = message


@dataclass(frozen=True)
class ImmojumpCredentials:
    base_url: str
    token: str
    organisation_id: str

    def __post_init__(self) -> None:
        normalized_base_url = normalize_base_url(self.base_url)
        if normalized_base_url not in ALLOWED_BASE_URLS:
            allowed = ', '.join(sorted(ALLOWED_BASE_URLS))
            raise ValueError(f'base_url not allowed: {normalized_base_url}. Allowed: {allowed}')
        if not str(self.token or '').strip():
            raise ValueError('token is required')
        if not str(self.organisation_id or '').strip():
            raise ValueError('organisation_id is required')

        object.__setattr__(self, 'base_url', normalized_base_url)
        object.__setattr__(self, 'token', str(self.token).strip())
        object.__setattr__(self, 'organisation_id', str(self.organisation_id).strip())


def normalize_base_url(base_url: str) -> str:
    return str(base_url or '').strip().rstrip('/')


class ImmojumpAPIClient:
    def __init__(
        self,
        credentials: ImmojumpCredentials,
        *,
        timeout_seconds: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.credentials = credentials
        self._client = httpx.Client(
            base_url=credentials.base_url,
            timeout=timeout_seconds,
            transport=transport,
            headers={
                'Authorization': f'Bearer {credentials.token}',
                'Accept': 'application/json',
                'X-Organisation-Id': credentials.organisation_id,
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> 'ImmojumpAPIClient':
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs) -> Any:
        response = self._client.request(method, path, **kwargs)
        if response.status_code >= 400:
            try:
                payload = response.json()
                message = payload.get('error') or payload.get('message') or str(payload)
            except Exception:
                message = response.text
            raise ImmojumpAPIError(response.status_code, message)

        if not response.content:
            return {}
        try:
            return response.json()
        except Exception:
            return {'raw': response.text}

    def connection_test(self) -> Any:
        return self._request(
            'GET',
            '/api/contacts/count',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def contacts_import_unified(
        self,
        *,
        source_type: str,
        dry_run: bool,
        smart: bool = True,
        source_text: str | None = None,
        file_path: str | None = None,
        sheet_name: str | None = None,
        mapping_overrides: dict[str, Any] | None = None,
    ) -> Any:
        if file_path:
            file_name = Path(file_path).name
            with open(file_path, 'rb') as fh:
                files = {'file': (file_name, fh, 'application/octet-stream')}
                data = {
                    'organisation_id': self.credentials.organisation_id,
                    'source_type': source_type,
                    'dry_run': str(bool(dry_run)).lower(),
                    'smart': str(bool(smart)).lower(),
                }
                if source_text:
                    data['source_text'] = source_text
                if sheet_name:
                    data['sheet_name'] = sheet_name
                if mapping_overrides:
                    import json

                    data['mapping_overrides'] = json.dumps(mapping_overrides)
                return self._request('POST', '/api/contacts/import-unified', data=data, files=files)

        payload: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
            'source_type': source_type,
            'dry_run': bool(dry_run),
            'smart': bool(smart),
        }
        if source_text is not None:
            payload['source_text'] = source_text
        if sheet_name:
            payload['sheet_name'] = sheet_name
        if mapping_overrides is not None:
            payload['mapping_overrides'] = mapping_overrides
        return self._request('POST', '/api/contacts/import-unified', json=payload)

    def contacts_job_status(self, *, job_id: str) -> Any:
        return self._request('GET', f'/api/contacts/import-jobs/{job_id}')

    def contacts_job_resume(self, *, job_id: str) -> Any:
        return self._request('POST', f'/api/contacts/import-jobs/{job_id}/resume')

    def contacts_job_cancel(self, *, job_id: str) -> Any:
        return self._request('POST', f'/api/contacts/import-jobs/{job_id}/cancel')

    def contacts_duplicates_preview(
        self,
        *,
        by: str = 'email,phone,mobile,name',
        min_count: int = 2,
        limit_groups: int = 200,
        ignore_generic_names: bool = True,
    ) -> Any:
        return self._request(
            'GET',
            '/api/contacts/duplicates',
            params={
                'organisation_id': self.credentials.organisation_id,
                'by': by,
                'min_count': int(min_count),
                'limit_groups': int(limit_groups),
                'ignore_generic_names': 'true' if ignore_generic_names else 'false',
            },
        )

    def contacts_merge_apply(self, *, primary_id: str, duplicate_ids: list[str]) -> Any:
        return self._request(
            'POST',
            '/api/contacts/merge',
            json={
                'primary_id': primary_id,
                'duplicate_ids': duplicate_ids,
            },
        )

    def pipeline_count(self) -> Any:
        return self._request(
            'GET',
            f'/api/pipelines/{self.credentials.organisation_id}/pipelines/count',
        )

    def pipeline_list(self) -> Any:
        return self._request(
            'GET',
            f'/api/pipelines/{self.credentials.organisation_id}/pipelines',
        )

    def pipeline_get(self, *, pipeline_id: int | str) -> Any:
        return self._request('GET', f'/api/pipelines/pipelines/{pipeline_id}')

    def pipeline_create(self, *, data: dict[str, Any]) -> Any:
        return self._request(
            'POST',
            f'/api/pipelines/{self.credentials.organisation_id}/pipelines',
            json=data,
        )

    def pipeline_update(self, *, pipeline_id: int | str, data: dict[str, Any]) -> Any:
        return self._request(
            'PUT',
            f'/api/pipelines/pipelines/{pipeline_id}',
            json=data,
        )

    def pipeline_delete(self, *, pipeline_id: int | str) -> Any:
        return self._request('DELETE', f'/api/pipelines/pipelines/{pipeline_id}')

    def pipeline_export(self, *, pipeline_id: int | str, format: str = 'yaml') -> Any:
        return self._request(
            'GET',
            f'/api/pipelines/pipelines/{pipeline_id}/export',
            params={'format': format},
        )

    def pipeline_import(self, *, payload: dict[str, Any] | str) -> Any:
        params = {'organisation_id': self.credentials.organisation_id}
        if isinstance(payload, str):
            return self._request(
                'POST',
                '/api/pipelines/pipelines/import',
                content=payload.encode('utf-8'),
                params=params,
                headers={'Content-Type': 'application/x-yaml'},
            )
        return self._request(
            'POST',
            '/api/pipelines/pipelines/import',
            json=payload,
            params=params,
        )

    def pipeline_statuses_list(self, *, pipeline_id: int | str) -> Any:
        return self._request(
            'GET',
            f'/api/pipelines/pipelines/{pipeline_id}/statuses',
        )

    def pipeline_status_create(self, *, pipeline_id: int | str, data: dict[str, Any]) -> Any:
        return self._request(
            'POST',
            f'/api/pipelines/pipelines/{pipeline_id}/statuses',
            json=data,
        )

    def pipeline_status_delete(self, *, pipeline_id: int | str, status_id: int | str) -> Any:
        return self._request(
            'DELETE',
            f'/api/pipelines/pipelines/{pipeline_id}/statuses/{status_id}',
        )

    def status_list(self) -> Any:
        return self._request(
            'GET',
            '/api/statuses/statuses',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def status_update(self, *, status_id: int | str, data: dict[str, Any]) -> Any:
        return self._request(
            'PUT',
            f'/api/statuses/statuses/{status_id}',
            json=data,
        )

    def status_delete(self, *, status_id: int | str) -> Any:
        return self._request('DELETE', f'/api/statuses/statuses/{status_id}')

    def status_swap_order(
        self,
        *,
        current_status_id: int | str,
        target_status_id: int | str,
        current_status_order: int,
        target_status_order: int,
    ) -> Any:
        return self._request(
            'PUT',
            f'/api/statuses/statuses/swap/{current_status_id}/{target_status_id}',
            json={
                'current_status_order': current_status_order,
                'target_status_order': target_status_order,
            },
        )

    def status_inbound_aliases_list(self, *, status_id: int | str) -> Any:
        return self._request(
            'GET',
            f'/api/statuses/statuses/{status_id}/inbound-aliases',
        )

    def status_inbound_alias_create(self, *, status_id: int | str, prefix: str | None = None) -> Any:
        payload: dict[str, Any] = {}
        if prefix:
            payload['prefix'] = prefix
        return self._request(
            'POST',
            f'/api/statuses/statuses/{status_id}/inbound-aliases',
            json=payload,
        )

    def activity_templates_list(self) -> Any:
        return self._request(
            'GET',
            '/api/activity-templates/activity_templates',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def activity_templates_recurring_list(self) -> Any:
        return self._request(
            'GET',
            '/api/activity-templates/activity_templates/recurring',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def activity_templates_by_status(self, *, status_id: int | str) -> Any:
        return self._request(
            'GET',
            f'/api/activity-templates/activity_templates/status/{status_id}',
        )

    def activity_template_get(self, *, template_id: str) -> Any:
        return self._request(
            'GET',
            f'/api/activity-templates/activity_templates/{template_id}',
        )

    def activity_template_create(self, *, data: dict[str, Any]) -> Any:
        payload = dict(data or {})
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request(
            'POST',
            '/api/activity-templates/activity_templates',
            json=payload,
        )

    def activity_template_update(self, *, template_id: str, data: dict[str, Any]) -> Any:
        return self._request(
            'PUT',
            f'/api/activity-templates/activity_templates/{template_id}',
            json=data,
        )

    def activity_template_delete(self, *, template_id: str) -> Any:
        return self._request(
            'DELETE',
            f'/api/activity-templates/activity_templates/{template_id}',
        )

    def activity_templates_batch_move(self, *, template_ids: list[str], target_status_id: int | str) -> Any:
        return self._request(
            'POST',
            '/api/activity-templates/activity_templates/status/batch_move',
            json={
                'template_ids': template_ids,
                'target_status_id': target_status_id,
            },
        )
