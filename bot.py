from __future__ import annotations
import asyncio, logging
import discord
from discord.ext import commands
from database import Database
from config import TOKEN,GUILD_ID,DATABASE_PATH

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s: %(message)s')
log=logging.getLogger('discord-security-bot')

class SecurityBot(commands.Bot):
    def __init__(self):
        intents=discord.Intents.default(); intents.members=True; intents.message_content=True; intents.messages=True; intents.reactions=True; intents.moderation=True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.db=Database(DATABASE_PATH)
    async def setup_hook(self):
        for name in ('logging','configuration','verification','moderation','tickets','reaction_roles','antispam','antiraid','antinuke'):
            try: await self.load_extension(f'cogs.{name}')
            except Exception: log.exception('Could not load cog %s',name)
        guild=discord.Object(id=GUILD_ID); self.tree.copy_global_to(guild=guild); await self.tree.sync(guild=guild)
    async def on_ready(self): log.info('Ready as %s in configured guild %s',self.user,GUILD_ID)
    async def on_command_error(self,ctx,error): log.warning('Command error: %s',error)
    async def on_app_command_error(self,interaction,error):
        log.exception('Slash command error',exc_info=error)
        message='The command could not be completed. Check permissions, hierarchy, and configuration.'
        if isinstance(error,app_commands.MissingPermissions): message='You do not have the required permission.'
        try:
            if interaction.response.is_done(): await interaction.followup.send(message,ephemeral=True)
            else: await interaction.response.send_message(message,ephemeral=True)
        except discord.HTTPException: pass

async def main():
    bot=SecurityBot()
    try: await bot.start(TOKEN)
    except discord.LoginFailure: log.error('Discord rejected the token; token was not printed.')
    finally: await bot.close()

if __name__=='__main__':
    from discord import app_commands
    asyncio.run(main())
