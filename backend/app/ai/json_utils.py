"""Parse JSON objects from LLM text responses."""

from __future__ import annotations

import json
import re
from typing import Any

_OPEN_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*", re.IGNORECASE)
_CLOSE_FENCE_PATTERN = re.compile(r"\s*```$")

_STRING_FIELD_KEYS = (
    "root_cause",
    "summary",
    "suggested_fix",
    "confidence_reason",
    "prevention_recommendation",
)
_ARRAY_FIELD_KEYS = ("kubectl_commands", "validation_steps", "additional_data_needed")


def extract_json_object(raw_response: str) -> dict[str, Any]:
    text = raw_response.strip()
    if not text:
        raise ValueError("LLM response was empty")

    text = _strip_markdown_fence(text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            data = _load_balanced_object(text)
        except ValueError:
            data = recover_truncated_json_object(text)

    if not isinstance(data, dict):
        raise ValueError("LLM response JSON must be an object")
    return data


def recover_truncated_json_object(text: str) -> dict[str, Any]:
    """Best-effort recovery when model output was cut off mid-JSON."""
    result: dict[str, Any] = {}

    for key in _STRING_FIELD_KEYS:
        value = _extract_json_string_value(text, key, allow_partial=True)
        if value:
            result[key] = value

    score_match = re.search(r'"confidence_score"\s*:\s*(\d+)', text)
    if score_match:
        result["confidence_score"] = int(score_match.group(1))

    needs_match = re.search(r'"needs_more_data"\s*:\s*(true|false)', text, re.IGNORECASE)
    if needs_match:
        result["needs_more_data"] = needs_match.group(1).lower() == "true"

    evidence = _extract_evidence_items(text)
    if evidence:
        result["evidence"] = evidence

    for key in _ARRAY_FIELD_KEYS:
        values = _extract_string_array_values(text, key, allow_partial=True)
        if values:
            result[key] = values

    if not result.get("root_cause") and not result.get("summary"):
        raise ValueError("Incomplete JSON object in LLM response")

    result.setdefault("root_cause", result.get("summary", "Analysis recovered from partial LLM output."))
    result.setdefault("summary", result.get("root_cause", "Summary unavailable."))
    result.setdefault("suggested_fix", "Review the investigation findings manually; LLM output was truncated.")
    result.setdefault("evidence", [])
    result.setdefault("kubectl_commands", [])
    result.setdefault("validation_steps", [])
    result.setdefault("prevention_recommendation", "")
    result.setdefault("confidence_score", int(result.get("confidence_score", 0) or 0))
    result.setdefault("confidence_reason", "Recovered from truncated LLM output.")
    result.setdefault("needs_more_data", bool(result.get("needs_more_data", True)))
    result.setdefault("additional_data_needed", result.get("additional_data_needed") or [])
    return result


def _strip_markdown_fence(text: str) -> str:
    if not text.startswith("```"):
        return text

    closed_match = re.search(r"^```(?:json)?\s*(.*)\s*```$", text, re.DOTALL | re.IGNORECASE)
    if closed_match:
        return closed_match.group(1).strip()

    stripped = _OPEN_FENCE_PATTERN.sub("", text, count=1).strip()
    return _CLOSE_FENCE_PATTERN.sub("", stripped, count=1).strip()


def _load_balanced_object(text: str) -> Any:
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object found in LLM response")

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : index + 1])

    raise ValueError("Incomplete JSON object in LLM response")


def _extract_json_string_value(text: str, key: str, allow_partial: bool = False) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"', text)
    if not match:
        return None

    index = match.end()
    chars: list[str] = []
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            chars.append(char)
            chars.append(text[index + 1])
            index += 2
            continue
        if char == '"':
            return _decode_json_string("".join(chars))
        chars.append(char)
        index += 1

    if allow_partial and chars:
        return _decode_json_string("".join(chars)).rstrip()
    return None


def _decode_json_string(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")


def _extract_string_array_values(text: str, key: str, allow_partial: bool = False) -> list[str]:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*\[', text)
    if not match:
        return []

    index = match.end()
    values: list[str] = []
    while index < len(text):
        while index < len(text) and text[index] in " \t\r\n,":
            index += 1
        if index >= len(text) or text[index] == "]":
            break
        if text[index] != '"':
            break
        index += 1
        chars: list[str] = []
        while index < len(text):
            char = text[index]
            if char == "\\" and index + 1 < len(text):
                chars.append(char)
                chars.append(text[index + 1])
                index += 2
                continue
            if char == '"':
                values.append(_decode_json_string("".join(chars)))
                index += 1
                break
            chars.append(char)
            index += 1
        else:
            if allow_partial and chars:
                values.append(_decode_json_string("".join(chars)).rstrip())
            break
    return values


def _extract_evidence_items(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for block in re.finditer(r'\{\s*"source"\s*:\s*"([^"]+)"\s*,\s*"detail"\s*:\s*"', text):
        source = block.group(1)
        detail = _extract_json_string_value(text[block.start() :], "detail", allow_partial=True)
        if detail:
            items.append({"source": source, "detail": detail})
    return items
