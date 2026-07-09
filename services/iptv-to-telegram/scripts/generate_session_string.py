"""Run this once, locally and interactively, to log the userbot account in
and print a Pyrogram session string. Paste the result into TG_SESSION_STRING
so the service can run unattended in a container without a session file.

Usage:
    TG_API_ID=... TG_API_HASH=... python scripts/generate_session_string.py

You'll be prompted for the userbot's phone number, login code, and 2FA
password (if enabled).
"""
import os

from pyrogram import Client

api_id = int(os.environ["TG_API_ID"])
api_hash = os.environ["TG_API_HASH"]

with Client("session_gen", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
    print(app.export_session_string())
