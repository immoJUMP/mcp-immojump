from __future__ import annotations

import copy
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


ALLOWED_BASE_URLS = {
    'http://localhost:8081',
    'https://beta.immojump.de',
    'https://immojump.de',
}


logger = logging.getLogger(__name__)


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


def _normalize_id(value: Any) -> str:
    return str(value or '').strip()


def _canonical_timestamp(value: Any) -> str | None:
    text = str(value or '').strip()
    if not text:
        return None
    try:
        if text.endswith('Z'):
            text = text[:-1] + '+00:00'
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except ValueError:
        return str(value).strip()


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

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connection_test(self) -> Any:
        return self._request(
            'GET',
            '/api/contacts/count',
            params={'organisation_id': self.credentials.organisation_id},
        )

    # ------------------------------------------------------------------
    # Immobilien / Properties
    # ------------------------------------------------------------------

    def immobilien_list(
        self,
        *,
        page: int = 1,
        per_page: int = 25,
    ) -> Any:
        return self._request(
            'GET',
            '/api/v2/immobilien',
            params={
                'organisation_id': self.credentials.organisation_id,
                'page': page,
                'per_page': per_page,
            },
        )

    def immobilien_search(
        self,
        *,
        search: str | None = None,
        status_ids: list[str] | None = None,
        tag_ids: list[str] | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Any:
        params: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
            'page': page,
            'per_page': per_page,
        }
        if search:
            params['search'] = search
        if status_ids:
            params['status_ids'] = ','.join(str(s) for s in status_ids)
        if tag_ids:
            params['tag_ids'] = ','.join(str(t) for t in tag_ids)
        return self._request('GET', '/api/v2/immobilien/search', params=params)

    def immobilien_count(self) -> Any:
        return self._request(
            'GET',
            '/api/immobilien/count',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def immobilien_get(self, *, immobilie_id: str) -> Any:
        return self._request('GET', f'/api/v2/immobilien/{immobilie_id}')

    def immobilien_create(self, *, data: dict[str, Any]) -> Any:
        payload = dict(data)
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request('POST', '/api/v2/immobilien', json=payload)

    def immobilien_update(self, *, immobilie_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/v2/immobilien/{immobilie_id}', json=data)

    def immobilien_patch(self, *, immobilie_id: str, data: dict[str, Any]) -> Any:
        return self._request('PATCH', f'/api/v2/immobilien/{immobilie_id}', json=data)

    def immobilien_delete(self, *, immobilie_id: str) -> Any:
        return self._request('DELETE', f'/api/v2/immobilien/{immobilie_id}')

    def immobilien_duplicate(self, *, immobilie_id: str) -> Any:
        return self._request('POST', f'/api/v2/immobilien/{immobilie_id}/duplicate')

    def immobilien_transfer(self, *, immobilie_id: str, target_organisation_id: str) -> Any:
        return self._request(
            'POST',
            f'/api/v2/immobilien/{immobilie_id}/transfer',
            json={'target_organisation_id': target_organisation_id},
        )

    def immobilien_contacts(self, *, immobilie_id: str) -> Any:
        return self._request('GET', f'/api/v2/immobilien/{immobilie_id}/contacts')

    # ------------------------------------------------------------------
    # Contacts – CRUD
    # ------------------------------------------------------------------

    def contacts_list(
        self,
        *,
        page: int = 1,
        per_page: int = 25,
        search: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
            'page': page,
            'per_page': per_page,
        }
        if search:
            params['search'] = search
        return self._request('GET', '/api/contacts', params=params)

    def contacts_get(self, *, contact_id: str) -> Any:
        return self._request('GET', f'/api/contacts/{contact_id}')

    def contacts_create(self, *, data: dict[str, Any]) -> Any:
        payload = dict(data)
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request('POST', '/api/contacts', json=payload)

    def contacts_update(self, *, contact_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/contacts/{contact_id}', json=data)

    def contacts_update_status(self, *, contact_id: str, status: str) -> Any:
        return self._request('PUT', f'/api/contacts/{contact_id}/status', json={'status': status})

    def contacts_delete(self, *, contact_id: str) -> Any:
        return self._request('DELETE', f'/api/contacts/{contact_id}')

    def contacts_count(self) -> Any:
        return self._request(
            'GET',
            '/api/contacts/count',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def contacts_bulk_delete(self, *, contact_ids: list[str]) -> Any:
        return self._request(
            'POST',
            '/api/contacts/bulk-delete',
            json={'contact_ids': contact_ids},
        )

    def contacts_get_immobilien(self, *, contact_id: str) -> Any:
        return self._request('GET', f'/api/contacts/{contact_id}/immobilien')

    def contacts_get_activities(self, *, contact_id: str) -> Any:
        return self._request('GET', f'/api/contacts/{contact_id}/activities')

    def contacts_merge_logs(self) -> Any:
        return self._request(
            'GET',
            '/api/contacts/merge/logs',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def contacts_merge_restore(self, *, merge_id: str) -> Any:
        return self._request('POST', '/api/contacts/merge/restore', json={'merge_id': merge_id})

    # ------------------------------------------------------------------
    # Contacts – Import (existing)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Activities
    # ------------------------------------------------------------------

    def activities_list(
        self,
        *,
        page: int = 1,
        per_page: int = 25,
        search: str | None = None,
        status: str | None = None,
        type: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
            'page': page,
            'per_page': per_page,
        }
        if search:
            params['search'] = search
        if status:
            params['status'] = status
        if type:
            params['type'] = type
        return self._request('GET', '/api/activities/activities', params=params)

    def activities_get(self, *, activity_id: str) -> Any:
        return self._request('GET', f'/api/activities/activities/{activity_id}')

    def activities_create(self, *, data: dict[str, Any]) -> Any:
        payload = dict(data)
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request('POST', '/api/activities/activities', json=payload)

    def activities_create_for_property(self, *, immobilie_id: str, data: dict[str, Any]) -> Any:
        payload = dict(data)
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request(
            'POST',
            f'/api/activities/activities/immobilie/{immobilie_id}',
            json=payload,
        )

    def activities_update(self, *, activity_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/activities/activities/{activity_id}', json=data)

    def activities_delete(self, *, activity_id: str) -> Any:
        return self._request('DELETE', f'/api/activities/activities/{activity_id}')

    def activities_list_by_property(self, *, immobilie_id: str) -> Any:
        return self._request('GET', f'/api/activities/activities/immobilie/{immobilie_id}')

    def activities_statistics(self) -> Any:
        return self._request(
            'GET',
            '/api/activities/activities/statistics',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def activities_structure_description(self, *, text: str) -> Any:
        return self._request(
            'POST',
            '/api/activities/structure-description',
            json={'text': text, 'organisation_id': self.credentials.organisation_id},
        )

    # ------------------------------------------------------------------
    # Activity Templates (existing)
    # ------------------------------------------------------------------

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
        payload = dict(data or {})
        replace_outcomes = bool(payload.pop('replace_outcomes', False))
        dry_run = bool(payload.pop('dry_run', False))
        if_updated_at = payload.pop('if_updated_at', None)

        current_template = self.activity_template_get(template_id=template_id)
        if not isinstance(current_template, dict):
            raise ImmojumpAPIError(500, 'Unexpected activity template response format')

        self._assert_if_updated_at_matches(current_template=current_template, if_updated_at=if_updated_at)

        if 'outcomes' in payload:
            incoming_outcomes = payload.get('outcomes')
            if incoming_outcomes is None:
                incoming_outcomes = []
            if not isinstance(incoming_outcomes, list):
                raise ImmojumpAPIError(400, 'outcomes must be a list')

            existing_outcomes = current_template.get('outcomes') or []
            if not isinstance(existing_outcomes, list):
                existing_outcomes = []
            if replace_outcomes:
                resolved_outcomes = copy.deepcopy(incoming_outcomes)
            else:
                resolved_outcomes = self._merge_outcomes_by_id(
                    existing_outcomes=existing_outcomes,
                    incoming_outcomes=incoming_outcomes,
                )
            self._validate_outcome_actions(outcomes=resolved_outcomes)
            payload['outcomes'] = resolved_outcomes

        preview = self._build_update_preview(
            template_id=template_id,
            current_template=current_template,
            update_payload=payload,
            replace_outcomes=replace_outcomes,
        )
        self._log_nested_update_changes(template_id=template_id, preview=preview)

        if dry_run:
            return preview

        return self._request(
            'PUT',
            f'/api/activity-templates/activity_templates/{template_id}',
            json=payload,
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

    # ------------------------------------------------------------------
    # Deals
    # ------------------------------------------------------------------

    def deals_list(
        self,
        *,
        page: int = 1,
        per_page: int = 25,
        pipeline_id: str | None = None,
        status_id: str | None = None,
        search: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
            'page': page,
            'per_page': per_page,
        }
        if pipeline_id:
            params['pipeline_id'] = pipeline_id
        if status_id:
            params['status_id'] = status_id
        if search:
            params['search'] = search
        return self._request('GET', '/api/deals', params=params)

    def deals_get(self, *, deal_id: str) -> Any:
        return self._request('GET', f'/api/deals/{deal_id}')

    def deals_create(self, *, data: dict[str, Any]) -> Any:
        payload = dict(data)
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request('POST', '/api/deals', json=payload)

    def deals_update(self, *, deal_id: str, data: dict[str, Any]) -> Any:
        return self._request('PATCH', f'/api/deals/{deal_id}', json=data)

    # ------------------------------------------------------------------
    # Tickets
    # ------------------------------------------------------------------

    def tickets_statuses(self) -> Any:
        return self._request(
            'GET',
            '/api/tickets/statuses',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def tickets_list(
        self,
        *,
        page: int = 1,
        per_page: int = 25,
        status: str | None = None,
        search: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
            'page': page,
            'per_page': per_page,
        }
        if status:
            params['status'] = status
        if search:
            params['search'] = search
        return self._request('GET', '/api/tickets', params=params)

    def tickets_get(self, *, ticket_id: str) -> Any:
        return self._request('GET', f'/api/tickets/{ticket_id}')

    def tickets_create(self, *, data: dict[str, Any]) -> Any:
        payload = dict(data)
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request('POST', '/api/tickets', json=payload)

    def tickets_update(self, *, ticket_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/tickets/{ticket_id}', json=data)

    def tickets_delete(self, *, ticket_id: str) -> Any:
        return self._request('DELETE', f'/api/tickets/{ticket_id}')

    def tickets_change_status(self, *, ticket_id: str, status: str) -> Any:
        return self._request('PATCH', f'/api/tickets/{ticket_id}/status', json={'status': status})

    def tickets_list_comments(self, *, ticket_id: str) -> Any:
        return self._request('GET', f'/api/tickets/{ticket_id}/activities')

    def tickets_add_comment(self, *, ticket_id: str, data: dict[str, Any]) -> Any:
        return self._request('POST', f'/api/tickets/{ticket_id}/activities', json=data)

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    def documents_list(
        self,
        *,
        immobilie_id: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Any:
        params: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
            'page': page,
            'per_page': per_page,
        }
        if immobilie_id:
            params['immobilie_id'] = immobilie_id
        return self._request('GET', '/api/documents/documents', params=params)

    def documents_delete(self, *, document_id: str) -> Any:
        return self._request('DELETE', f'/api/documents/documents/{document_id}')

    def documents_rename(self, *, document_id: str, name: str) -> Any:
        return self._request('PUT', f'/api/documents/documents/{document_id}/rename', json={'name': name})

    def documents_analyze(self, *, document_id: str) -> Any:
        return self._request('POST', f'/api/documents/documents/{document_id}/analyze')

    def documents_analyze_details(self, *, document_id: str) -> Any:
        return self._request('POST', f'/api/documents/documents/{document_id}/analyze/details')

    def documents_mark_reviewed(self, *, document_id: str) -> Any:
        return self._request('POST', f'/api/documents/documents/{document_id}/mark-reviewed')

    def documents_analysis_results(
        self,
        *,
        immobilie_id: str | None = None,
        document_id: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
        }
        if immobilie_id:
            params['immobilie_id'] = immobilie_id
        if document_id:
            params['document_id'] = document_id
        return self._request('GET', '/api/documents/analysis-results', params=params)

    def documents_clear_analysis(self, *, immobilie_id: str | None = None) -> Any:
        params: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
        }
        if immobilie_id:
            params['immobilie_id'] = immobilie_id
        return self._request('DELETE', '/api/documents/analysis-results', params=params)

    # ------------------------------------------------------------------
    # Loans
    # ------------------------------------------------------------------

    def loans_list(self) -> Any:
        return self._request(
            'GET',
            '/api/loans',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def loans_create(self, *, data: dict[str, Any]) -> Any:
        payload = dict(data)
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request('POST', '/api/loans', json=payload)

    def loans_update(self, *, loan_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/loans/{loan_id}', json=data)

    def loans_delete(self, *, loan_id: str) -> Any:
        return self._request('DELETE', f'/api/loans/{loan_id}')

    def loans_list_by_property(self, *, immobilie_id: str) -> Any:
        return self._request('GET', f'/api/immobilien/{immobilie_id}/loans')

    def loans_outstanding(self, *, loan_ids: list[str]) -> Any:
        return self._request('POST', '/api/loans/outstanding', json={'loan_ids': loan_ids})

    # ------------------------------------------------------------------
    # Units (Multi-family)
    # ------------------------------------------------------------------

    def units_list(self, *, immobilie_id: str) -> Any:
        return self._request('GET', f'/api/units/immobilie/{immobilie_id}/units')

    def units_count(self) -> Any:
        return self._request(
            'GET',
            '/api/units/units/count',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def units_create(self, *, immobilie_id: str, data: dict[str, Any]) -> Any:
        return self._request('POST', f'/api/units/unit/{immobilie_id}', json=data)

    def units_update(self, *, unit_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/units/unit/{unit_id}', json=data)

    def units_delete(self, *, unit_id: str) -> Any:
        return self._request('DELETE', f'/api/units/unit/{unit_id}')

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def tags_list(self, *, entity_type: str | None = None) -> Any:
        params: dict[str, Any] = {}
        if entity_type:
            params['entity_type'] = entity_type
        return self._request(
            'GET',
            f'/api/{self.credentials.organisation_id}/tags',
            params=params,
        )

    def tags_create(self, *, data: dict[str, Any]) -> Any:
        return self._request(
            'POST',
            f'/api/{self.credentials.organisation_id}/tags',
            json=data,
        )

    def tags_update(self, *, tag_id: str, data: dict[str, Any]) -> Any:
        return self._request(
            'PUT',
            f'/api/{self.credentials.organisation_id}/tags/{tag_id}',
            json=data,
        )

    def tags_delete(self, *, tag_id: str) -> Any:
        return self._request('DELETE', f'/api/tags/{tag_id}')

    def tags_get_entity(self, *, entity_type: str, entity_id: str) -> Any:
        return self._request('GET', f'/api/tags/{entity_type}/{entity_id}')

    def tags_update_entity(self, *, entity_type: str, entity_id: str, tag_ids: list[str]) -> Any:
        return self._request(
            'PUT',
            f'/api/tags/{entity_type}/{entity_id}',
            json={'tag_ids': tag_ids},
        )

    # ------------------------------------------------------------------
    # Pipelines (existing)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Statuses (existing)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Organisation
    # ------------------------------------------------------------------

    def organisation_list(self) -> Any:
        return self._request('GET', '/api/organisations')

    def organisation_get(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}')

    def organisation_update(self, *, org_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/organisations/{org_id}', json=data)

    def organisation_members(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/members')

    def organisation_update_member(self, *, org_id: str, user_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/organisations/{org_id}/members/{user_id}', json=data)

    def organisation_update_member_profile(self, *, org_id: str, user_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/organisations/{org_id}/members/{user_id}/profile', json=data)

    def organisation_update_member_roles(self, *, org_id: str, user_id: str, role_ids: list[str]) -> Any:
        return self._request(
            'PUT',
            f'/api/organisations/{org_id}/members/{user_id}/roles',
            json={'role_ids': role_ids},
        )

    def organisation_remove_member(self, *, org_id: str, user_id: str) -> Any:
        return self._request('DELETE', f'/api/organisations/{org_id}/members/{user_id}')

    def organisation_invites(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/invites')

    def organisation_invite(self, *, org_id: str, data: dict[str, Any]) -> Any:
        return self._request('POST', f'/api/organisations/{org_id}/invites', json=data)

    def organisation_cancel_invite(self, *, org_id: str, invite_id: str) -> Any:
        return self._request('DELETE', f'/api/organisations/{org_id}/invites/{invite_id}')

    def organisation_roles(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/roles')

    def organisation_create_role(self, *, org_id: str, data: dict[str, Any]) -> Any:
        return self._request('POST', f'/api/organisations/{org_id}/roles', json=data)

    def organisation_update_role(self, *, org_id: str, role_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/organisations/{org_id}/roles/{role_id}', json=data)

    def organisation_delete_role(self, *, org_id: str, role_id: str) -> Any:
        return self._request('DELETE', f'/api/organisations/{org_id}/roles/{role_id}')

    def organisation_report_design(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/report-design')

    def organisation_rebuild_report_design(self, *, org_id: str) -> Any:
        return self._request('POST', f'/api/organisations/{org_id}/report-design')

    # ------------------------------------------------------------------
    # Organisation Feed
    # ------------------------------------------------------------------

    def feed_list(
        self,
        *,
        cursor: str | None = None,
        channel_id: str | None = None,
        limit: int = 25,
    ) -> Any:
        params: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
            'limit': limit,
        }
        if cursor:
            params['cursor'] = cursor
        if channel_id:
            params['channel_id'] = channel_id
        return self._request('GET', '/api/organisation-feed', params=params)

    def feed_by_context(
        self,
        *,
        context_type: str,
        context_id: str,
    ) -> Any:
        return self._request(
            'GET',
            '/api/organisation-feed/by-context',
            params={
                'organisation_id': self.credentials.organisation_id,
                'context_type': context_type,
                'context_id': context_id,
            },
        )

    def feed_create_post(self, *, data: dict[str, Any]) -> Any:
        payload = dict(data)
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request('POST', '/api/organisation-feed/post', json=payload)

    def feed_edit_post(self, *, event_id: str, data: dict[str, Any]) -> Any:
        return self._request('PATCH', f'/api/organisation-feed/{event_id}', json=data)

    def feed_toggle_reaction(self, *, event_id: str, emoji: str) -> Any:
        return self._request(
            'POST',
            f'/api/organisation-feed/{event_id}/reactions',
            json={'emoji': emoji},
        )

    def feed_list_comments(self, *, event_id: str) -> Any:
        return self._request('GET', f'/api/organisation-feed/{event_id}/comments')

    def feed_add_comment(self, *, event_id: str, data: dict[str, Any]) -> Any:
        payload = dict(data)
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request('POST', f'/api/organisation-feed/{event_id}/comments', json=payload)

    def feed_edit_comment(self, *, comment_id: str, data: dict[str, Any]) -> Any:
        return self._request('PATCH', f'/api/organisation-feed/comments/{comment_id}', json=data)

    def feed_delete_comment(self, *, comment_id: str) -> Any:
        return self._request('DELETE', f'/api/organisation-feed/comments/{comment_id}')

    def feed_mark_seen(self, *, event_id: str) -> Any:
        return self._request('POST', f'/api/organisation-feed/{event_id}/seen')

    def feed_comment_object(self, *, data: dict[str, Any]) -> Any:
        payload = dict(data)
        payload.setdefault('organisation_id', self.credentials.organisation_id)
        return self._request('POST', '/api/organisation-feed/comment-object', json=payload)

    def feed_channels(self) -> Any:
        return self._request(
            'GET',
            '/api/organisation-feed/channels',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def feed_create_channel(self, *, name: str) -> Any:
        return self._request(
            'POST',
            '/api/organisation-feed/channels',
            json={'name': name, 'organisation_id': self.credentials.organisation_id},
        )

    def feed_rename_channel(self, *, channel_id: str, name: str) -> Any:
        return self._request(
            'PATCH',
            f'/api/organisation-feed/channels/{channel_id}',
            json={'name': name},
        )

    def feed_delete_channel(self, *, channel_id: str) -> Any:
        return self._request('DELETE', f'/api/organisation-feed/channels/{channel_id}')

    # ------------------------------------------------------------------
    # Email Messages
    # ------------------------------------------------------------------

    def email_list(
        self,
        *,
        folder: str | None = None,
        page: int = 1,
        per_page: int = 25,
        search: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {
            'organisation_id': self.credentials.organisation_id,
            'page': page,
            'per_page': per_page,
        }
        if folder:
            params['folder'] = folder
        if search:
            params['search'] = search
        return self._request('GET', '/api/email-messages', params=params)

    def email_get(self, *, message_id: str) -> Any:
        return self._request('GET', f'/api/email-messages/{message_id}')

    def email_thread(self, *, thread_id: str) -> Any:
        return self._request('GET', f'/api/email-messages/threads/{thread_id}')

    def email_mark_read(self, *, message_ids: list[str], read: bool = True) -> Any:
        return self._request(
            'POST',
            '/api/email-messages/mark-read',
            json={'message_ids': message_ids, 'read': read},
        )

    def email_mark_starred(self, *, message_ids: list[str], starred: bool = True) -> Any:
        return self._request(
            'POST',
            '/api/email-messages/mark-starred',
            json={'message_ids': message_ids, 'starred': starred},
        )

    def email_archive(self, *, message_ids: list[str]) -> Any:
        return self._request(
            'POST',
            '/api/email-messages/archive',
            json={'message_ids': message_ids},
        )

    def email_trash(self, *, message_ids: list[str]) -> Any:
        return self._request(
            'POST',
            '/api/email-messages/trash',
            json={'message_ids': message_ids},
        )

    def email_move(self, *, message_ids: list[str], folder: str) -> Any:
        return self._request(
            'POST',
            '/api/email-messages/move',
            json={'message_ids': message_ids, 'folder': folder},
        )

    def email_folders(self) -> Any:
        return self._request(
            'GET',
            '/api/email-messages/folders',
            params={'organisation_id': self.credentials.organisation_id},
        )

    def email_create_folder(self, *, name: str) -> Any:
        return self._request(
            'POST',
            '/api/email-messages/folders',
            json={'name': name, 'organisation_id': self.credentials.organisation_id},
        )

    def email_rename_folder(self, *, folder_id: str, name: str) -> Any:
        return self._request(
            'POST',
            '/api/email-messages/folders/rename',
            json={'folder_id': folder_id, 'name': name},
        )

    def email_delete_folder(self, *, folder_id: str) -> Any:
        return self._request(
            'POST',
            '/api/email-messages/folders/delete',
            json={'folder_id': folder_id},
        )

    def email_search(self, *, query: str) -> Any:
        return self._request(
            'GET',
            '/api/email-messages/search',
            params={
                'organisation_id': self.credentials.organisation_id,
                'query': query,
            },
        )

    def email_by_contact(self, *, contact_id: str) -> Any:
        return self._request('GET', f'/api/email-messages/contact/{contact_id}')

    def email_sync(self) -> Any:
        return self._request(
            'POST',
            '/api/email-messages/sync',
            json={'organisation_id': self.credentials.organisation_id},
        )

    # ------------------------------------------------------------------
    # Valuation
    # ------------------------------------------------------------------

    def valuation_request(self, *, immobilie_id: str, providers: list[str] | None = None) -> Any:
        payload: dict[str, Any] = {
            'immobilie_id': immobilie_id,
            'organisation_id': self.credentials.organisation_id,
        }
        if providers:
            payload['providers'] = providers
        return self._request('POST', '/api/valuation/request', json=payload)

    def valuation_history(self, *, immobilie_id: str) -> Any:
        return self._request('GET', f'/api/valuation/history/{immobilie_id}')

    def valuation_providers(self) -> Any:
        return self._request('GET', '/api/valuation/providers')

    # ------------------------------------------------------------------
    # User
    # ------------------------------------------------------------------

    def user_me(self) -> Any:
        return self._request('GET', '/api/user/me')

    def user_update_profile(self, *, data: dict[str, Any]) -> Any:
        return self._request('PUT', '/api/user/profile', json=data)

    # ------------------------------------------------------------------
    # Investor Portal
    # ------------------------------------------------------------------

    def investor_search_profile_get(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/search-profile')

    def investor_search_profile_save(self, *, org_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/organisations/{org_id}/search-profile', json=data)

    def investor_search_profiles(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/search-profiles')

    def investor_search_profile_delete(self, *, org_id: str, submission_id: str) -> Any:
        return self._request('DELETE', f'/api/organisations/{org_id}/search-profiles/{submission_id}')

    def investor_search_profile_submissions(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/search-profile-submissions')

    def investor_search_profile_submission_update(
        self, *, org_id: str, submission_id: str, data: dict[str, Any],
    ) -> Any:
        return self._request(
            'PUT',
            f'/api/organisations/{org_id}/search-profile-submissions/{submission_id}',
            json=data,
        )

    def investor_assignments_list(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/investor-assignments')

    def investor_assignments_create(self, *, org_id: str, data: dict[str, Any]) -> Any:
        return self._request('POST', f'/api/organisations/{org_id}/investor-assignments', json=data)

    def investor_assignments_bulk(self, *, org_id: str, data: dict[str, Any]) -> Any:
        return self._request('POST', f'/api/organisations/{org_id}/investor-assignments/bulk', json=data)

    def investor_assignment_update(self, *, org_id: str, assignment_id: str, data: dict[str, Any]) -> Any:
        return self._request(
            'PATCH',
            f'/api/organisations/{org_id}/investor-assignments/{assignment_id}',
            json=data,
        )

    def investor_assignment_delete(self, *, org_id: str, assignment_id: str) -> Any:
        return self._request('DELETE', f'/api/organisations/{org_id}/investor-assignments/{assignment_id}')

    def investor_my_assignments(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/my-assignments')

    def investor_my_assignment_get(self, *, org_id: str, assignment_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/my-assignments/{assignment_id}')

    def investor_matching_config(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/matching-config')

    def investor_matching_config_update(self, *, org_id: str, data: dict[str, Any]) -> Any:
        return self._request('PUT', f'/api/organisations/{org_id}/matching-config', json=data)

    def investor_reporting(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/investor-reporting')

    def investor_search_profile_masks(self, *, org_id: str) -> Any:
        return self._request('GET', f'/api/organisations/{org_id}/search-profile-masks')

    def investor_search_profile_mask_create(self, *, org_id: str, data: dict[str, Any]) -> Any:
        return self._request('POST', f'/api/organisations/{org_id}/search-profile-masks', json=data)

    def investor_search_profile_mask_update(
        self, *, org_id: str, mask_id: str, data: dict[str, Any],
    ) -> Any:
        return self._request(
            'PUT',
            f'/api/organisations/{org_id}/search-profile-masks/{mask_id}',
            json=data,
        )

    def investor_search_profile_mask_delete(self, *, org_id: str, mask_id: str) -> Any:
        return self._request('DELETE', f'/api/organisations/{org_id}/search-profile-masks/{mask_id}')

    # ------------------------------------------------------------------
    # Activity template update helpers (existing, private)
    # ------------------------------------------------------------------

    def _assert_if_updated_at_matches(self, *, current_template: dict[str, Any], if_updated_at: Any) -> None:
        if if_updated_at is None:
            return
        expected = _canonical_timestamp(if_updated_at)
        actual = _canonical_timestamp(current_template.get('updated_at'))
        if expected != actual:
            raise ImmojumpAPIError(
                409,
                'Template wurde zwischenzeitlich geändert. '
                'Bitte neu laden und Update erneut ausführen.',
            )

    @staticmethod
    def _merge_outcomes_by_id(
        *,
        existing_outcomes: list[dict[str, Any]],
        incoming_outcomes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = [copy.deepcopy(outcome) for outcome in existing_outcomes]
        existing_by_id: dict[str, dict[str, Any]] = {}

        for outcome in merged:
            outcome_id = _normalize_id(outcome.get('id'))
            if outcome_id:
                existing_by_id[outcome_id] = outcome

        for incoming in incoming_outcomes:
            if not isinstance(incoming, dict):
                raise ImmojumpAPIError(400, 'Each outcome must be an object')
            incoming_copy = copy.deepcopy(incoming)
            incoming_id = _normalize_id(incoming_copy.get('id'))
            target = existing_by_id.get(incoming_id) if incoming_id else None
            if target is None:
                merged.append(incoming_copy)
                continue
            for key, value in incoming_copy.items():
                target[key] = value

        return merged

    def _status_index(self) -> dict[str, dict[str, Any]]:
        statuses = self.status_list()
        index: dict[str, dict[str, Any]] = {}
        if not isinstance(statuses, list):
            return index
        for status in statuses:
            if not isinstance(status, dict):
                continue
            key = _normalize_id(status.get('id'))
            if key:
                index[key] = status
        return index

    @staticmethod
    def _status_name(status_payload: dict[str, Any]) -> str:
        return str(status_payload.get('name') or '').strip()

    @staticmethod
    def _status_org_id(status_payload: dict[str, Any]) -> str:
        pipeline = status_payload.get('pipeline') or {}
        return _normalize_id(pipeline.get('organisation_id'))

    def _resolve_template_org_id(
        self,
        *,
        template_payload: dict[str, Any],
        status_index: dict[str, dict[str, Any]],
    ) -> str:
        direct_org = _normalize_id(template_payload.get('organisation_id'))
        if direct_org:
            return direct_org
        status_id = _normalize_id(template_payload.get('status_id'))
        if status_id and status_id in status_index:
            return self._status_org_id(status_index[status_id])
        return ''

    def _validate_outcome_actions(self, *, outcomes: list[dict[str, Any]]) -> None:
        status_index: dict[str, dict[str, Any]] | None = None
        template_cache: dict[str, dict[str, Any]] = {}

        def _load_status_index() -> dict[str, dict[str, Any]]:
            nonlocal status_index
            if status_index is None:
                status_index = self._status_index()
            return status_index

        for outcome in outcomes:
            if not isinstance(outcome, dict):
                raise ImmojumpAPIError(400, 'Each outcome must be an object')
            actions = outcome.get('actions') or []
            if not isinstance(actions, list):
                raise ImmojumpAPIError(400, 'outcome.actions must be a list')

            for action in actions:
                if not isinstance(action, dict):
                    raise ImmojumpAPIError(400, 'Each action must be an object')
                action_type = str(action.get('type') or '').upper().strip()
                if action_type == 'STATUS_CHANGE':
                    target_status_id = _normalize_id(action.get('target_status_id'))
                    if not target_status_id:
                        raise ImmojumpAPIError(400, 'STATUS_CHANGE action requires target_status_id')
                    status_payload = _load_status_index().get(target_status_id)
                    if not status_payload:
                        raise ImmojumpAPIError(400, f'STATUS_CHANGE target_status_id not found: {target_status_id}')
                    target_status_name = action.get('target_status_name')
                    if target_status_name is not None:
                        expected_name = self._status_name(status_payload)
                        incoming_name = str(target_status_name).strip()
                        if incoming_name != expected_name:
                            raise ImmojumpAPIError(
                                400,
                                f'target_status_name mismatch for status {target_status_id}: '
                                f"expected '{expected_name}', got '{incoming_name}'",
                            )

                if action_type == 'CREATE_ACTIVITY':
                    template_id = _normalize_id(action.get('template_id'))
                    if not template_id:
                        continue
                    target_template = template_cache.get(template_id)
                    if target_template is None:
                        payload = self.activity_template_get(template_id=template_id)
                        if not isinstance(payload, dict):
                            raise ImmojumpAPIError(400, 'Invalid template payload for CREATE_ACTIVITY')
                        target_template = payload
                        template_cache[template_id] = target_template
                    target_org = self._resolve_template_org_id(
                        template_payload=target_template,
                        status_index=_load_status_index(),
                    )
                    if not target_org:
                        raise ImmojumpAPIError(
                            400,
                            f'Cannot resolve organisation for CREATE_ACTIVITY template_id {template_id}',
                        )
                    if target_org != self.credentials.organisation_id:
                        raise ImmojumpAPIError(
                            400,
                            f'CREATE_ACTIVITY template_id {template_id} belongs to another organisation',
                        )

    @staticmethod
    def _outcome_identity(outcome: dict[str, Any], index: int) -> str:
        outcome_id = _normalize_id(outcome.get('id'))
        if outcome_id:
            return f'id:{outcome_id}'
        key = _normalize_id(outcome.get('key'))
        if key:
            return f'key:{key}'
        return f'index:{index}'

    @classmethod
    def _build_outcomes_diff(
        cls,
        *,
        old_outcomes: list[dict[str, Any]],
        new_outcomes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        old_map = {cls._outcome_identity(outcome, idx): outcome for idx, outcome in enumerate(old_outcomes)}
        new_map = {cls._outcome_identity(outcome, idx): outcome for idx, outcome in enumerate(new_outcomes)}
        keys = sorted(set(old_map.keys()) | set(new_map.keys()))

        changed: list[dict[str, Any]] = []
        added: list[dict[str, Any]] = []
        removed: list[dict[str, Any]] = []
        action_changes: list[dict[str, Any]] = []

        for key in keys:
            old_item = old_map.get(key)
            new_item = new_map.get(key)
            if old_item is None and new_item is not None:
                added.append({'id': new_item.get('id'), 'key': new_item.get('key'), 'new': new_item})
                if new_item.get('actions'):
                    action_changes.append(
                        {'id': new_item.get('id'), 'key': new_item.get('key'), 'old': None, 'new': new_item.get('actions')}
                    )
                continue
            if new_item is None and old_item is not None:
                removed.append({'id': old_item.get('id'), 'key': old_item.get('key'), 'old': old_item})
                if old_item.get('actions'):
                    action_changes.append(
                        {'id': old_item.get('id'), 'key': old_item.get('key'), 'old': old_item.get('actions'), 'new': None}
                    )
                continue
            if old_item == new_item:
                continue
            field_diff: dict[str, Any] = {}
            for field_name in sorted(set(old_item.keys()) | set(new_item.keys())):
                old_value = old_item.get(field_name)
                new_value = new_item.get(field_name)
                if old_value != new_value:
                    field_diff[field_name] = {'old': old_value, 'new': new_value}
            if 'actions' in field_diff:
                action_changes.append(
                    {
                        'id': new_item.get('id') or old_item.get('id'),
                        'key': new_item.get('key') or old_item.get('key'),
                        'old': field_diff['actions']['old'],
                        'new': field_diff['actions']['new'],
                    }
                )
            changed.append(
                {
                    'id': new_item.get('id') or old_item.get('id'),
                    'key': new_item.get('key') or old_item.get('key'),
                    'fields': field_diff,
                }
            )

        return {
            'changed': changed,
            'added': added,
            'removed': removed,
            'action_changes': action_changes,
        }

    @classmethod
    def _build_update_preview(
        cls,
        *,
        template_id: str,
        current_template: dict[str, Any],
        update_payload: dict[str, Any],
        replace_outcomes: bool,
    ) -> dict[str, Any]:
        predicted_template = copy.deepcopy(current_template)
        for field_name, value in update_payload.items():
            predicted_template[field_name] = copy.deepcopy(value)

        changed_fields: dict[str, Any] = {}
        for field_name in sorted(set(current_template.keys()) | set(predicted_template.keys())):
            if field_name == 'outcomes':
                continue
            old_value = current_template.get(field_name)
            new_value = predicted_template.get(field_name)
            if old_value != new_value:
                changed_fields[field_name] = {'old': old_value, 'new': new_value}

        old_outcomes = current_template.get('outcomes') if isinstance(current_template.get('outcomes'), list) else []
        new_outcomes = predicted_template.get('outcomes') if isinstance(predicted_template.get('outcomes'), list) else []
        outcomes_diff = cls._build_outcomes_diff(old_outcomes=old_outcomes, new_outcomes=new_outcomes)
        if outcomes_diff['changed'] or outcomes_diff['added'] or outcomes_diff['removed']:
            changed_fields['outcomes'] = outcomes_diff

        return {
            'dry_run': True,
            'template_id': str(template_id),
            'replace_outcomes': bool(replace_outcomes),
            'has_changes': bool(changed_fields),
            'changed_fields': changed_fields,
            'request_payload': copy.deepcopy(update_payload),
        }

    def _log_nested_update_changes(self, *, template_id: str, preview: dict[str, Any]) -> None:
        changed_fields = preview.get('changed_fields') or {}
        outcomes_diff = changed_fields.get('outcomes') or {}
        if not outcomes_diff:
            return
        changed_outcome_ids = []
        for block in ('changed', 'added', 'removed'):
            for item in outcomes_diff.get(block, []):
                outcome_ref = _normalize_id(item.get('id')) or _normalize_id(item.get('key'))
                if outcome_ref:
                    changed_outcome_ids.append(outcome_ref)
        logger.info(
            'activity_template_update_nested_changes template_id=%s outcome_refs=%s action_changes=%s',
            template_id,
            changed_outcome_ids,
            outcomes_diff.get('action_changes', []),
        )
