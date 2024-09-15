import os
import requests
import yaml
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
from dotenv import load_dotenv
from canvasapi import Canvas
from datetime import datetime, timedelta
import pytz
import nacl.signing
import nacl.encoding
from mangum import Mangum
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
APPLICATION_ID = os.getenv("APPLICATION_ID")
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
CANVAS_API_KEY = os.getenv("CANVAS_API_KEY")
CANVAS_API_URL = os.getenv("CANVAS_API_URL")

CANVAS_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
OUTPUT_DATE_FORMAT = "%A, %B %d, %Y %I:%M %p"

# Initialize FastAPI app
app = FastAPI()

# Initialize Canvas API client
canvas = Canvas(CANVAS_API_URL, CANVAS_API_KEY)

# Load commands from YAML
with open("commands.yaml", "r") as file:
    commands = yaml.safe_load(file)

headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}

# Root path to check the API status
@app.get("/")
async def root():
    return JSONResponse(content={"message": "FastAPI Discord Bot Lambda running successfully"})

# Verify signature manually
def verify_discord_signature(signature: str, timestamp: str, body: str):
    message = timestamp + body
    try:
        verify_key = nacl.signing.VerifyKey(DISCORD_PUBLIC_KEY, encoder=nacl.encoding.HexEncoder)
        verify_key.verify(message.encode(), bytes.fromhex(signature))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid request signature")

@app.post("/")
async def interactions(request: Request, background_tasks: BackgroundTasks, x_signature_ed25519: str = Header(None), x_signature_timestamp: str = Header(None)):
    body = await request.body()
    try:
        verify_discord_signature(x_signature_ed25519, x_signature_timestamp, body.decode())
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid request signature")

    body_json = await request.json()

    # Respond to the Discord PING event
    if body_json["type"] == 1:
        return {"type": 1}  # PONG

    # Handle a command or interaction
    if body_json["type"] == 2:  # Slash command
        command = body_json["data"]["name"]
        interaction_id = body_json["id"]
        interaction_token = body_json["token"]

        # Acknowledge interaction immediately to avoid timeout
        response_url = f"https://discord.com/api/v9/interactions/{interaction_id}/{interaction_token}/callback"
        requests.post(response_url, json={"type": 5}, headers=headers)

        # Process commands
        if command == "showcourses":
            background_tasks.add_task(process_show_courses, interaction_id, interaction_token)
        elif command == "getcourseassignments":
            course_id = int(body_json["data"]["options"][0]["value"])
            num_assignments = int(body_json["data"]["options"][1]["value"]) if len(body_json["data"]["options"]) > 1 else 5
            background_tasks.add_task(process_get_course_assignments, interaction_id, interaction_token, course_id, num_assignments)
        elif command == "getassignments":
            background_tasks.add_task(process_assignments_due_next_week, interaction_id, interaction_token)

    return {"type": 4, "data": {"content": "Processing your request..."}}

# Process to fetch and send available courses
async def process_show_courses(interaction_id: str, interaction_token: str):
    courses = canvas.get_courses(enrollment_state="active")
    course_list = "\n".join([f"{course.name} (ID: {course.id})" for course in courses])
    if not course_list:
        course_list = "No active courses found."
    
    response_url = f"https://discord.com/api/v9/webhooks/{APPLICATION_ID}/{interaction_token}"
    data = {"content": f"Available courses:\n{course_list}"}
    requests.post(response_url, json=data, headers=headers)
    
#Process to fetch and send upcoming assignments for a specific course
async def process_get_course_assignments(interaction_id: str, interaction_token: str, course_id: int, num_assignments: int = 5):
    course = canvas.get_course(course_id)
    
    # Sort assignments by due date
    assignments = sorted(course.get_assignments(), key=lambda a: a.due_at if a.due_at else "")
    
    # Set current_time as an offset-aware datetime object (UTC)
    current_time = datetime.now(tz=pytz.utc)
    
    # Ensure due_at times are offset-aware by localizing them to UTC
    upcoming_assignments = [
        a for a in assignments
        if a.due_at and current_time < pytz.utc.localize(datetime.strptime(a.due_at, CANVAS_DATE_FORMAT))
    ]
    
    # Build the assignment list string
    assignment_list = ""
    for assignment in upcoming_assignments[:num_assignments]:
        # Convert due_at to a localized datetime in UTC
        due_date = pytz.utc.localize(datetime.strptime(assignment.due_at, CANVAS_DATE_FORMAT))
        assignment_list += f"{assignment.name} - Due: {due_date.strftime(OUTPUT_DATE_FORMAT)}\n"
    
    # Handle case where there are no upcoming assignments
    if not assignment_list:
        assignment_list = "No upcoming assignments."

    # Send the response to Discord
    response_url = f"https://discord.com/api/v9/webhooks/{APPLICATION_ID}/{interaction_token}"
    data = {"content": f"Upcoming assignments for course {course.name}:\n{assignment_list}"}
    requests.post(response_url, json=data, headers=headers)

# Process to fetch and send assignments due in the next week
async def process_assignments_due_next_week(interaction_id: str, interaction_token: str):
    courses = canvas.get_courses(enrollment_state="active")
    current_time = datetime.now(tz=pytz.utc)
    
    # Calculate end of the next week (7 days from now)
    next_week_end = current_time + timedelta(days=7)
    next_week_end = next_week_end.replace(hour=23, minute=59, second=59, tzinfo=pytz.utc)
    
    assignment_list = ""
    for course in courses:
        assignments = sorted(course.get_assignments(), key=lambda a: a.due_at if a.due_at else "")
        for assignment in assignments:
            if assignment.due_at:
                due_date = pytz.utc.localize(datetime.strptime(assignment.due_at, CANVAS_DATE_FORMAT))
                if current_time < due_date <= next_week_end:
                    assignment_list += f"{assignment.name} (Course: {course.name}) - Due: {due_date.strftime(OUTPUT_DATE_FORMAT)}\n"
    
    if not assignment_list:
        assignment_list = "No assignments due in the next week."
    
    response_url = f"https://discord.com/api/v9/webhooks/{APPLICATION_ID}/{interaction_token}"
    data = {"content": f"Assignments due next week:\n{assignment_list}"}
    requests.post(response_url, json=data, headers=headers)

# AWS Lambda handler
handler = Mangum(app)
