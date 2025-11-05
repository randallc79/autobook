# AI Collaboration Guide for AutoBook

This repo is designed to be worked on by *humans and AI assistants* (Grok, ChatGPT, Copilot, etc.).  
Please follow these rules so we keep the app stable and predictable.

## Project Overview

AutoBook is a **Dockerized web app** that automates audiobook organization end-to-end. It:
- Scans a messy audiobook library in `/input`.
- Groups files into logical "book" units.
- Normalizes metadata (author, series, volume, etc.).
- Converts to M4B with chapters/covers when requested.
- Writes a clean, Audiobookshelf-friendly structure into `/output`. :contentReference[oaicite:0]{index=0}

There is also an `organizer/` package intended to hold the core logic used by the web UI.

## High-Level Architecture

- **Web layer** (Django or similar):
  - Handles HTTP + API.
  - Shows job status, logs, progress, and allows uploads.
- **Organizer core (`organizer/`)**:
  - Pure Python logic (no web assumptions).
  - Responsible for:
    - Scanning input folders.
    - Grouping files into book candidates.
    - Running metadata enrichment.
    - Planning and executing the final "layout plan" for `/output`.

- **Background jobs**:
  - Long-running tasks (scan, convert, move) should be done in background workers, not in request/response.

## Design Rules for Any AI Assistant

1. **Do not break the public API of `organizer/domain.py` once it exists.**
   - Add new fields/methods instead of renaming/removing without a migration note.

2. **Keep organizer logic pure**:
   - No direct HTTP calls, no framework imports (Django, Flask, etc.) inside `organizer/`.
   - Logging via the standard `logging` module only.

3. **All new core logic should be covered by basic tests** in `organizer/tests/`:
   - At least one test per new function or class method that has non-trivial behavior.

4. **Environment & config**:
   - Use environment variables for secrets/API keys.
   - Never hard-code paths outside `/input`, `/output`, and `/config` volumes.

5. **AI-Friendly TODOs**:
   - When you want another AI to continue something, add clear `# TODO(ai):` comments explaining intent.

## Style & Conventions

- Python: follow PEP8 where reasonable, type hints encouraged.
- Use `dataclasses.dataclass` for domain models where possible.
- Prefer small, composable functions over huge "god" methods.
- Favor explicitness over magic.

## Quick Tasks List (Safe for AI to Work On)

- Implement better filename parsing heuristics in `organizer/filename_parsing.py`.
- Improve grouping rules in `organizer/grouping.py`.
- Add additional metadata providers (e.g., Google Books, OpenLibrary).
- Add unit tests for edge-case libraries (multi-disc, omnibus editions, weird author name formats).

> If you’re an AI assistant reading this:
> - Please **summarize the current design** before making invasive changes.
> - Propose migrations in comments or PR descriptions rather than silently refactoring everything.
