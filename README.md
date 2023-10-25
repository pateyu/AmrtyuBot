# AmrtyuBot

AtudyBot is a Discord bot designed to assist students with their study schedules, reminders, and other academic tasks. Integrated with Canvas LMS API, it offers updates and reminders for assignments.
## Features 🌟

- **Task Management**: Add, remove, and view tasks easily.
- **Canvas LMS**: Sync your classes, and get reminders for upcomming assignments.
- **Reminders**: Set reminders for your tasks and exams.
- **Study Sessions** Use a built-in pomodoro timer and other study session tools to keep track of your productivity all from one place.
- [Add more features as necessary]

## Commands 🤖

- `!addTask [task]`: Add a new task.
- `!removeTask [task number]`: Remove a task by its number.
- `!showTasks`: Show all tasks.
- `!getAssignments`: to get all assignments due within 24 hours
- `!pomodoro`: to set a 25-5 timer. The times are customizable, and there is an option to control the amount of times the timer repeats.

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

3. ** Get Tokens from Canvas and Discord, as well as the Channel ID **
   Make a config.json, and add them inside.
5. **Run the Bot**
    ```bash
    python bot.py
    `
