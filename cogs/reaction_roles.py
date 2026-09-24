from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from utils.embeds import success,error,info
from utils.permissions import bot_can_manage_role,staff

class ReactionRoles(commands.Cog):
    def __init__(self,bot): self.bot=bot
    group=app_commands.Group(name='rr',description='Persistent reaction roles')
    @group.command(name='setup')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_panel(self,i,channel:discord.TextChannel,title:str='Choose your roles',description:str='React below to receive a role.'):
        msg=await channel.send(embed=info(title,description)); await i.response.send_message(embed=success('Created',msg.jump_url),ephemeral=True)
    @group.command(name='add')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def add(self,i,message_id:str,emoji:str,role:discord.Role):
        if not bot_can_manage_role(i.guild,role) or role.permissions.administrator: return await i.response.send_message(embed=error('Denied','Role is above the bot, managed, default, or dangerous.'),ephemeral=True)
        msg=await i.channel.fetch_message(int(message_id)); await msg.add_reaction(emoji); self.bot.db._execute('INSERT OR REPLACE INTO reaction_roles VALUES(?,?,?,?)',(i.guild.id,int(message_id),emoji,role.id)); await i.response.send_message(embed=success('Saved',f'{emoji} → {role.mention}'),ephemeral=True)
    @group.command(name='remove')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def remove(self,i,message_id:str,emoji:str): self.bot.db._execute('DELETE FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?',(i.guild.id,int(message_id),emoji)); await i.response.send_message(embed=success('Removed','Reaction role mapping removed.'),ephemeral=True)
    @group.command(name='list')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def list(self,i): rows=self.bot.db._execute('SELECT * FROM reaction_roles WHERE guild_id=?',(i.guild.id,),many=True); await i.response.send_message(embed=info('Reaction roles','\n'.join(f"{r['message_id']} {r['emoji']} → <@&{r['role_id']}>" for r in rows) or 'None configured.'),ephemeral=True)
    async def handle(self,payload,add):
        if payload.guild_id is None:return
        row=self.bot.db._execute('SELECT role_id FROM reaction_roles WHERE guild_id=? AND message_id=? AND emoji=?',(payload.guild_id,payload.message_id,str(payload.emoji)),one=True)
        if not row:return
        guild=self.bot.get_guild(payload.guild_id); member=guild.get_member(payload.user_id) if guild else None; role=guild.get_role(row['role_id']) if guild else None
        if member and role and bot_can_manage_role(guild,role):
            try: await (member.add_roles(role) if add else member.remove_roles(role))
            except discord.HTTPException: pass
    @commands.Cog.listener()
    async def on_raw_reaction_add(self,p):
        if not self.bot.get_user(p.user_id) or not self.bot.get_user(p.user_id).bot: await self.handle(p,True)
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self,p): await self.handle(p,False)
async def setup(bot): await bot.add_cog(ReactionRoles(bot))
