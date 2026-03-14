import os
import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
from zoneinfo import ZoneInfo
import os

"""
Logger Service

When calling logger functions (debug_log, info_log, warning_log, error_log, critical_log)
from outside this module, pass the following keyword arguments:

Required parameters:
    path (str): File name where the log came from
    function (str): Function name where log is called from

Optional parameters:
    class_ (str): Class name if the log is called from inside a class
    error (str): Error message/details if it's an error log
    message (str): Message if it's not an error log

Example usage:
    from logger_service import error_log
    
    error_log(
        path="auth_service.py",
        function="login_user",
        class_="AuthService",
        error="Invalid credentials"
    )
    
    from logger_service import info_log
    
    info_log(
        path="user_service.py",
        function="create_user",
        message="User created successfully"
    )
"""

# Explicitly load .env from the project root (handles running from any directory)
load_dotenv()

DEVELOPMENT = os.environ.get('ENVIRONMENT', 'development') != "production"

LEVEL_EMOJIS = {
    'debug': '⚪',
    'info': '🔵',
    'warning': '🟠',
    'error': '🔴',
    'critical': ':rotating_light:',
}

SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', '#general-urgent-alerts')

def get_channel_id(channel_name: str, client: WebClient):
    """Return the channel ID for a given channel name (e.g., 'alerts')"""
    try:
        response = client.conversations_list(types="public_channel,private_channel")
        for channel in response["channels"]:
            if channel["name"] == channel_name.lstrip("#"):
                return channel["id"]
        print(f"[WARN] Channel '{channel_name}' not found in list.")
    except SlackApiError as e:
        print(f"[ERROR] Failed to fetch channels: {e.response['error']}")
    return None

def _send_slack(level, **kwargs):
    emoji = LEVEL_EMOJIS.get(level.lower(), '🔵')
    timestamp = datetime.now(ZoneInfo("Europe/Tirane")).strftime("%d-%m-%Y - %H:%M:%S")
    fields = "\n".join(f"*{k}*: `{v}`" for k, v in kwargs.items())
    msg = (
        f"{emoji} *{level.upper()} Alert*\n"
        f"{fields}\n"
        f"\n{timestamp}\n"
    )

    if DEVELOPMENT == "1":
        print(msg)
        return

    if not SLACK_TOKEN or not SLACK_CHANNEL:
        print("[WARN] Slack token or channel not set. Skipping Slack notification.")
        return

    client = WebClient(token=SLACK_TOKEN)

    try:
        client.chat_postMessage(channel=SLACK_CHANNEL, text=msg)
    except SlackApiError as e:
        print(f"[ERROR] Failed to send Slack message: {e.response['error']}")

def console_log(level='info', send_to_slack=True, **kwargs):
    message = {key: value for key, value in kwargs.items()}
    print(f"[{level.upper()}] {message}")
    if DEVELOPMENT == "1" or send_to_slack == False:
        print(message)
    else:
        if send_to_slack:
            _send_slack(level, **kwargs)
    

def debug_log(send_to_slack=True, **kwargs):
    console_log(**kwargs, level='debug', send_to_slack=send_to_slack)

def info_log(send_to_slack=True, **kwargs):
    console_log(**kwargs, level='info', send_to_slack=send_to_slack)

def warning_log(send_to_slack=True, **kwargs):
    console_log(**kwargs, level='warning', send_to_slack=send_to_slack)

def error_log(send_to_slack=True, **kwargs):
    console_log(**kwargs, level='error', send_to_slack=send_to_slack)

def critical_log(send_to_slack=True, **kwargs):
    console_log(**kwargs, level='critical', send_to_slack=send_to_slack)

def to_json(data: dict, file_path: str) -> None:
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def read_json(file_path: str) -> dict:
    with open(file_path, 'r') as f:
        return json.load(f)
