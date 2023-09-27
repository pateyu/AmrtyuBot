
from discord.ext import commands
import asyncio
import discord
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

# Load the configuration file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Access the token
discord_token = config['TOKEN']
CHANNEL_ID = 1154552490361102426


@dataclass
class Session:
    is_active: bool = False
    is_pomodoro: bool = False
    start_time: datetime = datetime.min
    total_time: timedelta = timedelta(0)


bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
session=Session()
todo_lists = {}


@bot.event
async def on_ready():
    print("Hello, the study bot is ready!")
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("Hello! Study bot is ready!")
@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")

@bot.command()
async def add(ctx, *arr):
    result = 0
    for i in arr:
        result += int(i)
    await ctx.send(f"Result = {result}")
    
@bot.command()
async def multiply(ctx, *arr: int):
    result = 1  # start with 1 because 1 is the identity for multiplication
    for i in arr:
        result *= i
    await ctx.send(f"Result = {result}")

@bot.command()
async def start(ctx):
    global session
    if session.is_active:
        await ctx.send("Session is already active!")
        return

    session.is_active = True
    session.start_time = datetime.now()
    await ctx.send(f"Study session has started.")

@bot.command()
async def end(ctx):
    global session
    if not session.is_active or session.is_pomodoro:
        await ctx.send("No regular session is active to end!")
        return

    end_time = datetime.now()
    session.total_time += end_time - session.start_time
    session.is_active = False
    await ctx.send(f"Study session has been ended! Total study time: {session.total_time}")

@bot.command()
async def pomodoro(ctx, work_time: int = 25, break_time: int = 5, cycles: int = 1):
    global session
    if session.is_active:
        await ctx.send("Session is already active!")
        return

    session.is_active = True
    session.is_pomodoro = True
    session.start_time = datetime.now()

    for _ in range(cycles):
        if not session.is_active:  # Check if session should end prematurely
            break
        await ctx.send(f"Starting a {work_time}-minute work period now!")
        await asyncio.sleep(work_time * 60)
        session.total_time += timedelta(minutes=work_time)

        await ctx.send(f"Time for a {break_time}-minute break!")
        await asyncio.sleep(break_time * 60)

    session.is_active = False
    session.is_pomodoro = False
    await ctx.send(f"Pomodoro session has ended! Total study time: {session.total_time}")

@bot.command()
async def stop(ctx):
    global session
    if not session.is_active or not session.is_pomodoro:
        await ctx.send("No Pomodoro session is active to stop!")
        return

    end_time = datetime.now()
    session.total_time += end_time - session.start_time
    session.is_active = False
    await ctx.send("Pomodoro session has been stopped!")
    await ctx.send(f"Total study time: {session.total_time}")

@bot.command()
async def add_task(ctx, *, task: str):
    """Add a task to the user's to-do list."""
    user_id = ctx.author.id
    if user_id not in todo_lists:
        todo_lists[user_id] = []
    todo_lists[user_id].append(task)
    await ctx.send(f"Task added: {task}")

@bot.command()
async def remove_task(ctx, task_num: int):
    """Remove a task from the user's to-do list by its number."""
    user_id = ctx.author.id
    if user_id not in todo_lists or task_num > len(todo_lists[user_id]) or task_num <= 0:
        await ctx.send(f"No task found with number {task_num}.")
    else:
        removed = todo_lists[user_id].pop(task_num - 1)
        await ctx.send(f"Task removed: {removed}")

@bot.command()
async def view_tasks(ctx):
    """View all tasks in the user's to-do list."""
    user_id = ctx.author.id
    if user_id not in todo_lists or not todo_lists[user_id]:
        await ctx.send(f"You have no tasks in your to-do list.")
    else:
        tasks = "\n".join(f"{i+1}. {task}" for i, task in enumerate(todo_lists[user_id]))
        await ctx.send(f"Your to-do list:\n{tasks}")
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")








bot.run(discord_token)