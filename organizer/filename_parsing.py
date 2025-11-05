from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import uuid

from .domain import AudioFile, BookCandidate, SourceFormat


def detect_source_format(path: Path) -> SourceFormat:
    ext = path.suffix.lower().lstrip(".")
    return {
        "mp3": SourceFormat.MP3,
        "m4b": SourceFormat.M4B,
        "flac": SourceFormat.FLAC,
        "aac": SourceFormat.AAC,
        "m4a": SourceFormat.AAC,
        "ogg": SourceFormat.OGG,
    }.get(ext, SourceFormat.OTHER)


def build_candidates_from_files(files: Iterable[Path]) -> List[BookCandidate]:
    """
    Very first-pass heuristic: group by parent directory name.
    Grok or another AI can later improve this to handle:
      - multiple books in one folder
      - disc subfolders
      - weird naming schemes
    """
    by_parent: dict[Path, BookCandidate] = {}

    for path in files:
        parent = path.parent
        if parent not in by_parent:
            cid = str(uuid.uuid4())
            by_parent[parent] = BookCandidate(
                id=cid,
                raw_title_hint=parent.name,
            )

        audio_file = AudioFile(
            path=path,
            size_bytes=path.stat().st_size,
            format=detect_source_format(path),
        )
        by_parent[parent].add_file(audio_file)

    return list(by_parent.values())
