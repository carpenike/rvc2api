"""
Base class for backend features (core or optional).
"""


class Feature:
    """
    Base class for backend features (core or optional).
    Subclass this and implement startup/shutdown as needed.
    """

    name: str
    enabled: bool
    core: bool
    config: dict

    def __init__(
        self, name: str, enabled: bool = False, core: bool = False, config: dict | None = None
    ):
        self.name = name
        self.enabled = enabled
        self.core = core
        self.config = config or {}

    async def startup(self):
        """Called on FastAPI startup if feature is enabled."""
        pass

    async def shutdown(self):
        """Called on FastAPI shutdown if feature is enabled."""
        pass

    @property
    def health(self) -> str:
        """
        Returns the health status of the feature.
        Override in subclasses for real checks.
        """
        if not self.enabled:
            return "disabled"
        return "unknown"  # Default; subclasses can override with real health logic
