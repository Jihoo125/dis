"""Small, thread-safe SQLite persistence layer for the single-server bot."""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.initialize()

    def initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS config (guild_id INTEGER PRIMARY KEY, verified_role_id INTEGER, unverified_role_id INTEGER, verification_channel_id INTEGER, mod_log_channel_id INTEGER, ticket_category_id INTEGER, ticket_log_channel_id INTEGER, support_role_id INTEGER, staff_role_id INTEGER, raid_threshold INTEGER NOT NULL DEFAULT 10, raid_window INTEGER NOT NULL DEFAULT 20, lockdown_enabled INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS warnings (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, moderator_id INTEGER NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL UNIQUE, user_id INTEGER NOT NULL, claimed_by INTEGER, created_at TEXT NOT NULL, closed_at TEXT);
        CREATE TABLE IF NOT EXISTS reaction_roles (guild_id INTEGER NOT NULL, message_id INTEGER NOT NULL, emoji TEXT NOT NULL, role_id INTEGER NOT NULL, PRIMARY KEY(guild_id,message_id,emoji));
        CREATE TABLE IF NOT EXISTS whitelist (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, reason TEXT, PRIMARY KEY(guild_id,user_id));
        CREATE TABLE IF NOT EXISTS verification_attempts (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, last_attempt TEXT, verified INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(guild_id,user_id));
        CREATE TABLE IF NOT EXISTS moderation_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, action TEXT NOT NULL, target_id INTEGER, moderator_id INTEGER, reason TEXT, created_at TEXT NOT NULL);
        """
        with self.lock:
            self.conn.executescript(schema)
            self.conn.commit()

    def _execute(self, sql: str, args: tuple[Any, ...] = (), *, one=False, many=False):
        with self.lock:
            cur = self.conn.execute(sql, args)
            result = cur.fetchall() if many else (cur.fetchone() if one else cur.lastrowid)
            self.conn.commit()
            return result

    def get_config(self, guild_id: int) -> dict[str, Any]:
        row = self._execute("SELECT * FROM config WHERE guild_id=?", (guild_id,), one=True)
        if row:
            return dict(row)
        self._execute("INSERT INTO config(guild_id) VALUES(?)", (guild_id,))
        return dict(self._execute("SELECT * FROM config WHERE guild_id=?", (guild_id,), one=True))

    def set_config(self, guild_id: int, key: str, value: Any) -> None:
        allowed = {"verified_role_id","unverified_role_id","verification_channel_id","mod_log_channel_id","ticket_category_id","ticket_log_channel_id","support_role_id","staff_role_id","raid_threshold","raid_window","lockdown_enabled"}
        if key not in allowed:
            raise ValueError("Unsupported configuration key")
        self.get_config(guild_id)
        self._execute(f"UPDATE config SET {key}=? WHERE guild_id=?", (value, guild_id))

    def add_warning(self, guild: int, user: int, moderator: int, reason: str) -> None:
        self._execute("INSERT INTO warnings(guild_id,user_id,moderator_id,reason,created_at) VALUES(?,?,?,?,?)", (guild,user,moderator,reason,now()))
        self.log_moderation(guild, "warn", user, moderator, reason)

    def warnings(self, guild: int, user: int):
        return self._execute("SELECT * FROM warnings WHERE guild_id=? AND user_id=? ORDER BY id DESC", (guild,user), many=True)

    def log_moderation(self, guild: int, action: str, target: int|None, moderator: int|None, reason: str|None) -> None:
        self._execute("INSERT INTO moderation_logs(guild_id,action,target_id,moderator_id,reason,created_at) VALUES(?,?,?,?,?,?)", (guild,action,target,moderator,reason,now()))

    def ticket_for_user(self, guild: int, user: int):
        return self._execute("SELECT * FROM tickets WHERE guild_id=? AND user_id=? AND closed_at IS NULL", (guild,user), one=True)

    def ticket_for_channel(self, guild: int, channel: int):
        return self._execute("SELECT * FROM tickets WHERE guild_id=? AND channel_id=? AND closed_at IS NULL", (guild,channel), one=True)

    def create_ticket(self, guild: int, channel: int, user: int) -> None:
        self._execute("INSERT INTO tickets(guild_id,channel_id,user_id,created_at) VALUES(?,?,?,?)", (guild,channel,user,now()))

    def close_ticket(self, guild: int, channel: int) -> None:
        self._execute("UPDATE tickets SET closed_at=? WHERE guild_id=? AND channel_id=? AND closed_at IS NULL", (now(),guild,channel))

    def claim_ticket(self, guild: int, channel: int, user: int) -> None:
        self._execute("UPDATE tickets SET claimed_by=? WHERE guild_id=? AND channel_id=? AND closed_at IS NULL", (user,guild,channel))

    def add_whitelist(self, guild: int, user: int, reason: str = "") -> None:
        self._execute("INSERT OR REPLACE INTO whitelist(guild_id,user_id,reason) VALUES(?,?,?)", (guild,user,reason))

    def remove_whitelist(self, guild: int, user: int) -> None:
        self._execute("DELETE FROM whitelist WHERE guild_id=? AND user_id=?", (guild,user))

    def is_whitelisted(self, guild: int, user: int) -> bool:
        return bool(self._execute("SELECT 1 FROM whitelist WHERE guild_id=? AND user_id=?", (guild,user), one=True))

    def whitelist(self, guild: int):
        return self._execute("SELECT * FROM whitelist WHERE guild_id=?", (guild,), many=True)
