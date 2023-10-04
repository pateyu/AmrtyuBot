import discord
from discord.ext import commands
from database import create_connection


tasks = {}

class task(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.conn = create_connection()

    @commands.Cog.listener()
    async def on_ready(self):
        print("todo.py cog is ready.")

    @commands.command()
    async def addTask(self, ctx, *, task: str): 
        user_id = ctx.author.id
        if user_id not in tasks:
            tasks[user_id] = []
        tasks[user_id].append(task)
        embed = discord.Embed(
            title="Task Added",
            description=f"Added task: {task}",
            color=discord.Color.green()  
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def removeTask(self, ctx, *, task: int):
        user_id = ctx.author.id
        if user_id not in tasks:
            embed = discord.Embed(
                title="No Tasks",
                description="You have no tasks.",
                color=discord.Color.red()  
            )
            await ctx.send(embed=embed)
            return
        
        if task > len(tasks[user_id]) or task <= 0:
            embed = discord.Embed(
                title="Task Not Found",
                description=f"No task found with number {task}.",
                color=discord.Color.red()  
            )
            await ctx.send(embed=embed)
            return
        
        removed_task = tasks[user_id].pop(task-1)
        embed = discord.Embed(
            title="Task Removed",
            description=f"Removed task: {removed_task}",
            color=discord.Color.green()  
        )
        await ctx.send(embed=embed)    
             
    @commands.command()
    async def showTasks(self, ctx):
        user_id = ctx.author.id
        if user_id not in tasks or not tasks[user_id]:
            embed = discord.Embed(
                title="No Tasks",
                description="You have no tasks.",
                color=discord.Color.red()  
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"{ctx.author.name}'s To-Do List",
                description="\n".join([f"{i+1}. {task}" for i, task in enumerate(tasks[user_id])]),
                color=discord.Color.blue()  
            )
            await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(task(client))