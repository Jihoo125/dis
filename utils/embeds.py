from __future__ import annotations
import discord

COLORS = {"success": 0x2ecc71, "error": 0xe74c3c, "warning": 0xf1c40f, "info": 0x3498db, "security": 0x9b59b6, "ticket": 0x5865F2}

def embed(kind: str, title: str, description: str = "") -> discord.Embed:
    return discord.Embed(title=title, description=description, color=COLORS.get(kind, COLORS["info"]), timestamp=discord.utils.utcnow())

def success(title: str, text: str): return embed("success", title, text)
def error(title: str, text: str): return embed("error", title, text)
def warning(title: str, text: str): return embed("warning", title, text)
def info(title: str, text: str): return embed("info", title, text)
def security(title: str, text: str): return embed("security", title, text)
def ticket(title: str, text: str): return embed("ticket", title, text)
