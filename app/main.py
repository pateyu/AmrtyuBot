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
import time
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
async def interactions(request: Request, x_signature_ed25519: str = Header(None), x_signature_timestamp: str = Header(None)):
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
        if command == "showcourses":
            return await show_courses()
        elif command == "getcourseassignments":
            course_id = int(body_json["data"]["options"][0]["value"])
            num_assignments = int(body_json["data"]["options"][1]["value"]) if len(body_json["data"]["options"]) > 1 else 5
            return await get_course_assignments(course_id, num_assignments)
    return {"type": 4, "data": {"content": "Unknown command"}}

# Retrieve available courses
async def show_courses():
    courses = canvas.get_courses(enrollment_state="active")
    course_list = "\n".join([f"{course.name} (ID: {course.id})" for course in courses])
    return {"type": 4, "data": {"content": f"Available courses:\n{course_list}"}}

# Get upcoming assignments for a specific course
async def get_course_assignments(course_id: int, num_assignments: int = 5):
    course = canvas.get_course(course_id)
    assignments = sorted(course.get_assignments(), key=lambda a: a.due_at if a.due_at else "")
    
    current_time = datetime.utcnow()
    upcoming_assignments = [a for a in assignments if a.due_at and current_time < datetime.strptime(a.due_at, CANVAS_DATE_FORMAT)]
    
    assignment_list = ""
    for assignment in upcoming_assignments[:num_assignments]:
        due_date = pytz.utc.localize(datetime.strptime(assignment.due_at, CANVAS_DATE_FORMAT))
        assignment_list += f"{assignment.name} - Due: {due_date.strftime(OUTPUT_DATE_FORMAT)}\n"
    
    return {"type": 4, "data": {"content": f"Upcoming assignments for course {course.name}:\n{assignment_list}"}}
# Register commands with Discord
@app.post("/register_commands")
async def register_commands():
    for command in commands:
        response = requests.post(f"https://discord.com/api/v9/applications/{APPLICATION_ID}/commands", json=command, headers=headers)
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"status": "Commands registered successfully"}

# Delete all commands from Discord
@app.delete("/delete_all_commands")
async def delete_all_commands():
    get_url = f"https://discord.com/api/v9/applications/{APPLICATION_ID}/commands"
    response = requests.get(get_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    commands = response.json()

    for command in commands:
        delete_url = f"https://discord.com/api/v9/applications/{APPLICATION_ID}/commands/{command['id']}"
        delete_response = requests.delete(delete_url, headers=headers)

        # Handle rate limits
        if delete_response.status_code == 429:
            retry_after = delete_response.json().get('retry_after', 1)
            print(f"Rate limited. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)

        elif delete_response.status_code != 204:
            raise HTTPException(status_code=delete_response.status_code, detail=delete_response.text)

    return {"status": "All commands deleted successfully"}

# AWS Lambda handler
handler = Mangum(app)  
