from discord.ext import commands
import json

# Load the configuration file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Access the token
discord_token = config['TOKEN']
CHANNEL_ID = 1154552490361102426