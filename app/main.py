import os
import requests
import yaml
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import nacl.signing
import nacl.encoding
from mangum import Mangum
from fastapi.responses import JSONResponse
import boto3
import time
from canvasapi import Canvas

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
APPLICATION_ID = os.getenv("APPLICATION_ID")
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")

CANVAS_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
OUTPUT_DATE_FORMAT = "%A, %B %d, %Y %I:%M %p"

# Initialize FastAPI app
app = FastAPI()

# DynamoDB table initialization
dynamodb = boto3.resource('dynamodb')
dynamodb_table = dynamodb.Table('StudyBotUserConfig')

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
        user_id = body_json["member"]["user"]["id"]

        # Acknowledge interaction immediately to avoid timeout
        response_url = f"https://discord.com/api/v9/interactions/{interaction_id}/{interaction_token}/callback"
        requests.post(response_url, json={"type": 5}, headers=headers)

        if command == "setup":
            background_tasks.add_task(process_setup_command, interaction_id, interaction_token, user_id, background_tasks)
        else:
            # Check if user has completed setup
            user_config = get_user_config(user_id)
            if not user_config:
                response_message = "Please complete the setup using `/setup` before using this command."
                requests.post(response_url, json={"content": response_message}, headers=headers)
                return

            if command == "showcourses":
                background_tasks.add_task(process_show_courses, interaction_id, interaction_token, user_config)
            elif command == "getcourseassignments":
                course_id = int(body_json["data"]["options"][0]["value"])
                num_assignments = int(body_json["data"]["options"][1]["value"]) if len(body_json["data"]["options"]) > 1 else 5
                background_tasks.add_task(process_get_course_assignments, interaction_id, interaction_token, course_id, num_assignments, user_config)
            elif command == "getassignments":
                background_tasks.add_task(process_assignments_due_next_week, interaction_id, interaction_token, user_config)

    return {"type": 4, "data": {"content": "Processing your request..."}}

# Helper to send a message to the user
def send_dm_to_user(user_id, content):
    # Step 1: Create a DM channel
    dm_channel_url = "https://discord.com/api/v10/users/@me/channels"
    response = requests.post(dm_channel_url, json={"recipient_id": user_id}, headers=headers)
    channel_data = response.json()
    channel_id = channel_data.get("id")

    # Step 2: Send message in the DM channel
    if channel_id:
        message_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        data = {"content": content}
        requests.post(message_url, json=data, headers=headers)

    return channel_id

# Helper to poll for user response
def poll_for_response(channel_id, user_id):
    message_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    start_time = time.time()
    timeout = 120  # 2 minutes

    while time.time() - start_time < timeout:
        # Fetch the latest messages
        response = requests.get(message_url, headers=headers)
        messages = response.json()

        # Look for a message from the user
        for message in messages:
            if message["author"]["id"] == user_id:
                return message["content"]  # User's response

        # Sleep for a second before polling again
        time.sleep(1)

    return None  # Timeout

# Helper to get user config from DynamoDB
def get_user_config(user_id):
    response = dynamodb_table.get_item(Key={"user": user_id})
    return response.get("Item")

# Process the /setup command
async def process_setup_command(interaction_id: str, interaction_token: str, user_id: str, background_tasks: BackgroundTasks):
    # Send the setup DM to the user
    channel_id = send_dm_to_user(user_id, "Please provide your Canvas API key, URL, and timezone (EST, CST, MST, PST, UTC)")

    # Poll for the response in the background
    background_tasks.add_task(handle_setup_response, channel_id, user_id, interaction_id, interaction_token)

# Handle the user's response and update DynamoDB
def handle_setup_response(channel_id, user_id, interaction_id, interaction_token):
    user_response = poll_for_response(channel_id, user_id)

    if user_response:
        # Parse the user's response (assume format is: API_KEY, URL, TIMEZONE)
        try:
            api_key, url, timezone = user_response.split(",")
            # Validate timezone input
            if timezone.strip().upper() not in ["EST", "CST", "MST", "PST", "UTC"]:
                raise ValueError("Invalid timezone format")

            # Update the user's configuration in DynamoDB
            dynamodb_table.put_item(Item={
                "user": user_id,
                "canvas_api_key": api_key.strip(),
                "canvas_url": url.strip(),
                "timezone": timezone.strip().upper()
            })

            # Send a success message
            send_dm_to_user(user_id, "Successfully updated Canvas API, URL, and timezone!")
        except ValueError:
            send_dm_to_user(user_id, "Invalid response format. Please try again with the format: API_KEY, URL, TIMEZONE.")
    else:
        send_dm_to_user(user_id, "Setup incomplete. Please use /setup again.")

    # Final response to interaction
    response_url = f"https://discord.com/api/v9/webhooks/{APPLICATION_ID}/{interaction_token}"
    requests.post(response_url, json={"content": "Setup process completed."}, headers=headers)

# Process to fetch and send available courses
async def process_show_courses(interaction_id: str, interaction_token: str, user_config):
    canvas_api_key = user_config.get('canvas_api_key')
    canvas_url = user_config.get('canvas_url')
    
    if not canvas_api_key or not canvas_url:
        response_url = f"https://discord.com/api/v9/webhooks/{APPLICATION_ID}/{interaction_token}"
        data = {"content": "Error: Missing Canvas API key or URL. Please complete setup using `/setup`."}
        requests.post(response_url, json=data, headers=headers)
        return
    
    # Initialize Canvas API object
    canvas = Canvas(canvas_url, canvas_api_key)

    courses = canvas.get_courses(enrollment_state="active")
    course_list = "\n".join([f"{course.name} (ID: {course.id})" for course in courses])
    if not course_list:
        course_list = "No active courses found."
    
    response_url = f"https://discord.com/api/v9/webhooks/{APPLICATION_ID}/{interaction_token}"
    data = {"content": f"Available courses:\n{course_list}"}
    requests.post(response_url, json=data, headers=headers)

#Process to fetch and send upcoming assignments for a specific course
async def process_get_course_assignments(interaction_id: str, interaction_token: str, course_id: int, num_assignments: int, user_config):
    canvas_api_key = user_config.get('canvas_api_key')
    canvas_url = user_config.get('canvas_url')
    
    if not canvas_api_key or not canvas_url:
        response_url = f"https://discord.com/api/v9/webhooks/{APPLICATION_ID}/{interaction_token}"
        data = {"content": "Error: Missing Canvas API key or URL. Please complete setup using `/setup`."}
        requests.post(response_url, json=data, headers=headers)
        return
    
    # Initialize Canvas API object
    canvas = Canvas(canvas_url, canvas_api_key)
    
    course = canvas.get_course(course_id)
    assignments = sorted(course.get_assignments(), key=lambda a: a.due_at if a.due_at else "")
    
    current_time = datetime.now(tz=pytz.utc)
    upcoming_assignments = [a for a in assignments if a.due_at and current_time < pytz.utc.localize(datetime.strptime(a.due_at, CANVAS_DATE_FORMAT))]
    
    assignment_list = ""
    for assignment in upcoming_assignments[:num_assignments]:
        due_date = pytz.utc.localize(datetime.strptime(assignment.due_at, CANVAS_DATE_FORMAT))
        assignment_list += f"{assignment.name} - Due: {due_date.strftime(OUTPUT_DATE_FORMAT)}\n"
    
    if not assignment_list:
        assignment_list = "No upcoming assignments."

    response_url = f"https://discord.com/api/v9/webhooks/{APPLICATION_ID}/{interaction_token}"
    data = {"content": f"Upcoming assignments for course {course.name}:\n{assignment_list}"}
    requests.post(response_url, json=data, headers=headers)

# Process to fetch and send assignments due in the next week
async def process_assignments_due_next_week(interaction_id: str, interaction_token: str, user_config):
    canvas_api_key = user_config.get('canvas_api_key')
    canvas_url = user_config.get('canvas_url')
    
    if not canvas_api_key or not canvas_url:
        response_url = f"https://discord.com/api/v9/webhooks/{APPLICATION_ID}/{interaction_token}"
        data = {"content": "Error: Missing Canvas API key or URL. Please complete setup using `/setup`."}
        requests.post(response_url, json=data, headers=headers)
        return
    
    # Initialize Canvas API object
    canvas = Canvas(canvas_url, canvas_api_key)

    courses = canvas.get_courses(enrollment_state="active")
    current_time = datetime.now(tz=pytz.utc)
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
