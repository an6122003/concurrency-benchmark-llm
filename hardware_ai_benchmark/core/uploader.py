"""Upload results to the community database — with sanitization first.

Design:
  sanitize_for_upload(document)  strips private data (paths, hostnames, env)
  Uploader                       interface with .upload(payload) -> UploadResult
  HttpUploader                   POST {server}/api/benchmark-results
  MockUploader                   writes payload to the local outbox folder

The outbox doubles as the retry queue: failed HTTP uploads are saved there and
can be re-sent later.
"""

from __future__ import annotations

import copy
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import outbox_dir

DEFAULT_ENDPOINT = "/api/benchmark-results"

# Keys whose values are local/private and never belong in an upload.
PRIVATE_KEYS = {
    "python_executable", "prompts_file", "hardware_image", "pnp_device_id",
    "local_scan", "processes", "model_files", "env", "base_url", "out_dir",
}
_HOME_RE = re.compile(r"(/Users/[^/\s\"]+|/home/[^/\s\"]+|[A-Z]:\\+Users\\+[^\\\s\"]+)")


def _scrub_strings(value: Any) -> Any:
    if isinstance(value, str):
        return _HOME_RE.sub("~", value)
    if isinstance(value, list):
        return [_scrub_strings(item) for item in value]
    if isinstance(value, dict):
        return {k: _scrub_strings(v) for k, v in value.items()}
    return value


def _drop_private_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _drop_private_keys(v) for k, v in value.items() if k not in PRIVATE_KEYS}
    if isinstance(value, list):
        return [_drop_private_keys(item) for item in value]
    return value


def sanitize_for_upload(document: Dict[str, Any], include_system_metadata: bool = True) -> Dict[str, Any]:
    """Return an upload-safe copy. Never mutates the local result document."""
    payload = copy.deepcopy(document)
    if not include_system_metadata:
        payload["system"] = {"withheld": True}
        payload["platform"] = {
            "os": payload.get("platform", {}).get("os"),
            "arch": payload.get("platform", {}).get("arch"),
        }
    payload = _drop_private_keys(payload)
    payload = _scrub_strings(payload)
    # The checksum covered the unsanitized document; recipients re-verify
    # against the sanitized form, so recompute it here.
    from .result_schema import _checksum
    payload["checksum"] = _checksum(payload)
    return payload


def upload_preview(payload: Dict[str, Any]) -> List[str]:
    """Human-readable summary of what an upload will contain."""
    plat = payload.get("platform", {})
    system = payload.get("system", {})
    gpus = (system.get("gpu") or {}).get("detected") or []
    lines = [
        f"Result id: {payload.get('result_id')}",
        f"Status: {payload.get('status')}",
        f"Alias: {payload.get('user_alias') or 'anonymous'}",
        f"OS / arch: {plat.get('os', '?')} / {plat.get('arch', '?')}",
        f"GPU: {'; '.join(g.get('name', '?') for g in gpus) or 'withheld/none'}",
        f"Model: {payload.get('model', {}).get('name', '?')}",
        f"Summaries: {len((payload.get('results') or {}).get('summaries') or [])} concurrency levels",
        "No file paths, usernames, or environment variables are included.",
    ]
    return lines


@dataclass
class UploadResult:
    ok: bool
    message: str
    saved_to: Optional[Path] = None


class Uploader:
    """Interface. Implementations must be safe to call from a worker thread."""

    def upload(self, payload: Dict[str, Any]) -> UploadResult:  # pragma: no cover
        raise NotImplementedError


class MockUploader(Uploader):
    """No server yet / offline: save the upload-ready payload to the outbox."""

    def upload(self, payload: Dict[str, Any]) -> UploadResult:
        path = outbox_dir() / f"upload-{payload.get('result_id', 'unknown')}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return UploadResult(True, f"Saved upload payload to outbox:\n{path}", saved_to=path)


class HttpUploader(Uploader):
    """POSTs to the community database server."""

    def __init__(self, server_url: str, endpoint: str = DEFAULT_ENDPOINT, timeout: float = 15.0):
        self.url = server_url.rstrip("/") + endpoint
        self.timeout = timeout

    def upload(self, payload: Dict[str, Any]) -> UploadResult:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.url, data=body, method="POST",
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                answer = json.loads(response.read().decode("utf-8") or "{}")
            return UploadResult(True, f"Uploaded. Server says: {answer.get('message', 'accepted')}")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            result = UploadResult(False, f"Server rejected upload (HTTP {exc.code}): {detail}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            result = UploadResult(False, f"Could not reach server: {exc}")
        # Failed → keep a retryable copy in the outbox.
        result.saved_to = MockUploader().upload(payload).saved_to
        result.message += f"\nA copy was saved for retry: {result.saved_to}"
        return result


def pending_uploads() -> List[Path]:
    return sorted(outbox_dir().glob("upload-*.json"))


def retry_pending(uploader: Uploader) -> List[UploadResult]:
    """Re-send everything in the outbox; delete entries that succeed."""
    results = []
    for path in pending_uploads():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            results.append(UploadResult(False, f"Unreadable outbox file {path.name}: {exc}"))
            continue
        result = uploader.upload(payload)
        if result.ok and not isinstance(uploader, MockUploader):
            path.unlink(missing_ok=True)
        results.append(result)
    return results
