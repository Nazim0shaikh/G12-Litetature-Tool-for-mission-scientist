"""Safe application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    max_question_length: int = 2000

    @classmethod
    def from_env(cls) -> "AppConfig":
        origins = tuple(
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if origin.strip()
        )
        return cls(
            cors_origins=origins,
            max_question_length=int(os.getenv("MAX_QUESTION_LENGTH", "2000")),
        )
