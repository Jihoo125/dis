from __future__ import annotations
from collections import deque
import time, discord
from discord.ext import commands
from discord import app_commands
from utils.embeds import security,success,info

class AntiRaid(commands.Cog):
    def __init__(self,bot): self.bot=bot; self.joins=deque()
    def active(self,guild):
        cfg=self.bot.db.get_config(guild.id); now=time.monotonic(); window=cfg['raid_window'];
        while self.joins and now-self.joins[0]>window:self.joins.popleft()
        return len(self.joins)>=cfg['raid_threshold']
    @commands.Cog.listener()
    async def on_member_join(self,m):
        self.joins.append(time.monotonic())
        if self.active(m.guild) and not self.bot.db.get_config(m.guild.id)['lockdown_enabled']:
            self.bot.db.set_config(m.guild.id,'lockdown_enabled',1); cfg=self.bot.db.get_config(m.guild.id); ch=m.guild.get_channel(cfg.get('mod_log_channel_id')) if cfg.get('mod_log_channel_id') else None
            if ch:
                try: await ch.send(embed=security("Raid detected","Join threshold exceeded; lockdown enabled for unverified members."))
                except discord.HTTPException: pass
    group=app_commands.Group(name='raid',description='Raid protection')
    @group.command(name='status')
    async def status(self,i):
        cfg=self.bot.db.get_config(i.guild.id); await i.response.send_message(embed=info('Raid protection',f"Current joins: {len(self.joins)}\nThreshold: {cfg['raid_threshold']}\nWindow: {cfg['raid_window']} seconds\nLockdown: {'Active' if cfg['lockdown_enabled'] else 'Inactive'}"),ephemeral=True)
    @group.command(name='lockdown')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def lockdown(self,i): self.bot.db.set_config(i.guild.id,'lockdown_enabled',1); await i.response.send_message(embed=security('Lockdown enabled','Unverified access remains restricted.'),ephemeral=True)
    @group.command(name='unlock')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def unlock(self,i): self.bot.db.set_config(i.guild.id,'lockdown_enabled',0); await i.response.send_message(embed=success('Lockdown disabled','Normal configured access is restored.'),ephemeral=True)
async def setup(bot): await bot.add_cog(AntiRaid(bot))
