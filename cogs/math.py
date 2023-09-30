
from discord.ext import commands

class math(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("math.py cog is ready.")

    @commands.command()
    async def add(self, ctx, *arr: int):
        """Add numbers together."""
        result = 0
        for i in arr:
            result += int(i)
        await ctx.send(f"Result = {result}")
    
    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello!")

    @commands.command()
    async def multiply(self, ctx, *arr: int):
        """Multiply numbers together."""
        result = 1  
        for i in arr:
            result *= i
        await ctx.send(f"Result = {result}")

async def setup(client):
    await client.add_cog(math(client))
