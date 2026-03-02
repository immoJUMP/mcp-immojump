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
        # Keep raw value if timestamp parsing fails on either side.
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
