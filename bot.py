from discord.ext import commands, tasks
import asyncio
import discord
import os
import json
from database import create_table

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

discord_token = config['TOKEN']
CHANNEL_ID = int(config['CHANNEL_ID'])

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")
            print(f"Loaded Cog: {filename[:-3]}")
        else:
            print("Unable to load pycache folder.")

async def main():
    async with client:
        await create_table()
        await load()
        await client.start(discord_token)

@client.event
async def on_ready():
    print("Bot is ready.")
    channel = client.get_channel(CHANNEL_ID)
    await channel.send("Hello! Study bot is ready!")

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")


asyncio.run(main())