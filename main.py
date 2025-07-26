import os
import ssl
import certifi
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

ssl_context = ssl.create_default_context(cafile=certifi.where())
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"], ssl=ssl_context)
print(client.auth_test())
print(client.conversations_list(types="public_channel,private_channel"))