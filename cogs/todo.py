from discord.ext import commands


tasks = {}

class task(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("todo.py cog is ready.")

    @commands.command()
    async def addTask(self, ctx, *, task: str): 
        user_id = ctx.author.id
        if user_id not in tasks:
            tasks[user_id] = []
        tasks[user_id].append(task)
        await ctx.send(f"Added task: {task}")

    @commands.command()
    async def removeTask(self, ctx, *, task: int):
        user_id = ctx.author.id
        if user_id not in tasks:
            await ctx.send("You have no tasks.")
            
        if task not in tasks[user_id]:
            await ctx.send(f"No task found with number {task}.")
            
        else:
            removed_task = tasks[user_id].pop(task-1)
            await ctx.send(f"Removed task: {removed_task}")
            
    @commands.command()
    async def showTasks(self, ctx):
        user_id = ctx.author.id
        if user_id not in tasks or not tasks[user_id]:
            await ctx.send("You have no tasks on your to-do list")
            return
        else:
            tasks_str = "\n".join([f"{i+1}) {task}" for i, task in enumerate(tasks[user_id])])
            await ctx.send(f"Your to-do list: \n{tasks_str}")


async def setup(client):
    await client.add_cog(task(client))
