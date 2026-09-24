from __future__ import annotations
import discord
from discord.ext import commands
# discord.py-captcha currently exposes discord_captcha. The adapter keeps package API changes isolated.
try:
    from discord_captcha import Captcha
except ImportError:
    Captcha = None
from utils.embeds import success,error,warning

class Verification(commands.Cog):
    def __init__(self,bot): self.bot=bot
    @commands.Cog.listener()
    async def on_member_join(self,m):
        cfg=self.bot.db.get_config(m.guild.id); role=m.guild.get_role(cfg.get('unverified_role_id')) if cfg.get('unverified_role_id') else None
        if role and role < m.guild.me.top_role:
            try: await m.add_roles(role,reason='Verification')
            except discord.HTTPException: return
        if cfg.get('verification_channel_id') and Captcha:
            channel=m.guild.get_channel(cfg['verification_channel_id'])
            if channel:
                try:
                    # The package owns generation and answer checking; no answer is exposed here.
                    captcha=Captcha(channel=channel, member=m)
                    await captcha.start()
                except Exception:
                    await channel.send(embed=warning('Verification unavailable','Please contact staff to complete verification.'),delete_after=15)
    async def verify(self,m):
        cfg=self.bot.db.get_config(m.guild.id); un=m.guild.get_role(cfg.get('unverified_role_id')); ver=m.guild.get_role(cfg.get('verified_role_id'))
        if ver and m.guild.me and ver < m.guild.me.top_role:
            if un: await m.remove_roles(un,reason='CAPTCHA passed')
            await m.add_roles(ver,reason='CAPTCHA passed')
async def setup(bot): await bot.add_cog(Verification(bot))
