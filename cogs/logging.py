from __future__ import annotations
import discord
from discord.ext import commands
from utils.embeds import info

class Logging(commands.Cog):
    def __init__(self,bot): self.bot=bot
    async def write(self,guild,title,text):
        cfg=self.bot.db.get_config(guild.id); cid=cfg.get("mod_log_channel_id"); channel=guild.get_channel(cid) if cid else None
        if channel:
            try: await channel.send(embed=info(title,text))
            except discord.HTTPException: pass
    @commands.Cog.listener()
    async def on_member_join(self,m): await self.write(m.guild,"Member joined",f"{m.mention} (`{m.id}`)")
    @commands.Cog.listener()
    async def on_member_remove(self,m): await self.write(m.guild,"Member left",f"{m} (`{m.id}`)")
    @commands.Cog.listener()
    async def on_message_delete(self,m):
        if m.guild and not m.author.bot: await self.write(m.guild,"Message deleted",f"Author: {m.author.mention}\nChannel: {m.channel.mention}\n{m.content[:1000] or '[no text]'}")
    @commands.Cog.listener()
    async def on_message_edit(self,before,after):
        if before.guild and before.content != after.content and not before.author.bot: await self.write(before.guild,"Message edited",f"Author: {before.author.mention}\nChannel: {before.channel.mention}\nBefore: {before.content[:500]}\nAfter: {after.content[:500]}")
async def setup(bot): await bot.add_cog(Logging(bot))
