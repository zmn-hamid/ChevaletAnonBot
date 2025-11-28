import json
import os

from config import AI_SESSION_ID, AI_URL
from modules.Global.log import logger

# Settings file path
SETTINGS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "dynamic_settings.json"
)


class DynamicSettings:
    """Manages dynamic settings that can be changed at runtime and persist across restarts."""

    def __init__(self):
        self._settings = {}
        self._load_settings()

    def _load_settings(self) -> None:
        """Load settings from file, falling back to config defaults if not found."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
                logger.info("Loaded dynamic settings from file")
            else:
                logger.info("No dynamic settings file found, using config defaults")
        except Exception as e:
            logger.warning(
                f"Failed to load dynamic settings: {e}, using config defaults"
            )
            self._settings = {}

    def _save_settings(self) -> None:
        """Save current settings to file."""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
            logger.info("Saved dynamic settings to file")
        except Exception as e:
            logger.error(f"Failed to save dynamic settings: {e}")
            raise

    def get_ai_url(self) -> str:
        """Get the AI URL, falling back to config if not set."""
        return self._settings.get("ai_url", AI_URL)

    def set_ai_url(self, url: str) -> None:
        """Set the AI URL and persist to file."""
        self._settings["ai_url"] = url
        self._save_settings()

    def get_ai_session_id(self) -> str:
        """Get the AI session ID, falling back to config if not set."""
        return self._settings.get("ai_session_id", AI_SESSION_ID)

    def set_ai_session_id(self, session_id: str) -> None:
        """Set the AI session ID and persist to file."""
        self._settings["ai_session_id"] = session_id
        self._save_settings()

    def reset_ai_url(self) -> None:
        """Reset AI URL to config default."""
        if "ai_url" in self._settings:
            del self._settings["ai_url"]
            self._save_settings()

    def reset_ai_session_id(self) -> None:
        """Reset AI session ID to config default."""
        if "ai_session_id" in self._settings:
            del self._settings["ai_session_id"]
            self._save_settings()


# Singleton instance
dynamic_settings = DynamicSettings()
