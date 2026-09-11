"""
Checks Too Good To Go for available "surprise bags" at a specific store
(default: Fob Sushi, Bellevue) and pushes a phone notification via ntfy.sh
the moment bags become available.

Meant to be run on a schedule (e.g. every 5 minutes via GitHub Actions,
cron, or Task Scheduler) -- see README.md.

Required environment variables:
    TGTG_ACCESS_TOKEN
    TGTG_REFRESH_TOKEN
    TGTG_COOKIE
    NTFY_TOPIC        e.g. "pramil-tgtg-8f3k2" (pick something unique/hard to guess)

Optional:
    STORE_SEARCH      free-text filter, default "Fob Sushi"
    LATITUDE          default 47.6152 (Fob Sushi Bar, 333 108th Ave NE, Bellevue WA)
    LONGITUDE         default -122.1932
    RADIUS_KM         default 2 (keeps results limited to that Bellevue location,
                       not the separate Seattle/Belltown Fob Sushi store)
"""

import os
import sys
import time
import datetime
import requests
from typing import Optional
from tgtg import TgtgClient

STORE_SEARCH = os.environ.get("STORE_SEARCH", "Fob Sushi")
LATITUDE = float(os.environ.get("LATITUDE", "47.6152"))
LONGITUDE = float(os.environ.get("LONGITUDE", "-122.1932"))
RADIUS_KM = int(os.environ.get("RADIUS_KM", "2"))
NTFY_TOPIC = os.environ["NTFY_TOPIC"]
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "20"))   # seconds between checks
RUN_SECONDS = int(os.environ.get("RUN_SECONDS", "280"))       # how long to keep looping this run


def notify(title: str, message: str, click_url: Optional[str] = None):
    headers = {
        "Title": title.encode("utf-8"),
        "Priority": "urgent",
        "Tags": "sushi,bell",
    }
    if click_url:
        headers["Click"] = click_url  # tapping the notification opens this
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers=headers,
        timeout=15,
    )


def check_once(client, already_notified: set) -> set:
    """Runs one check; returns updated set of store names currently notified-on."""
    try:
        items = client.get_items(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            radius=RADIUS_KM,
            favorites_only=False,
            discover=True,
            search_phrase=STORE_SEARCH,
            with_stock_only=False,
        )
    except Exception as e:
        print(f"Error querying TGTG: {e}", file=sys.stderr)
        return already_notified

    if not items:
        print(f"No store found matching '{STORE_SEARCH}' near ({LATITUDE}, {LONGITUDE}).")
        return already_notified

    still_available = set()
    for item in items:
        store_name = item.get("store", {}).get("store_name", "Unknown store")
        if "bellevue" not in store_name.lower():
            continue  # extra safety net: skip any other Fob Sushi location the radius picked up
        available = item.get("items_available", 0)
        item_id = item.get("item", {}).get("item_id")
        share_url = f"https://share.toogoodtogo.com/item/{item_id}/" if item_id else None
        price = item.get("item", {}).get("price_including_taxes", {})
        price_str = (
            f"${price.get('minor_units', 0) / (10 ** price.get('decimals', 2)):.2f}"
            if price
            else "?"
        )
        print(f"[{time.strftime('%H:%M:%S')}] {store_name}: {available} bag(s) available")

        if available > 0:
            still_available.add(store_name)
            if store_name not in already_notified:
                notify(
                    title=f"🍣 {store_name}: {available} bag(s) available!",
                    message=f"Price {price_str} — tap to open in the TGTG app and reserve.",
                    click_url=share_url,
                )

    return still_available


def main():
    client = TgtgClient(
        access_token=os.environ["TGTG_ACCESS_TOKEN"],
        refresh_token=os.environ["TGTG_REFRESH_TOKEN"],
        cookie=os.environ["TGTG_COOKIE"],
        # Treat the token as freshly refreshed so the library trusts it for its
        # full lifetime instead of hitting the refresh endpoint on every run --
        # that endpoint is the one most likely to trip TGTG's anti-bot captcha.
        last_time_token_refreshed=datetime.datetime.now(),
    )

    deadline = time.time() + RUN_SECONDS
    already_notified = set()  # store names we've already pinged about this run

    while True:
        already_notified = check_once(client, already_notified)
        if time.time() >= deadline:
            break
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
