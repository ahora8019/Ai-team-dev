"""Provider-neutral contracts and bounded run-state persistence."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
from typing import Literal
from uuid import uuid4

RunStatus = Literal["queued", "running", "succeeded", "failed", "timed_out", "cancelled", "skipped"]
_ALLOWED_TRANSITIONS = {
    "queued": {"running", "cancelled", "skipped"},
    "running": {"succeeded", "failed", "timed_out", "cancelled"},
    "succeeded": set(), "failed": set(), "timed_out": set(), "cancelled": set(), "skipped": set(),
}
_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|password)\s*[:=]\s*[^\s,;]+"),
)

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def redact(text: str, replacement: str = "[REDACTED]") -> str:
    """Redact common credential shapes before storing an error summary."""
    safe = text
    for pattern in _SECRET_PATTERNS:
        safe = pattern.sub(replacement, safe)
    return safe[:2000]

@dataclass
class RunRecord:
    run_id: str
    task_id: str
    adapter: str
    status: RunStatus
    attempt: int
    max_attempts: int
    created_at: str
    updated_at: str
    report_path: str | None = None
    exit_code: int | None = None
    error_summary: str | None = None

    @classmethod
    def create(cls, task_id: str, adapter: str, max_attempts: int = 2) -> "RunRecord":
        if not task_id.strip():
            raise ValueError("task_id must not be empty")
        if not adapter.strip():
            raise ValueError("adapter must not be empty")
        if not 1 <= max_attempts <= 5:
            raise ValueError("max_attempts must be between 1 and 5")
        now = utc_now()
        return cls(str(uuid4()), task_id, adapter, "queued", 0, max_attempts, now, now)

    def transition(self, status: RunStatus, *, exit_code: int | None = None,
                   report_path: str | None = None, error_summary: str | None = None) -> None:
        if status not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(f"invalid run transition: {self.status} -> {status}")
        if status == "running":
            if self.attempt >= self.max_attempts:
                raise ValueError("maximum attempts reached")
            self.attempt += 1
        self.status = status
        self.updated_at = utc_now()
        if exit_code is not None:
            self.exit_code = exit_code
        if report_path is not None:
            self.report_path = report_path
        if error_summary is not None:
            self.error_summary = redact(error_summary)

    def to_dict(self) -> dict:
        return asdict(self)

class RunStore:
    """JSON-backed store for a single writer; not a concurrent database."""
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, run: RunRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(run.to_dict(), indent=2, sort_keys=True) + "\n"
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, self.path)

    def load(self) -> RunRecord:
        return RunRecord(**json.loads(self.path.read_text(encoding="utf-8")))
