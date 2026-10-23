from dataclasses import dataclass

from .errors import MarkliteError

MAX_HEADING_LEVEL = 6


@dataclass(frozen=True)
class Options:
    heading_ids: bool = True
    toc_max_level: int = 3
    code_class_prefix: str = "language-"
    safe_links: bool = True
    hard_breaks: bool = False

    def __post_init__(self):
        if not 1 <= self.toc_max_level <= MAX_HEADING_LEVEL:
            raise MarkliteError(f"toc_max_level must be between 1 and {MAX_HEADING_LEVEL}")
