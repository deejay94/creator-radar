"""Extract job listings from Upwork API/JSON payloads."""

from __future__ import annotations

import re
from typing import Any

from radar.upwork.parse import canonical_job_url

_JOB_ID_RE = re.compile(r"^[0-9a-zA-Z]{10,}$")


def _normalize_job_id(raw_id: Any) -> str | None:
    if raw_id is None:
        return None
    value = str(raw_id).strip().lstrip("~")
    if _JOB_ID_RE.match(value):
        return value
    return None


def extract_jobs_from_payload(data: Any) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    _walk_payload(data, found, seen)
    return found


def _walk_payload(node: Any, found: list[dict[str, str]], seen: set[str]) -> None:
    if isinstance(node, dict):
        title = node.get("title") or node.get("jobTitle") or node.get("name")
        job_id = _normalize_job_id(
            node.get("id") or node.get("ciphertext") or node.get("uid") or node.get("jobId")
        )
        if title and job_id and job_id not in seen:
            title_text = str(title).strip()
            if len(title_text) >= 3:
                seen.add(job_id)
                url = str(node.get("url") or node.get("link") or canonical_job_url(job_id))
                if url.startswith("/"):
                    url = f"https://www.upwork.com{url}"
                found.append(
                    {
                        "external_id": job_id,
                        "title": title_text,
                        "url": url,
                    }
                )
        for value in node.values():
            _walk_payload(value, found, seen)
    elif isinstance(node, list):
        for item in node:
            _walk_payload(item, found, seen)


def merge_job_items(*groups: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            job_id = item.get("external_id", "")
            if not job_id or job_id in seen:
                continue
            seen.add(job_id)
            merged.append(item)
    return merged
