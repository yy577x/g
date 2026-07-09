"""Core restream logic: joins a Telegram channel's video chat as a userbot
and publishes an IPTV source into it, reconnecting on failure."""
import asyncio
import logging
import signal

from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

from .config import Config

logger = logging.getLogger("iptv_to_telegram")


def build_media_stream(config: Config) -> MediaStream:
    ffmpeg_params = []
    if config.ffmpeg_scale:
        ffmpeg_params.append(f"-vf scale={config.ffmpeg_scale}")
    if config.ffmpeg_framerate:
        ffmpeg_params.append(f"-r {config.ffmpeg_framerate}")
    return MediaStream(
        config.iptv_source,
        video_flags=MediaStream.Flags.AUTO_DETECT,
        additional_ffmpeg_parameters=" ".join(ffmpeg_params) if ffmpeg_params else None,
    )


class RestreamService:
    """Owns the Pyrogram/PyTgCalls sessions and the reconnect loop."""

    def __init__(self, config: Config):
        self.config = config
        if config.session_string:
            self.app = Client(
                config.session_name,
                api_id=config.api_id,
                api_hash=config.api_hash,
                session_string=config.session_string,
                in_memory=True,
            )
        else:
            self.app = Client(
                config.session_name,
                api_id=config.api_id,
                api_hash=config.api_hash,
                workdir=config.session_workdir,
            )
        self.calls = PyTgCalls(self.app)
        self._stream_ended = asyncio.Event()
        self._stopping = False

        @self.calls.on_stream_end()
        async def _on_stream_end(_client, _update):
            logger.warning("stream ended (IPTV source likely dropped or call closed)")
            self._stream_ended.set()

    async def _broadcast_once(self):
        self._stream_ended.clear()
        await self.calls.play(self.config.channel, build_media_stream(self.config))
        logger.info("broadcasting %s -> %s", self.config.iptv_source, self.config.channel)
        await self._stream_ended.wait()

    async def run_forever(self):
        await self.app.start()
        await self.calls.start()
        try:
            while not self._stopping:
                try:
                    await self._broadcast_once()
                except Exception as exc:  # noqa: BLE001 - must survive any transient failure
                    logger.exception("restream dropped: %s", exc)
                if self._stopping:
                    break
                logger.info("reconnecting in %.1fs", self.config.reconnect_delay_seconds)
                await asyncio.sleep(self.config.reconnect_delay_seconds)
        finally:
            await self._shutdown()

    async def stop(self):
        self._stopping = True
        self._stream_ended.set()

    async def _shutdown(self):
        try:
            await self.calls.leave_call(self.config.channel)
        except Exception:
            logger.debug("leave_call failed during shutdown", exc_info=True)
        await self.app.stop()


async def _amain():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = Config.from_env()
    service = RestreamService(config)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(service.stop()))

    await service.run_forever()


def main():
    asyncio.run(_amain())
