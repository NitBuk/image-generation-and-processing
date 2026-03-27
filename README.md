# Image Generation and Processing

A small Python image toolkit that combines deterministic image transforms with an optional OpenAI-backed generation path. The local editor handles grayscale conversion, blur, resize, rotation, edge detection, and quantization. The AI path is separate, optional, and only runs when `OPENAI_API_KEY` is configured.

## At A Glance

- Local-only: image loading, editing, previewing, and saving.
- API-backed: prompt-based image generation, saved locally as PNGs plus a JSON manifest.
- Entry points: interactive CLI and a Tkinter GUI.
- Packaging: `pyproject.toml`, editable install, and a small unittest suite.

## What Runs Where

- There is no hosted deployment in this repository.
- Everything in the editor runs locally.
- AI image generation is the only network-backed feature, and it is disabled unless you set an API key.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install -e ".[dev]"
python main.py
```

For AI generation, install the optional dependency and set your key in `.env`:

```bash
pip install -e ".[ai,dev]"
```

Then choose the generation path in the CLI or GUI. Do not commit secrets. Keep the key in `.env` or your shell environment only.

## Project Structure

```text
image_generation_and_processing/
  ai.py        # Optional OpenAI integration and artifact writing
  cli.py       # Interactive command-line flow
  config.py    # Environment loading and runtime config
  core.py      # Pure image transforms
  gui.py       # Tkinter interface
  io.py        # Pillow-based image I/O
tests/test_core.py
main.py        # CLI wrapper
gui.py         # GUI wrapper
```

## Developer Workflow

- Run the local editor: `python main.py`
- Run the GUI: `python gui.py`
- Run tests: `python -m unittest discover -s tests -v`
- Lint: `ruff check .`
- Format: `ruff format .`
- Core image logic lives in `image_generation_and_processing/core.py`.
- API-backed generation lives in `image_generation_and_processing/ai.py`.
- CLI and GUI entry points live in `image_generation_and_processing/cli.py` and `image_generation_and_processing/gui.py`.

## Architecture

The repo is intentionally split into three layers:

- Pure transforms in `core.py` operate on nested Python lists and are easy to test.
- File I/O in `io.py` is isolated behind Pillow so the rest of the code stays deterministic.
- Optional generation in `ai.py` reads configuration from `.env` and persists output artifacts locally.

That separation keeps the local editor honest: you can understand, test, and review the core behavior without needing an API key.

## Limitations

- AI generation depends on a valid OpenAI key and a compatible installed SDK.
- The repo does not include model training or image dataset management.
- The GUI is intentionally lightweight and focused on basic editing workflows.

## What This Demonstrates

- Clean separation between pure logic and side effects.
- Basic Python packaging and editable installs.
- Safer API-key handling with environment variables instead of checked-in secrets.
- Test coverage for deterministic transforms.
- A readable, recruiter-friendly README and repo layout.

## Recent Improvements

- Replaced the old flat script layout with a package-based structure.
- Removed `keys.py`-style setup in favor of `.env.example` and runtime env loading.
- Added tests for the core transforms.
- Added CI, a PR template, and ignored runtime artifacts like `images/` and `responses/`.

## Roadmap

- Expand the CLI with non-interactive flags if the repo needs scripted batch processing.
- Add more image fixtures for richer visual regression tests.
- Add a small sample gallery only if generated outputs can be verified and committed honestly.
