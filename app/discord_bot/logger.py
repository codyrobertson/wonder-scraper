"""
Discord webhook logger for scrape activity and system events.
"""
import os
import requests
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()


LOGS_WEBHOOK_URL = os.getenv("DISCORD_LOGS_WEBHOOK_URL")


def _send_log(
    title: str,
    description: str,
    color: int,
    fields: list = None
) -> bool:
    """Send a log message to Discord webhook."""
    if not LOGS_WEBHOOK_URL:
        return False

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Wonders Scraper"}
    }

    if fields:
        embed["fields"] = fields

    try:
        response = requests.post(
            LOGS_WEBHOOK_URL,
            json={
                "username": "Wonders Logs",
                "embeds": [embed]
            },
            timeout=5
        )
        return response.status_code in (200, 204)
    except Exception as e:
        print(f"Discord log failed: {e}")
        return False


def log_scrape_start(card_count: int, scrape_type: str = "full") -> bool:
    """Log when a scrape job starts."""
    return _send_log(
        title="Scrape Started",
        description=f"Starting **{scrape_type}** scrape job",
        color=0x3B82F6,  # Blue
        fields=[
            {"name": "Cards", "value": str(card_count), "inline": True},
            {"name": "Type", "value": scrape_type.title(), "inline": True},
            {"name": "Time", "value": datetime.utcnow().strftime("%H:%M UTC"), "inline": True}
        ]
    )


def log_scrape_complete(
    cards_processed: int,
    new_listings: int,
    new_sales: int,
    duration_seconds: float,
    errors: int = 0
) -> bool:
    """Log when a scrape job completes."""
    status = "with errors" if errors > 0 else "successfully"
    color = 0xF59E0B if errors > 0 else 0x10B981  # Yellow if errors, green otherwise

    minutes = int(duration_seconds // 60)
    seconds = int(duration_seconds % 60)
    duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    return _send_log(
        title=f"Scrape Complete",
        description=f"Scrape finished {status}",
        color=color,
        fields=[
            {"name": "Cards Processed", "value": str(cards_processed), "inline": True},
            {"name": "New Listings", "value": str(new_listings), "inline": True},
            {"name": "New Sales", "value": str(new_sales), "inline": True},
            {"name": "Duration", "value": duration_str, "inline": True},
            {"name": "Errors", "value": str(errors), "inline": True}
        ]
    )


def log_scrape_error(card_name: str, error: str) -> bool:
    """Log a scrape error for a specific card."""
    return _send_log(
        title="Scrape Error",
        description=f"Error scraping **{card_name}**",
        color=0xEF4444,  # Red
        fields=[
            {"name": "Error", "value": error[:1000], "inline": False}
        ]
    )


def log_snapshot_update(cards_updated: int) -> bool:
    """Log when market snapshots are updated."""
    return _send_log(
        title="Snapshots Updated",
        description=f"Updated market snapshots for **{cards_updated}** cards",
        color=0x8B5CF6,  # Purple
        fields=[
            {"name": "Cards", "value": str(cards_updated), "inline": True},
            {"name": "Time", "value": datetime.utcnow().strftime("%H:%M UTC"), "inline": True}
        ]
    )


def log_info(title: str, message: str) -> bool:
    """Log a general info message."""
    return _send_log(
        title=title,
        description=message,
        color=0x6B7280  # Gray
    )


def log_warning(title: str, message: str) -> bool:
    """Log a warning message."""
    return _send_log(
        title=f"Warning: {title}",
        description=message,
        color=0xF59E0B  # Yellow
    )


def log_error(title: str, message: str) -> bool:
    """Log an error message."""
    return _send_log(
        title=f"Error: {title}",
        description=message,
        color=0xEF4444  # Red
    )
