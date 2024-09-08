# AmrtyuBot
## As of September 7, 2024: AmrtyuBot is being updated and new features will be added. Firstly, it will now use the Wolfram Alpha API, and it will also be hosted on AWS Lambda. More chnages can be expected.
AmrtyuBot is a Discord study bot designed to assist students with their study schedules, reminders, and other academic tasks. Integrated with Canvas LMS API, it offers updates and reminders for assignments.
## Features 🌟

- **Task Management**: Add, remove, and view tasks easily.
- **Canvas LMS**: Sync your classes, and get reminders for upcomming assignments.
- **Reminders**: Set reminders for your tasks and exams.
- **Study Sessions** Use a built-in pomodoro timer and other study session tools to keep track of your productivity all from one place.

## Commands 🤖

- `!addTask [task]`: Add a new task.
- `!removeTask [task number]`: Remove a task by its number.
- `!showTasks`: Show all tasks.
- `!getAssignments`: to get all assignments due within 24 hours
- `!pomodoro`: to set a 25-5 timer. The times are customizable, and there is an option to control the amount of times the timer repeats.
- Check out the cogs for all the other commands

## Setup and Installation ⚙️

1. **Clone the Repository**
    ```bash
    git clone [Your Repository Link]
    ```

2. **Install Dependencies**
    ```bash
    pip install canvasapi
    pip install -U discord.py
    ```

3. **Get Tokens from Canvas and Discord, as well as the Channel ID**
   - Make a config.json, and add them inside. It should look like this:
     ```bash
     {
      "TOKEN": "YOUR_DISCORD_TOKEN",

      "CANVAS_API_KEY": "YOUR_CANVAS_API_KEY",

      "CHANNEL_ID": "YOUR_CHANNEL ID"
     }
 ```
5. **Run the Bot**
    ```bash
    python bot.py
    `
