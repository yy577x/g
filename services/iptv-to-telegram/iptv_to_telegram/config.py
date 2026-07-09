"""Environment-driven configuration for the IPTV -> Telegram restream service."""
import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    pass


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    session_name: str
    session_workdir: str
    session_string: str | None
    channel: str
    iptv_source: str
    reconnect_delay_seconds: float
    ffmpeg_scale: str | None
    ffmpeg_framerate: str | None

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            api_id=int(_require("TG_API_ID")),
            api_hash=_require("TG_API_HASH"),
            session_name=os.environ.get("TG_SESSION_NAME", "userbot"),
            session_workdir=os.environ.get("TG_SESSION_WORKDIR", "."),
            session_string=os.environ.get("TG_SESSION_STRING") or None,
            channel=_require("TG_CHANNEL"),
            iptv_source=_require("IPTV_SOURCE_URL"),
            reconnect_delay_seconds=float(os.environ.get("RECONNECT_DELAY_SECONDS", "5")),
            ffmpeg_scale=os.environ.get("FFMPEG_SCALE") or None,
            ffmpeg_framerate=os.environ.get("FFMPEG_FRAMERATE") or None,
        )
