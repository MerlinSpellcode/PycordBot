import discord
from discord.ext import commands
from discord.ui import Button, View
import configparser
import asyncio

intents = discord.Intents.all()
counter_bot = commands.Bot(command_prefix='!', intents=intents)
config = configparser.ConfigParser()

try:
    config.read('config.ini')
except configparser.Error as e:
    print(f"Error reading configuration file: {e}")
    exit(1)

try:
    token = config.get('Bot', 'Token')
    default_channel_id = int(config.get('Bot', 'Channel'))
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"Error reading configuration options: {e}")
    exit(1)

set_count = False

class MyView(View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author
        self.update_count = 0
        self.update_task = None

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.author

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    async def update_counter(self, counter):
        global set_count
        while counter:
            await asyncio.sleep(5)
            self.update_count += 1
            new_embed = discord.Embed(title="Counter", description=str(self.update_count), color=0x00ff00)
            await self.message.edit(embed=new_embed, view=self)

class WorkButton(Button):
    def __init__(self, view):
        super().__init__(style=discord.ButtonStyle.green, label='Work')
        self.parent_view = view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not self.parent_view.update_task:
            self.parent_view.update_task = asyncio.create_task(self.parent_view.update_counter(counter=True))

class CancelButton(Button):
    def __init__(self, view):
        super().__init__(style=discord.ButtonStyle.red, label='Cancel')
        self.parent_view = view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.parent_view.update_task:
            self.parent_view.update_task.cancel()
            self.parent_view.update_task = None
        
        for item in self.parent_view.children:
            item.disabled = True
        
        await self.parent_view.message.edit(view=self.parent_view)
        await interaction.channel.send('Goodbye')

@counter_bot.event
async def on_ready():
    try:
        print(f"We have logged in as {counter_bot.user}")
    except Exception as e:
        print(f"Error when logging in: {e}")

@counter_bot.event
async def on_message(message):
    try:
        if message.channel.id != default_channel_id:
            return

        print(f"Message from {message.author}: {message.content}")
        await counter_bot.process_commands(message)
    except discord.DiscordException as e:
        print(f"Error processing message: {e}")

@counter_bot.command()
async def bot(ctx):
    try:
        embed = discord.Embed(title="Counter", description='0', color=0x00ff00)
        view = MyView(ctx.author)
        view.message = await ctx.send(content='Hello! Its a Counter Bot', embed=embed, view=None)
        view.add_item(WorkButton(view))
        view.add_item(CancelButton(view))
        await view.message.edit(view=view)
    except discord.DiscordException as e:
        print(f"Error when executing bot command: {e}")

try:
    counter_bot.run(token)
except discord.LoginFailure as e:
    print(f"Authentication error: {e}")
except discord.ConnectionClosed as e:
    print(f"Closed connection: {e}")