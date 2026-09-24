from __future__ import annotations
import asyncio, time
from collections import defaultdict, deque
import discord
from discord.ext import commands
from utils.embeds import warning

class AntiSpam(commands.Cog):
    def __init__(self,bot): self.bot=bot; self.events=defaultdict(deque); self.repeats=defaultdict(deque); self.cooldown=set()
    @commands.Cog.listener()
    async def on_message(self,m):
        if not m.guild or m.author.bot or self.bot.db.is_whitelisted(m.guild.id,m.author.id): return
        if m.author.guild_permissions.manage_messages: return
        key=(m.guild.id,m.author.id); now=time.monotonic(); q=self.events[key]; q.append(now)
        while q and now-q[0]>8:q.popleft()
        rq=self.repeats[key]; rq.append((now,m.content));
        while rq and now-rq[0][0]>30:rq.popleft()
        repeated=sum(x==m.content for _,x in rq)>=4; excessive=len(q)>=7 or len(m.mentions)>=6 or m.content.count("@everyone")+m.content.count("@here")>=2
        if (repeated or excessive) and key not in self.cooldown:
            self.cooldown.add(key)
            try:
                await m.delete(); await m.author.timeout(discord.utils.utcnow()+discord.timedelta(seconds=60),reason="Anti-spam")
                await m.channel.send(embed=warning("Anti-spam",f"{m.author.mention} was timed out for spam."),delete_after=8)
            except (discord.Forbidden,discord.HTTPException): pass
            finally: asyncio.get_running_loop().call_later(60,self.cooldown.discard,key)
async def setup(bot): await bot.add_cog(AntiSpam(bot))
