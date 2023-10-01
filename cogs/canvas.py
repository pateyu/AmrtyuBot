import discord
from discord import client
from discord.ext import commands,tasks
from canvasapi import Canvas
from canvasapi.course import Course, Assignment
import datetime
import pytz
import pandas as pd
from time import perf_counter
import json

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

API_KEY = config['API_KEY']
API_URL = 'https://umsystem.instructure.com/'


class CanvasCog(commands.Cog):
    @commands.Cog.listener()
    async def on_ready(self):
        print("canvas.py cog is ready.")



async def setup(client):
    await client.add_cog(CanvasCog(client))






