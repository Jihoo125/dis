from __future__ import annotations
import discord

async def can_manage(interaction: discord.Interaction) -> bool:
    return bool(interaction.guild and (interaction.user.guild_permissions.manage_guild or interaction.user.guild_permissions.manage_messages))

def bot_can_manage_role(guild: discord.Guild, role: discord.Role) -> bool:
    return guild.me is not None and role < guild.me.top_role and not role.is_default() and not role.managed

def staff(member: discord.Member, role_id: int|None = None) -> bool:
    return member.guild_permissions.manage_guild or member.guild_permissions.manage_messages or bool(role_id and any(r.id == role_id for r in member.roles))

def target_is_manageable(guild: discord.Guild, target: discord.Member) -> bool:
    return guild.me is not None and target != guild.me and target.top_role < guild.me.top_role
