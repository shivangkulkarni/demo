from typing import Any
import os
from mcp.server.fastmcp import FastMCP
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import ssl
import certifi

load_dotenv()

ssl_context = ssl.create_default_context(cafile=certifi.where())

mcp = FastMCP("demo-mcp-server")


def get_channel_id(client: WebClient, channel: str) -> str:
    """Helper function to get channel ID from name or ID."""
    channels = client.conversations_list(types="public_channel,private_channel")["channels"]
    channel_id = next((c["id"] for c in channels if c["name"] == channel or c["id"] == channel), None)
    return channel_id

@mcp.tool()
def fetch_messages(channel: str, count: int = 10) -> list:
    """Fetch recent Slack messages from a channel."""
    try:
        client = WebClient(token=os.environ["SLACK_BOT_TOKEN"], ssl=ssl_context)
        channel_id = get_channel_id(client, channel)
        if not channel_id:
            return [f"Channel '{channel}' not found"]
        result = client.conversations_history(channel=channel_id, limit=count)
        messages = [msg["text"] for msg in result["messages"] if "text" in msg]
        return messages
    except SlackApiError as e:
        return [f"Slack API Error: {e.response['error']}"]
    except Exception as e:
        return [f"Error: {str(e)}"]

@mcp.tool()
def post_summary(channel: str, summary: str) -> str:
    """Post a summary back to the Slack channel."""
    try:
        client = WebClient(token=os.environ["SLACK_BOT_TOKEN"], ssl=ssl_context)
        channel_id = get_channel_id(client, channel)
        if not channel_id:
            return f"Channel '{channel}' not found"
        client.chat_postMessage(channel=channel_id, text=summary)
        return "Message posted successfully"
    except SlackApiError as e:
        return f"Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def generate_summary(messages: list) -> str:
    """Generate a summary from a list of messages."""
    if not messages:
        return "No messages to summarize."
    return "Summary: " + " ".join(messages)

@mcp.resource("slack://channels")
def list_channels() -> str:
    """List all available Slack channels."""
    try:
        client = WebClient(token=os.environ["SLACK_BOT_TOKEN"], ssl=ssl_context)
        channels = client.conversations_list(types="public_channel,private_channel")["channels"]
        channel_list = [f"#{c['name']} (ID: {c['id']})" for c in channels]
        return "\n".join(channel_list)
    except Exception as e:
        return f"Error fetching channels: {str(e)}"

@mcp.resource("slack://channel/{channel}/info")  
def channel_info(channel: str) -> str:
    """Get information about a specific Slack channel."""
    try:
        client = WebClient(token=os.environ["SLACK_BOT_TOKEN"], ssl=ssl_context)
        channel_id = get_channel_id(client, channel)
        if not channel_id:
            return f"Channel '{channel}' not found"
        
        info = client.conversations_info(channel=channel_id)["channel"]
        return f"Channel: #{info['name']}\nMembers: {info.get('num_members', 'Unknown')}\nTopic: {info.get('topic', {}).get('value', 'No topic')}"
    except Exception as e:
        return f"Error getting channel info: {str(e)}"

@mcp.prompt()
def summarize_and_post(channel: str = "mcp", count: int = 10) -> str:
    """Summarize recent chat messages and post summary back to Slack."""
    messages = fetch_messages(channel, count)
    if not messages or (len(messages) == 1 and "Error" in messages[0]):
        return f"Failed to fetch messages: {messages[0] if messages else 'No messages found'}"
    
    summary = generate_summary(messages)
    result = post_summary(channel, summary)
    return f"Summary generated and posted to #{channel}. Post result: {result}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
