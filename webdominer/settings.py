from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class Settings:
    """
    Central configuration for the WebDoMiner pipeline.

    Keep all tunable values here so the rest of the codebase remains clean
    and easy to reason about.
    """

    # Project paths
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[1]
    )
    data_input_dir: Path = field(init=False)
    data_output_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)

    # Input / output files
    default_input_file: Path = field(init=False)
    accepted_output_file: Path = field(init=False)
    rejected_output_file: Path = field(init=False)
    failed_output_file: Path = field(init=False)

    # Keyword extraction / discovery
    top_keywords: int = 20
    top_urls_per_keyword: int = 10
    search_backend: str = "ddg"  # supported later: "ddg", "searxng"
    searxng_base_url: Optional[str] = None

    # URL filtering
    allowed_schemes: tuple[str, ...] = ("http", "https")
    bad_extensions: tuple[str, ...] = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".bmp",
        ".tiff",
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
        ".mkv",
        ".mp3",
        ".wav",
        ".flac",
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".exe",
        ".dmg",
        ".iso",
        ".apk",
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
    )
    bad_url_patterns: tuple[str, ...] = (
        "/search",
        "/login",
        "/signin",
        "/signup",
        "/register",
        "/privacy",
        "/terms",
        "/policy",
        "/cookies",
        "/account",
        "/cart",
        "/checkout",
        "/wp-content/",
        "/tag/",
        "/author/",
        "/category/",
    )

    # Scraping / extraction
    min_word_count: int = 150
    request_timeout_seconds: int = 20
    request_delay_seconds: float = 1.0
    max_retries: int = 2
    user_agent: str = (
        "Mozilla/5.0 (compatible; WebDoMiner/1.0; +https://github.com/your-repo)"
    )

    # Playwright fallback
    enable_playwright_fallback: bool = True
    playwright_timeout_ms: int = 15000

    # Semantic filtering
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.45

    # Logging
    log_level: str = "INFO"
    log_filename: str = "webdominer.log"

    def __post_init__(self) -> None:
        self.data_input_dir = self.project_root / "data" / "input"
        self.data_output_dir = self.project_root / "data" / "output"
        self.logs_dir = self.project_root / "logs"

        self.default_input_file = self.data_input_dir / "requirements.txt"
        self.accepted_output_file = self.data_output_dir / "corpus.jsonl"
        self.rejected_output_file = self.data_output_dir / "rejected.jsonl"
        self.failed_output_file = self.data_output_dir / "failed.jsonl"

    @property
    def log_file_path(self) -> Path:
        return self.logs_dir / self.log_filename

    def ensure_directories(self) -> None:
        """Create runtime directories if they do not already exist."""
        self.data_input_dir.mkdir(parents=True, exist_ok=True)
        self.data_output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)