from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def new_id() -> str:
    return str(uuid.uuid4())


def with_public_id(document: dict[str, Any] | None) -> dict[str, Any] | None:
    if document is None:
        return None
    payload = dict(document)
    payload["id"] = str(payload.pop("_id"))
    return payload
