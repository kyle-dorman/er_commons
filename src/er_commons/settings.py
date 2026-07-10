"""Typed project settings loaded from the required local ``.env`` file."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    """Settings shared by project commands.

    ``data_root`` intentionally has no default: every checkout must declare its
    artifact location explicitly in ``.env`` or in its environment.
    """

    data_root: Path

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ER_COMMONS_",
        extra="ignore",
    )


def load_settings() -> ProjectSettings:
    """Load and validate the current checkout's explicitly configured settings."""
    # Pydantic-settings supplies this required field from .env or the environment.
    return ProjectSettings()  # type: ignore[call-arg]
