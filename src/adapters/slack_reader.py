import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from src.adapters.storage_utils import load_json, save_json

load_dotenv(override=True)

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def _get_thread_permalink(channel_id, thread_ts):
    if not channel_id or not thread_ts:
        return None
    try:
        result = client.chat_getPermalink(channel=channel_id, message_ts=thread_ts)
        return result.get("permalink")
    except SlackApiError as e:
        print(f"Error fetching permalink for {thread_ts}: {e.response['error']}")
        return None

def fetch_slack_threads(channel_id):
    print(f"Fetching threads for channel: {channel_id}...")
    
    sources_state = load_json("sources_state.json")
    last_ts = sources_state.get("slack", {}).get(channel_id, {}).get("last_ts", "0")
    
    all_threads = []
    try:
        # Fetch history
        result = client.conversations_history(
            channel=channel_id,
            oldest=last_ts
        )
        
        messages = result.get("messages", [])
        # Iterate backwards to process oldest first (or just filter correctly)
        for msg in reversed(messages):
            ts = msg.get("ts")
            # If it's a thread starter, fetch replies
            if msg.get("thread_ts") == ts or "reply_count" in msg:
                try:
                    replies = client.conversations_replies(
                        channel=channel_id,
                        ts=ts
                    )
                    all_threads.append({
                        "ts": ts,
                        "channel_id": channel_id,
                        "thread_url": _get_thread_permalink(channel_id, ts),
                        "messages": replies.get("messages", [])
                    })
                except SlackApiError as e:
                    print(f"Error fetching replies for {ts}: {e.response['error']}")
            else:
                # Individual message treated as a single-message thread
                all_threads.append({
                    "ts": ts,
                    "channel_id": channel_id,
                    "thread_url": _get_thread_permalink(channel_id, ts),
                    "messages": [msg]
                })

        if all_threads:
            new_last_ts = max(t["ts"] for t in all_threads)
            if "slack" not in sources_state:
                sources_state["slack"] = {}
            if channel_id not in sources_state["slack"]:
                sources_state["slack"][channel_id] = {}
            sources_state["slack"][channel_id]["last_ts"] = new_last_ts
            save_json("sources_state.json", sources_state)

    except SlackApiError as e:
        print(f"Error fetching history: {e.response['error']}")
    
    return all_threads

def fetch_slack_thread(channel_id, thread_ts):
    print(f"Fetching thread replies for channel: {channel_id}, thread: {thread_ts}...")
    try:
        replies = client.conversations_replies(channel=channel_id, ts=thread_ts)
        return {
            "ts": thread_ts,
            "channel_id": channel_id,
            "thread_url": _get_thread_permalink(channel_id, thread_ts),
            "messages": replies.get("messages", []),
        }
    except SlackApiError as e:
        print(f"Error fetching replies for {thread_ts}: {e.response['error']}")
        return None

def normalize_thread(thread):
    conv_text = ""
    for msg in thread.get("messages", []):
        user = msg.get("user", "System")
        text = msg.get("text", "")
        conv_text += f"{user}: {text}\n"
    return conv_text
