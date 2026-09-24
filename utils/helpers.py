from __future__ import annotations
import discord

def emoji_key(value: str|discord.Emoji|discord.PartialEmoji) -> str:
    return str(value)

def mention_ids(text: str) -> int:
    return len(discord.utils.findall(r"<@!?\d+>", text))
