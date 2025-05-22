# github_update_checker.py
"""
GitHub Update Checker for rvc2api

Provides a background task to periodically check the latest release
version from GitHub and cache it for API use.
This avoids client-side rate limiting and centralizes update logic.
"""

import asyncio
import logging
import os
import time

import httpx

from core_daemon.feature_base import Feature

DEFAULT_GITHUB_OWNER = "carpenike"
DEFAULT_GITHUB_REPO = "rvc2api"


def get_github_repo():
    """Get the GitHub repo (owner, repo) from env or defaults."""
    repo_env = os.getenv("GITHUB_UPDATE_REPO")
    if repo_env and "/" in repo_env:
        owner, repo = repo_env.split("/", 1)
        return owner, repo
    return DEFAULT_GITHUB_OWNER, DEFAULT_GITHUB_REPO


def build_github_api_url(owner, repo):
    return f"https://api.github.com/repos/{owner}/{repo}/releases/latest"


CHECK_INTERVAL = 3600  # seconds (1 hour)


class UpdateChecker:
    """
    Periodically checks the latest GitHub release and caches the result.

    Attributes:
        latest_version (str|None): The latest version string, or None if not fetched.
        last_checked (float): Timestamp of the last check attempt.
        last_success (float): Timestamp of the last successful check.
        error (str|None): Error message from the last failed check, if any.
        latest_release_info (dict|None): Full metadata from the latest release,
        or None if not fetched.
    """

    def __init__(self):
        self.latest_version = None
        self.last_checked = 0
        self.last_success = 0
        self.error = None
        self.latest_release_info = None
        self._task = None
        self._logger = logging.getLogger("github_update_checker")
        self.owner, self.repo = get_github_repo()
        self.api_url = build_github_api_url(self.owner, self.repo)

    async def start(self):
        """
        Starts the background update checker task if not already running.
        """
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def _run(self):
        """
        Background loop: checks for updates every CHECK_INTERVAL seconds.
        """
        while True:
            await self.check_now()
            await asyncio.sleep(CHECK_INTERVAL)

    async def check_now(self):
        """
        Immediately checks GitHub for the latest release version and updates the cache.
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self.api_url)
                resp.raise_for_status()
                data = resp.json()
                tag = data.get("tag_name", "").lstrip("v")
                self.latest_version = tag
                self.last_success = time.time()
                self.error = None
                # Store useful metadata for the frontend
                self.latest_release_info = {
                    "tag_name": data.get("tag_name"),
                    "name": data.get("name"),
                    "body": data.get("body"),
                    "html_url": data.get("html_url"),
                    "published_at": data.get("published_at"),
                    "created_at": data.get("created_at"),
                    "assets": [
                        {
                            "name": a.get("name"),
                            "browser_download_url": a.get("browser_download_url"),
                            "size": a.get("size"),
                            "download_count": a.get("download_count"),
                        }
                        for a in data.get("assets", [])
                    ],
                    "tarball_url": data.get("tarball_url"),
                    "zipball_url": data.get("zipball_url"),
                    "prerelease": data.get("prerelease"),
                    "draft": data.get("draft"),
                    "author": (
                        {
                            "login": data.get("author", {}).get("login"),
                            "html_url": data.get("author", {}).get("html_url"),
                        }
                        if data.get("author")
                        else None
                    ),
                    "discussion_url": data.get("discussion_url"),
                }
                self._logger.info(f"Fetched latest GitHub version: {tag}")
        except Exception as e:
            self.error = str(e)
            self._logger.warning(f"Failed to fetch GitHub version: {e}")
        self.last_checked = time.time()

    async def force_check(self):
        """Force an immediate update check (for API use)."""
        await self.check_now()

    def get_status(self):
        """
        Returns the cached update check result and status, including release metadata.

        Returns:
            dict: Contains latest_version, last_checked, last_success, error,
            latest_release_info, repo, and api_url.
        """
        return {
            "latest_version": self.latest_version,
            "last_checked": self.last_checked,
            "last_success": self.last_success,
            "error": self.error,
            "latest_release_info": self.latest_release_info,
            "repo": f"{self.owner}/{self.repo}",
            "api_url": self.api_url,
        }


update_checker = UpdateChecker()


class UpdateCheckerFeature(Feature):
    """Feature wrapper for the GitHub update checker background service."""

    def __init__(self):
        super().__init__(name="github_update_checker", enabled=True, core=True)

    @property
    def health(self):
        # Consider healthy if last_success is recent and no error
        status = update_checker.get_status()
        if status["error"]:
            return "error"
        if status["last_success"] and (status["last_checked"] - status["last_success"] < 7200):
            return "healthy"
        return "unknown"

    @property
    def status(self):
        return update_checker.get_status()
