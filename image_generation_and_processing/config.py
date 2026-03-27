"""Runtime configuration and lightweight `.env` loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    api_key: str | None
    image_model: str
    responses_dir: Path
    images_dir: Path
    default_image_size: str


def load_env_file(path: Path | str = ".env") -> None:
    """Load key/value pairs from a local `.env` file if it exists."""

    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Read runtime configuration once per process."""

    load_env_file()
    return AppConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
        responses_dir=Path(os.getenv("IMAGE_TOOL_RESPONSES_DIR", "responses")),
        images_dir=Path(os.getenv("IMAGE_TOOL_IMAGES_DIR", "images")),
        default_image_size=os.getenv("IMAGE_TOOL_IMAGE_SIZE", "1024x1024"),
    )
