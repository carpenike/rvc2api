import asyncio
import contextlib
import logging

import httpx

from core_daemon.feature_base import Feature

logger = logging.getLogger(__name__)


class UptimeRobotFeature(Feature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._task = None
        self._last_status = "unknown"
        self._last_message = None

    async def startup(self) -> None:
        if not self.enabled:
            return
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("UptimeRobotFeature started polling loop.")

    async def shutdown(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        logger.info("UptimeRobotFeature stopped polling loop.")

    @property
    def health(self) -> str:
        return self._last_status

    async def _poll_loop(self) -> None:
        api_key = self.config.get("api_key")
        if not api_key:
            self._last_status = "no_api_key"
            return
        url = "https://api.uptimerobot.com/v2/getMonitors"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"api_key": api_key, "format": "json"}
        while True:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, data=data, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        result = resp.json()
                        if result.get("stat") == "ok":
                            monitors = result.get("monitors", [])
                            if all(m.get("status") == 2 for m in monitors):
                                self._last_status = "healthy"
                            else:
                                self._last_status = "down"
                            self._last_message = monitors
                        else:
                            self._last_status = "api_error"
                            self._last_message = result
                    else:
                        self._last_status = f"http_{resp.status_code}"
                        self._last_message = resp.text
            except Exception as e:
                self._last_status = "error"
                self._last_message = str(e)
            await asyncio.sleep(60)  # Poll every 60 seconds
