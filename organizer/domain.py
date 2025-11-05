from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict
import enum


class SourceFormat(enum.Enum):
    MP3 = "mp3"
    M4B = "m4b"
    FLAC = "flac"
    AAC = "aac"
    OGG = "ogg"
    OTHER = "other"


class JobStatus(enum.Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    ORGANIZING = "organizing"
    CONVERTING = "converting"
    WRITING_OUTPUT = "writing_output"
    DONE = "done"
    FAILED = "failed"


@dataclass
class AudioFile:
    """A raw audio file as found on disk under /input."""
    path: Path
    size_bytes: int
    format: SourceFormat
    track_number: Optional[int] = None
    disc_number: Optional[int] = None

    def relative_to_input(self, input_root: Path) -> Path:
        return self.path.relative_to(input_root)


@dataclass
class BookCandidate:
    """
    A group of files that likely belong to the same book.

    This is created by filename / folder heuristics BEFORE metadata enrichment.
    """
    id: str                                # stable internal ID (e.g. uuid or hash)
    raw_title_hint: str                    # guessed from folder/filenames
    raw_author_hint: Optional[str] = None
    series_hint: Optional[str] = None
    series_index_hint: Optional[str] = None  # "01", "1", "1.5", etc.

    files: List[AudioFile] = field(default_factory=list)

    def add_file(self, f: AudioFile) -> None:
        self.files.append(f)

    @property
    def total_size_bytes(self) -> int:
        return sum(f.size_bytes for f in self.files)


@dataclass
class EnrichedBook:
    """
    A book after metadata providers (Audible, Google Books, etc.) have run.
    """
    candidate: BookCandidate
    title: str
    author: str
    series: Optional[str] = None
    series_index: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    publish_year: Optional[int] = None
    cover_image_path: Optional[Path] = None
    extra_metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class LayoutPlan:
    """
    Describes how we will write an EnrichedBook into /output so that
    Audiobookshelf and similar tools see it cleanly.

    Example:
      /output/Author/Series/01 - Book Title/Book Title.m4b
    """
    enriched_book: EnrichedBook
    output_root: Path
    output_dir: Path
    output_file: Path
    will_convert_to_m4b: bool = True


@dataclass
class Job:
    """
    A full organization job: from messy input to final clean output.
    """
    id: str
    input_root: Path
    output_root: Path
    status: JobStatus = JobStatus.PENDING
    error_message: Optional[str] = None

    candidates: List[BookCandidate] = field(default_factory=list)
    enriched_books: List[EnrichedBook] = field(default_factory=list)
    layout_plans: List[LayoutPlan] = field(default_factory=list)

    def mark_failed(self, message: str) -> None:
        self.status = JobStatus.FAILED
        self.error_message = message
