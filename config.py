"""Runtime configuration loaded from environment variables."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
GUILD_ID = int(os.getenv("GUILD_ID", "0") or 0)
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "database" / "bot.db")))

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Copy .env.example to .env and set it.")
if not GUILD_ID:
    raise RuntimeError("GUILD_ID is missing. Set the single server ID in .env.")
