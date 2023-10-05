import discord
from discord.ext import commands, tasks
from canvasapi import Canvas
from datetime import datetime, timedelta
import json
import pytz
from time import perf_counter

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

API_KEY = config['CANVAS_API_KEY']
API_URL = 'https://umsystem.instructure.com/'
CHANNEL_ID = int(config['CHANNEL_ID'])

CANVAS_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
OUTPUT_DATE_FORMAT = "%A, %B %d, %Y %I:%M %p"

class CanvasCog(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.canvas = Canvas(API_URL, API_KEY)
        self.assignment_alert.start()  # Start the background task

    def cog_unload(self):
        self.assignment_alert.cancel()  # Stop the assignment_alert task

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.wait_until_ready()
        print("canvas.py cog is ready.")

    @commands.command(aliases=["courses"])
    async def show_courses(self, ctx):
        """Retrieve courses using the stored token."""
        courses = self.canvas.get_courses(enrollment_state="active")

        embed = discord.Embed(
            title='Available courses',
            description="Here are your courses:"
        )
        for idx, course in enumerate(courses, start=1):
            course_info = f"Code: {course.course_code}  \n ID: {course.id}"
            embed.add_field(name=f"{idx}. {course.name}", value=course_info, inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["due", "upcoming", "assignments"])
    async def get_assignments(self, ctx, course_id: int, num_assignments: int = 5):
        # gets starts time
        start_time = perf_counter()
        # creates embed
        embed = discord.Embed(description="Retrieving upcoming assignments for course...")
        message = await ctx.send(embed=embed)
    
        # gets course
        course = self.canvas.get_course(course_id)
        #sorts assignments by due date
        sorted_assignments = sorted(
            course.get_assignments(),
            key=lambda a: a.due_at if a.due_at is not None else " "
        )
        #GETS CURRENT TIME
        current_time = datetime.now()
        # gets index of first assignment that is due after current time
        assignment_index = 0
        while (
            assignment_index < len(sorted_assignments) and
            (
                sorted_assignments[assignment_index].due_at is None or
                current_time > datetime.strptime(sorted_assignments[assignment_index].due_at, CANVAS_DATE_FORMAT)
            )
        ):
            assignment_index += 1
        # gets upcoming assignments from user input
        upcoming_assignments = sorted_assignments[assignment_index:min(assignment_index+num_assignments, len(sorted_assignments))]
        # Add each upcoming assignment's name and due date to the embed
        for assignment in upcoming_assignments:
            due_date = pytz.utc.localize(datetime.strptime(assignment.due_at, CANVAS_DATE_FORMAT))
            due_date_ct = due_date.astimezone(pytz.timezone('America/Chicago'))
            embed.add_field(name=assignment.name, value=due_date_ct.strftime(OUTPUT_DATE_FORMAT), inline=False)
        #update embed
        embed.title = course.name
        embed.description = "Here are the upcoming due dates for this course"
        await message.edit(embed=embed)
        print(f"Successfully sent upcoming assignments for {course.name:<80}")
    @tasks.loop(hours=24)
    async def assignment_alert(self):
        ALERT_BEFORE = timedelta(days=2)
        
        # Get all active courses for the user
        user = self.canvas.get_current_user()
        courses = user.get_courses(enrollment_state="active")
        
        for course in courses:
            for assignment in course.get_assignments():
                if assignment.due_at is not None:
                    due_date = pytz.utc.localize(datetime.strptime(assignment.due_at, CANVAS_DATE_FORMAT))
                    current_time = datetime.now(pytz.utc)
                    
                    # Check if the due date is in the future and within the alert period
                    if due_date > current_time and (due_date - current_time) <= ALERT_BEFORE:
                        due_date_ct = due_date.astimezone(pytz.timezone('America/Chicago'))
                        embed = discord.Embed(
                            title="Assignment Due Soon",
                            description=f"Assignment **{assignment.name}** for course **{course.name}** is due on {due_date_ct.strftime(OUTPUT_DATE_FORMAT)}!",
                            color= 0x001F3F
                        )
                        channel = self.client.get_channel(CHANNEL_ID)
                        await channel.send(embed=embed)
                       
    @assignment_alert.before_loop
    async def before_assignment_alert(self):
        await self.client.wait_until_ready()  # Wait for the bot to be ready

async def setup(client):
    await client.add_cog(CanvasCog(client))