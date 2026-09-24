from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from utils.embeds import ticket,success,error,info
from utils.permissions import staff

class CloseView(discord.ui.View):
    def __init__(self,cog): super().__init__(timeout=None); self.cog=cog
    @discord.ui.button(label='Close Ticket',emoji='🔒',style=discord.ButtonStyle.danger,custom_id='ticket:close')
    async def close(self,i,b): await self.cog.close(i)

class TicketView(discord.ui.View):
    def __init__(self,cog): super().__init__(timeout=None); self.cog=cog
    @discord.ui.button(label='Create Ticket',emoji='🎫',style=discord.ButtonStyle.primary,custom_id='ticket:create')
    async def create(self,i,b): await self.cog.create(i)

class Tickets(commands.Cog):
    def __init__(self,bot): self.bot=bot
    group=app_commands.Group(name='ticket',description='Support tickets')
    async def create(self,i):
        if self.bot.db.ticket_for_user(i.guild.id,i.user.id): return await i.response.send_message(embed=error('Already open','You already have an open ticket.'),ephemeral=True)
        cfg=self.bot.db.get_config(i.guild.id); cat=i.guild.get_channel(cfg.get('ticket_category_id')) if cfg.get('ticket_category_id') else None; support=i.guild.get_role(cfg.get('support_role_id')) if cfg.get('support_role_id') else None
        overwrites={i.guild.default_role:discord.PermissionOverwrite(view_channel=False),i.user:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True)}
        if support: overwrites[support]=discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True)
        channel=await i.guild.create_text_channel(f'ticket-{i.user.name[:20]}',category=cat,overwrites=overwrites,reason='Ticket created'); self.bot.db.create_ticket(i.guild.id,channel.id,i.user.id)
        await channel.send(embed=ticket('🎫 Ticket',f'Hello {i.user.mention}! Please describe your issue in detail.'),view=CloseView(self)); await i.response.send_message(embed=success('Ticket created',channel.mention),ephemeral=True)
    async def close(self,i):
        row=self.bot.db.ticket_for_channel(i.guild.id,i.channel.id)
        if not row:return await i.response.send_message(embed=error('Not a ticket','This channel is not an open ticket.'),ephemeral=True)
        member=i.user if isinstance(i.user,discord.Member) else None
        if member and i.user.id != row['user_id'] and not staff(member,self.bot.db.get_config(i.guild.id).get('support_role_id')): return await i.response.send_message(embed=error('Denied','Only the creator or support staff can close this ticket.'),ephemeral=True)
        lines=[]
        try:
            async for m in i.channel.history(limit=500,oldest_first=True): lines.append(f'[{m.created_at.isoformat()}] {m.author}: {m.content}')
        except discord.HTTPException: pass
        transcript='\n'.join(lines) or 'No messages.'; cfg=self.bot.db.get_config(i.guild.id); log=i.guild.get_channel(cfg.get('ticket_log_channel_id')) if cfg.get('ticket_log_channel_id') else None
        if log:
            file=discord.File(__import__('io').BytesIO(transcript.encode()),filename=f'transcript-{i.channel.id}.txt'); await log.send(embed=info('Ticket closed',f'Closed by {i.user.mention}'),file=file)
        self.bot.db.close_ticket(i.guild.id,i.channel.id); await i.response.send_message(embed=success('Closing','This ticket will be archived shortly.')); await i.channel.edit(name=f'closed-{i.channel.name}', overwrites={i.guild.default_role:discord.PermissionOverwrite(view_channel=False)}); await i.channel.delete(delay=5)
    @group.command(name='setup')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_panel(self,i,channel:discord.TextChannel): await channel.send(embed=ticket('🎫 Support','Need help? Click below to create a private support ticket.'),view=TicketView(self)); await i.response.send_message(embed=success('Ticket panel','Panel created.'),ephemeral=True)
    @group.command(name='close')
    async def close_cmd(self,i): await self.close(i)
    @group.command(name='claim')
    async def claim(self,i):
        row=self.bot.db.ticket_for_channel(i.guild.id,i.channel.id)
        if not row or not staff(i.user,self.bot.db.get_config(i.guild.id).get('support_role_id')): return await i.response.send_message(embed=error('Denied','Support staff only.'),ephemeral=True)
        self.bot.db.claim_ticket(i.guild.id,i.channel.id,i.user.id); await i.response.send_message(embed=success('Claimed',f'{i.user.mention} claimed this ticket.'))
    @group.command(name='rename')
    async def rename(self,i,name:str):
        if not self.bot.db.ticket_for_channel(i.guild.id,i.channel.id) or not staff(i.user,self.bot.db.get_config(i.guild.id).get('support_role_id')): return await i.response.send_message(embed=error('Denied','Support staff only.'),ephemeral=True)
        await i.channel.edit(name=name[:90]); await i.response.send_message(embed=success('Renamed',name))
    @group.command(name='add')
    async def add(self,i,user:discord.Member): await i.channel.set_permissions(user,view_channel=True,send_messages=True,read_message_history=True); await i.response.send_message(embed=success('Added',user.mention))
    @group.command(name='remove')
    async def remove(self,i,user:discord.Member): await i.channel.set_permissions(user,overwrite=None); await i.response.send_message(embed=success('Removed',user.mention))
    @group.command(name='transcript')
    async def transcript(self,i): await i.response.send_message(embed=info('Transcript','Transcripts are automatically sent to the configured ticket log when closed.'),ephemeral=True)
async def setup(bot): await bot.add_cog(Tickets(bot)); bot.add_view(TicketView(bot.get_cog('Tickets'))); bot.add_view(CloseView(bot.get_cog('Tickets')))
