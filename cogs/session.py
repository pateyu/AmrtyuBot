from discord.ext import commands, tasks
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import json

@dataclass
class Session:
    is_active: bool = False
    is_pomodoro: bool = False
    start_time: datetime = datetime.min
    total_time: timedelta = timedelta(0)


with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    
MAX_SESSION = 60
CHANNEL_ID = 1154552490361102426
session = Session()

class SessionCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("session.py cog is ready.")

    @tasks.loop(minutes=MAX_SESSION)
    async def break_remind(self):
        channel = self.client.get_channel(CHANNEL_ID)
        await channel.send(f"**Time to take a break!** You've been studying for {MAX_SESSION} minutes")
    
    @commands.command()
    async def start(self, ctx, session_length: int = None):
        global session
        if session.is_active:
            await ctx.send("Session is already active!")
            return

        session.is_active = True
        session.start_time = datetime.now()

  
        if session_length is None:
            await ctx.send("Study session has started with no time limit!")
            return

        num_breaks = session_length // MAX_SESSION
        self.break_remind.start(loop_count=num_breaks)
        await ctx.send(f"Study session has started for {session_length} minutes.")

    @commands.command()
    async def end(self, ctx):
        global session
        if not session.is_active:
            await ctx.send("No session is active to end!")
            return

        end_time = datetime.now()
        session.total_time += end_time - session.start_time
        session.is_active = False
        self.break_remind.stop()
        await ctx.send(f"Study session has been ended! Total study time: {session.total_time}")

    @commands.command()
    async def pomodoro(self, ctx, work_time: int = 25, break_time: int = 5, cycles: int = 1):
        global session
        if session.is_active:
            await ctx.send("Session is already active!")
            return

        session.is_active = True
        session.is_pomodoro = True
        session.start_time = datetime.now()

        for _ in range(cycles):
            if not session.is_active:
                break
            await ctx.send(f"Starting a {work_time}-minute work period now!")
            await asyncio.sleep(work_time * 60)
            session.total_time += timedelta(minutes=work_time)

            await ctx.send(f"Time for a {break_time}-minute break!")
            await asyncio.sleep(break_time * 60)

        session.is_active = False
        session.is_pomodoro = False
        await ctx.send(f"Pomodoro session has ended! Total study time: {session.total_time}")

    @commands.command()
    async def stop(self, ctx):
        global session
        if not session.is_active or not session.is_pomodoro:
            await ctx.send("No Pomodoro session is active to stop!")
            return

        end_time = datetime.now()
        session.total_time += end_time - session.start_time
        session.is_active = False
        await ctx.send("Pomodoro session has been stopped!")
        await ctx.send(f"Total study time: {session.total_time}")

async def setup(client):
    await client.add_cog(SessionCog(client))
