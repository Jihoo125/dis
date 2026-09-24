from __future__ import annotations
from collections import defaultdict,deque
import time, discord
from discord.ext import commands
from utils.embeds import security

class AntiNuke(commands.Cog):
    def __init__(self,bot): self.bot=bot; self.actions=defaultdict(deque)
    async def audit(self,guild,kind):
        try: entries=[e async for e in guild.audit_logs(limit=1,action=kind)]
        except (discord.Forbidden,discord.HTTPException): return
        if not entries:return
        e=entries[0]; uid=e.user.id; now=time.monotonic(); q=self.actions[(guild.id,uid,kind)]; q.append(now)
        while q and now-q[0]>20:q.popleft()
        if len(q)>=4 and not self.bot.db.is_whitelisted(guild.id,uid):
            cfg=self.bot.db.get_config(guild.id); ch=guild.get_channel(cfg.get('mod_log_channel_id')) if cfg.get('mod_log_channel_id') else None
            if ch:
                try: await ch.send(embed=security('Anti-nuke alert',f"{e.user.mention} performed {len(q)} {kind.name} actions in 20 seconds."))
                except discord.HTTPException: pass
    @commands.Cog.listener()
    async def on_guild_channel_delete(self,c): await self.audit(c.guild,discord.AuditLogAction.channel_delete)
    @commands.Cog.listener()
    async def on_guild_role_delete(self,r): await self.audit(r.guild,discord.AuditLogAction.role_delete)
    @commands.Cog.listener()
    async def on_member_ban(self,g,m): await self.audit(g,discord.AuditLogAction.ban)
    @commands.Cog.listener()
    async def on_member_remove(self,m): await self.audit(m.guild,discord.AuditLogAction.kick)
async def setup(bot): await bot.add_cog(AntiNuke(bot))
