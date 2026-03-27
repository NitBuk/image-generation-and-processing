"""Optional OpenAI-backed image generation helpers."""

from __future__ import annotations

import base64
import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import AppConfig, get_config


@dataclass(frozen=True)
class GeneratedImageResult:
    prompt: str
    response_path: Path
    image_paths: list[Path]


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug[:40] or "image"


def _ensure_openai_client(api_key: str):
    try:  # pragma: no cover - exercised only in environments with the SDK
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "OpenAI support is optional. Install it with `pip install -e '.[ai]'`."
        ) from exc
    return OpenAI(api_key=api_key)


def _response_items(response) -> list[object]:
    if isinstance(response, dict):
        return list(response.get("data", []))
    return list(getattr(response, "data", []))


def _extract_bytes(item: object) -> bytes:
    if isinstance(item, dict):
        b64_json = item.get("b64_json")
        if b64_json:
            return base64.b64decode(b64_json)
        url = item.get("url")
    else:
        b64_json = getattr(item, "b64_json", None)
        if b64_json:
            return base64.b64decode(b64_json)
        url = getattr(item, "url", None)

    if url:
        with urllib.request.urlopen(url) as handle:  # nosec - URL comes from the API response
            return handle.read()

    raise RuntimeError("The image response did not include bytes or a URL.")


def _write_manifest(
    config: AppConfig,
    prompt: str,
    model: str,
    timestamp: str,
    response,
    image_paths: list[Path],
) -> Path:
    slug = _slugify(prompt)
    config.responses_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = config.responses_dir / f"{slug}-{timestamp}.json"
    manifest = {
        "prompt": prompt,
        "model": model,
        "created_at": timestamp,
        "image_paths": [str(path) for path in image_paths],
        "image_count": len(image_paths),
        "response_type": type(response).__name__,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def generate_image(prompt: str, *, config: AppConfig | None = None) -> GeneratedImageResult:
    """Generate an image through the OpenAI API and persist local artifacts."""

    runtime = config or get_config()
    if not runtime.api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Create a local `.env` file or export the variable first."
        )

    client = _ensure_openai_client(runtime.api_key)
    image_kwargs = {
        "model": runtime.image_model,
        "prompt": prompt,
        "size": runtime.default_image_size,
    }

    try:
        response = client.images.generate(**image_kwargs)
    except TypeError:
        response = client.images.generate(prompt=prompt, size=runtime.default_image_size)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _slugify(prompt)
    output_dir = runtime.images_dir / f"{slug}-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths: list[Path] = []
    for index, item in enumerate(_response_items(response)):
        image_bytes = _extract_bytes(item)
        image_path = output_dir / f"{slug}-{index}.png"
        image_path.write_bytes(image_bytes)
        image_paths.append(image_path)

    manifest_path = _write_manifest(
        runtime,
        prompt,
        runtime.image_model,
        timestamp,
        response,
        image_paths,
    )
    return GeneratedImageResult(prompt=prompt, response_path=manifest_path, image_paths=image_paths)
