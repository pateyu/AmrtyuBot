# AmrtyuBot
## As of September 7, 2024: AmrtyuBot is being updated and new features are being added. The Readme will be updated after all major changes are added.
Study is a Discord study bot designed to assist students with their study schedules, reminders, and other academic tasks. Integrated with Canvas LMS API, it offers updates and reminders for assignments.
## Features 🌟

- **Canvas LMS**: Sync your classes, and get reminders for upcomming assignments.
- **Reminders**: Set reminders for your tasks and exams.


## Commands 🤖
- `/setup`: To setup your Canvas API and URL.
- `/getcourseassignment [course] [number of assignments]`: Get the latest assignments due for a course. 
- `/showcourses`: Show all courses that you are enrolled in.
- `/getAssignments`: to get all assignments due within a week.



## Setup and Installation ⚙️

1. **Clone the Repository**
    ```bash
    git clone [repository link]
    ```

2. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    
    ```

3. **Get Tokens from Canvas and Discord.**
   - Make a .env , and add them inside. It should look like this:
     ```bash
     
      TOKEN=YOUR_DISCORD_TOKEN

      CANVAS_API_KEY=YOUR_CANVAS_API_KEY
    
5. **Run the Bot**
```bash
    python bot.py
    `

