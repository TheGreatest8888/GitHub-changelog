#!/usr/bin/env python3
import os
import requests
import feedparser
import re
import time

# Use environment variables for secrets
WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN", "")
WEBEX_ROOM_ID = os.getenv("WEBEX_ROOM_ID", "")

# The official feed URL for GitHub Changelog
RSS_FEED_URL = "https://github.blog/changelog/feed/"

# Time window (in seconds); if the item is older than this, skip it.
# Example: 3600 seconds = 1 hour
TIME_WINDOW_SECONDS = 3600

def send_message_to_webex(title: str, markdown_msg: str) -> bool:
    """
    Sends a Markdown-formatted message to a Webex room using
    the Webex Bot token. Returns True if successful, False otherwise.
    """
    url = "https://webexapis.com/v1/messages"
    headers = {
        "Authorization": f"Bearer {WEBEX_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "roomId": WEBEX_ROOM_ID,
        "markdown": markdown_msg
    }

    try:
        resp = requests.post(url, json=data, headers=headers)
        resp.raise_for_status()
        print(f"[INFO] Posted: {title}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Could not post {title} - {e}")
        return False

def parse_feed_and_post():
    """
    Parse the RSS feed, check each entry's publish time, and post if it's within our time window.
    """
    feed = feedparser.parse(RSS_FEED_URL)
    current_time = time.time()

    for entry in feed.entries:
        # If there's no parsed publish time, skip
        if not hasattr(entry, "published_parsed") or not entry.published_parsed:
            continue

        published_ts = time.mktime(entry.published_parsed)
        age_in_seconds = current_time - published_ts

        # Skip if older than TIME_WINDOW_SECONDS
        if age_in_seconds > TIME_WINDOW_SECONDS:
            continue

        # Clean HTML from the content if it exists
        content_html = ""
        if hasattr(entry, "content") and entry.content:
            content_html = entry.content[0].value or ""
            # Remove <a class="heading-link"> elements
            content_html = re.sub(r'<a[^>]*class=["\']heading-link[^>]*>.*?</a>', '', content_html)
            # Convert HTML entities
            content_html = (content_html
                            .replace("&lt;", "<")
                            .replace("&gt;", ">")
                            .replace("&apos;", "'")
                            .replace("&quot;", '"'))

        # Construct the message in Markdown
        message = (
            f"# [{entry.title}]({entry.link})\n\n"
            f"#### **Details:**\n\n"
            f"{content_html}\n\n"
        )

        # Send to Webex
        send_message_to_webex(entry.title, message)

if __name__ == "__main__":
    parse_feed_and_post()
