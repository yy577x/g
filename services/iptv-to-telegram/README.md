# iptv-to-telegram

Restreams an IPTV source (RTMP/HLS/any FFmpeg-readable URL) into a Telegram
channel's live video chat, using a userbot (real MTProto account) as the
broadcaster. See `../../TELEGRAM_RESTREAM.md`-style design notes in the
originating conversation for the full rationale — this directory is the
implementation.

Standalone microservice: its own dependencies, its own Dockerfile. It does
not touch the rest of this repo.

## Requirements

- A Telegram **API ID / API hash** from https://my.telegram.org.
- A real Telegram account (the "userbot") that is an **admin of the target
  channel** with "manage video chats" rights. This cannot be a bot account —
  the Bot API has no video-chat support.
- FFmpeg installed on the host (or use the provided Dockerfile, which
  installs it).
- Rights to redistribute the IPTV content, and compliance with Telegram's
  ToS on automated/userbot activity. See the legal note in the design doc.

## Setup

```bash
cp .env.example .env
# edit .env: TG_API_ID, TG_API_HASH, TG_CHANNEL, IPTV_SOURCE_URL
pip install -r requirements.txt
```

### First login (creates the userbot session)

The first run needs an interactive login (phone number + code, and 2FA
password if enabled).

- **File-based session** (simplest for local/manual use): just run the
  service once outside Docker — Pyrogram will prompt interactively and save
  the session under `TG_SESSION_WORKDIR`.
- **Session string** (recommended for containers, since there's no TTY to
  prompt in): run this locally once, then set `TG_SESSION_STRING` in `.env`
  instead of using the file-based session:

  ```bash
  TG_API_ID=... TG_API_HASH=... python scripts/generate_session_string.py
  ```

## Run locally

```bash
set -a; source .env; set +a
python -m iptv_to_telegram
```

## Run with Docker

```bash
docker build -t iptv-to-telegram .
docker run --rm --env-file .env -v "$(pwd)/sessions:/app/sessions" iptv-to-telegram
```

(Omit the volume mount if you're using `TG_SESSION_STRING` instead of a
file-based session.)

## Config reference (env vars)

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `TG_API_ID` | yes | - | Telegram API ID |
| `TG_API_HASH` | yes | - | Telegram API hash |
| `TG_CHANNEL` | yes | - | Target channel username or ID; userbot must be admin there |
| `IPTV_SOURCE_URL` | yes | - | Any FFmpeg-readable input (RTMP, HLS `.m3u8`, etc.) |
| `TG_SESSION_STRING` | no | - | Pre-generated session string; if set, takes priority over the file session |
| `TG_SESSION_NAME` | no | `userbot` | Session file name (used when no session string) |
| `TG_SESSION_WORKDIR` | no | `.` | Directory for the session file |
| `RECONNECT_DELAY_SECONDS` | no | `5` | Delay before retrying after either leg (IPTV source or Telegram call) drops |
| `FFMPEG_SCALE` | no | - | e.g. `1280:720`; forces a scale if Telegram rejects the raw source |
| `FFMPEG_FRAMERATE` | no | - | e.g. `30`; forces a framerate |

## How it works

1. Logs in as the userbot (Pyrogram/MTProto).
2. Starts or joins `TG_CHANNEL`'s video chat as the broadcaster (`pytgcalls`,
   which shells out to FFmpeg internally to decode/normalize
   `IPTV_SOURCE_URL`).
3. Waits for a stream-end event (source dropped, or call closed).
4. On any failure or stream end, waits `RECONNECT_DELAY_SECONDS` and retries
   — runs unattended until stopped (`SIGINT`/`SIGTERM` leaves the call
   cleanly and exits).

## Notes

- If the raw IPTV source isn't accepted as-is, set `FFMPEG_SCALE` /
  `FFMPEG_FRAMERATE` rather than debugging blind — this isolates "FFmpeg can
  read this source" from "pytgcalls accepts this exact format."
- `pytgcalls`/`pyrogram` APIs shift between major versions; versions are
  pinned in `requirements.txt`. If `pyrogram` is unmaintained for your
  `pytgcalls` version, the drop-in fork `pyrofork` is a common substitute.
