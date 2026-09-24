from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from utils.embeds import success, error, info
from utils.permissions import can_manage

class Configuration(commands.Cog):
    def __init__(self, bot): self.bot = bot
    config_group = app_commands.Group(name="config", description="Configure this server")
    async def set_value(self, interaction, key, value, label):
        if not await can_manage(interaction): return await interaction.response.send_message(embed=error("Denied","Manage Server or Manage Messages is required."), ephemeral=True)
        self.bot.db.set_config(interaction.guild.id, key, value.id if hasattr(value, "id") else value)
        await interaction.response.send_message(embed=success("Saved", f"{label} set to {value}."), ephemeral=True)
    @config_group.command(name="verified-role")
    async def verified(self,i:discord.Interaction,role:discord.Role): await self.set_value(i,"verified_role_id",role,"Verified role")
    @config_group.command(name="unverified-role")
    async def unverified(self,i:discord.Interaction,role:discord.Role): await self.set_value(i,"unverified_role_id",role,"Unverified role")
    @config_group.command(name="verification-channel")
    async def verification_channel(self,i:discord.Interaction,channel:discord.TextChannel): await self.set_value(i,"verification_channel_id",channel,"Verification channel")
    @config_group.command(name="mod-log")
    async def modlog(self,i:discord.Interaction,channel:discord.TextChannel): await self.set_value(i,"mod_log_channel_id",channel,"Moderation log")
    @config_group.command(name="ticket-category")
    async def category(self,i:discord.Interaction,category:discord.CategoryChannel): await self.set_value(i,"ticket_category_id",category,"Ticket category")
    @config_group.command(name="ticket-log")
    async def ticketlog(self,i:discord.Interaction,channel:discord.TextChannel): await self.set_value(i,"ticket_log_channel_id",channel,"Ticket log")
    @config_group.command(name="support-role")
    async def support(self,i:discord.Interaction,role:discord.Role): await self.set_value(i,"support_role_id",role,"Support role")
    @config_group.command(name="staff-role")
    async def staff_role(self,i:discord.Interaction,role:discord.Role): await self.set_value(i,"staff_role_id",role,"Staff role")
    @config_group.command(name="raid-threshold")
    async def threshold(self,i:discord.Interaction,value:app_commands.Range[int,2,100]): await self.set_value(i,"raid_threshold",value,"Raid threshold")
    @config_group.command(name="raid-window")
    async def window(self,i:discord.Interaction,value:app_commands.Range[int,5,300]): await self.set_value(i,"raid_window",value,"Raid window")
    whitelist = app_commands.Group(name="whitelist",description="Manage anti-nuke whitelist",parent=config_group)
    @whitelist.command(name="add")
    async def wl_add(self,i:discord.Interaction,user:discord.Member,reason:str=""): await self.set_value(i,"_noop",0,"Whitelist") if False else None; self.bot.db.add_whitelist(i.guild.id,user.id,reason); await i.response.send_message(embed=success("Whitelisted",f"{user.mention} excluded from automatic anti-nuke actions."),ephemeral=True)
    @whitelist.command(name="remove")
    async def wl_remove(self,i:discord.Interaction,user:discord.Member): self.bot.db.remove_whitelist(i.guild.id,user.id); await i.response.send_message(embed=success("Removed",f"{user.mention} removed from whitelist."),ephemeral=True)
    @whitelist.command(name="list")
    async def wl_list(self,i:discord.Interaction): rows=self.bot.db.whitelist(i.guild.id); await i.response.send_message(embed=info("Whitelist","\n".join(f"<@{r['user_id']}> — {r['reason'] or 'no reason'}" for r in rows) or "No whitelisted users."),ephemeral=True)
async def setup(bot): await bot.add_cog(Configuration(bot))
