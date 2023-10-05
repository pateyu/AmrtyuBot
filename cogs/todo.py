import discord
from discord.ext import commands
from database import create_connection

class todo(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("todo.py cog is ready.")

    @commands.command()
    async def addTask(self, ctx, *, task: str):
        user_id = ctx.author.id
        conn = await create_connection()
        async with conn.execute('INSERT INTO tasks (user_id, task) VALUES (?, ?)', (user_id, task)):
            await conn.commit()

        await conn.close()

        embed = discord.Embed(
            title="Task Added",
            description=f"Added task: {task}",
            color=discord.Color.green()  
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def removeTask(self, ctx, *, task: int):
        user_id = ctx.author.id
        conn = await create_connection()
        async with conn.execute('SELECT task FROM tasks WHERE user_id = ?', (user_id,)) as cursor:
            user_tasks = await cursor.fetchall()

        if not user_tasks:
            embed = discord.Embed(
                title="No Tasks",
                description="You have no tasks.",
                color=discord.Color.red()  
            )
            await ctx.send(embed=embed)
            await conn.close()
            return

        if task > len(user_tasks) or task <= 0:
            embed = discord.Embed(
                title="Task Not Found",
                description=f"No task found with number {task}.",
                color=discord.Color.red()  
            )
            await ctx.send(embed=embed)
            await conn.close()
            return

        removed_task = user_tasks.pop(task - 1)[0]
        async with conn.execute('DELETE FROM tasks WHERE user_id = ? AND task = ?', (user_id, removed_task)):
            await conn.commit()

        await conn.close()

        embed = discord.Embed(
            title="Task Removed",
            description=f"Removed task: {removed_task}",
            color=discord.Color.green() 
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def showTasks(self, ctx):
        user_id = ctx.author.id
        conn = await create_connection()
        async with conn.execute('SELECT task FROM tasks WHERE user_id = ?', (user_id,)) as cursor:
            user_tasks = await cursor.fetchall()
        await conn.close()
        if not user_tasks:
            embed = discord.Embed(
                title="No Tasks",
                description="You have no tasks.",
                color=discord.Color.red()  
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"{ctx.author.name}'s To-Do List",
                description="\n".join([f"{i + 1}. {task[0]}" for i, task in enumerate(user_tasks)]),
                color=discord.Color.blue()  
            )
            await ctx.send(embed=embed)

async def setup(client):
    await client.add_cog(todo(client))
