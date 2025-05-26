"""
GitHub Update Models

Pydantic models for GitHub release information and update status.
These models represent data structures for update checking functionality.
"""

from typing import Any

from pydantic import BaseModel


class GitHubReleaseAsset(BaseModel):
    """Represents a downloadable asset attached to a GitHub release."""

    name: str
    browser_download_url: str
    size: int | None = None
    download_count: int | None = None


class GitHubReleaseInfo(BaseModel):
    """Represents metadata about a GitHub release for update checking."""

    tag_name: str | None = None
    name: str | None = None
    body: str | None = None
    html_url: str | None = None
    published_at: str | None = None
    created_at: str | None = None
    assets: list[GitHubReleaseAsset] | None = None
    tarball_url: str | None = None
    zipball_url: str | None = None
    prerelease: bool | None = None
    draft: bool | None = None
    author: dict[str, Any] | None = None  # login, html_url
    discussion_url: str | None = None


class GitHubUpdateStatus(BaseModel):
    """Represents the status and metadata of the latest GitHub release as cached by the server."""

    latest_version: str | None = None
    last_checked: float | None = None
    last_success: float | None = None
    error: str | None = None
    latest_release_info: GitHubReleaseInfo | None = None
    repo: str | None = None
    api_url: str | None = None
