from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from utils.embeds import success,error,info,warning
from utils.permissions import target_is_manageable,can_manage

class Moderation(commands.Cog):
    def __init__(self,bot): self.bot=bot
    async def ok(self,i,action,target,reason): self.bot.db.log_moderation(i.guild.id,action,target.id if target else None,i.user.id,reason); await i.response.send_message(embed=success(action.title(),f"Target: {target}\nReason: {reason}"),ephemeral=True)
    async def allowed(self,i): return i.guild and (i.user.guild_permissions.moderate_members or i.user.guild_permissions.manage_messages)
    @app_commands.command()
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self,i:discord.Interaction,user:discord.Member,reason:str="No reason provided"):
        if not target_is_manageable(i.guild,user): return await i.response.send_message(embed=error("Denied","That member is above the bot or cannot be managed."),ephemeral=True)
        await user.ban(reason=reason); await self.ok(i,"ban",user,reason)
    @app_commands.command()
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self,i,user:discord.Member,reason:str="No reason provided"):
        if not target_is_manageable(i.guild,user): return await i.response.send_message(embed=error("Denied","That member cannot be managed."),ephemeral=True)
        await user.kick(reason=reason); await self.ok(i,"kick",user,reason)
    @app_commands.command()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self,i,user:discord.Member,minutes:app_commands.Range[int,1,40320],reason:str="No reason provided"):
        if not target_is_manageable(i.guild,user): return await i.response.send_message(embed=error("Denied","That member cannot be managed."),ephemeral=True)
        await user.timeout(discord.utils.utcnow()+discord.timedelta(minutes=minutes),reason=reason); await self.ok(i,"timeout",user,reason)
    @app_commands.command()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self,i,user:discord.Member): await user.timeout(None,reason="Manual removal"); await self.ok(i,"untimeout",user,"Manual removal")
    @app_commands.command()
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self,i,user:discord.Member,reason:str): self.bot.db.add_warning(i.guild.id,user.id,i.user.id,reason); await self.ok(i,"warn",user,reason)
    @app_commands.command()
    async def warnings(self,i,user:discord.Member):
        if not await can_manage(i): return await i.response.send_message(embed=error("Denied","Staff permission required."),ephemeral=True)
        rows=self.bot.db.warnings(i.guild.id,user.id); text="\n".join(f"#{r['id']} <t:{int(discord.utils.parse_time(r['created_at']).timestamp())}:R> — {r['reason']}" for r in rows) or "No warnings."
        await i.response.send_message(embed=info(f"Warnings for {user}",text),ephemeral=True)
    @app_commands.command(name="clear")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self,i:discord.Interaction,amount:app_commands.Range[int,1,100]): n=await i.channel.purge(limit=amount); await self.ok(i,"purge",i.user,f"Deleted {len(n)} messages")
    @app_commands.command()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self,i:discord.Interaction,seconds:app_commands.Range[int,0,21600]): await i.channel.edit(slowmode_delay=seconds); await self.ok(i,"slowmode",i.user,f"{seconds} seconds")
    @app_commands.command()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self,i:discord.Interaction): await i.channel.set_permissions(i.guild.default_role,send_messages=False); await self.ok(i,"lock",i.user,"Channel locked")
    @app_commands.command()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self,i:discord.Interaction): await i.channel.set_permissions(i.guild.default_role,send_messages=None); await self.ok(i,"unlock",i.user,"Channel unlocked")
async def setup(bot): await bot.add_cog(Moderation(bot))
