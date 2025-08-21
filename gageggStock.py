import os
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import datetime

# Grow A Garden Stock API
STOCK_API = 'https://vextbzatpprnksyutbcp.supabase.co/rest/v1/growagarden_stock?select=*&active=eq.true&order=created_at.desc'
API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZleHRiemF0cHBybmtzeXV0YmNwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NjYzMTIsImV4cCI6MjA2OTQ0MjMxMn0.apcPdBL5o-t5jK68d9_r9C7m-8H81NQbTXK0EW0o800'

LINE_BROADCAST_URL = 'https://api.line.me/v2/bot/message/broadcast'
LINE_TOKEN_ENV = 'LINE_CHANNEL_ACCESS_TOKEN'


def fetch_stock():
    """Fetch stock data from Grow A Garden API"""
    req = Request(STOCK_API, headers={
        'User-Agent': 'Mozilla/5.0',
        'apikey': API_KEY
    })
    with urlopen(req, timeout=10) as r:
        return json.load(r)


def filter_eggs(data):
    """Return ALL egg stock items (no filtering)."""
    return [item for item in data if item.get('type', '') == 'egg_stock']


def filter_seeds(data):
    """Return ALL seed stock items (no filtering)."""
    return [item for item in data if item.get('type', '') == 'seed_stock']


def organize_eggs(eggs_data):
    """Group eggs by display_name (fallback to item_id) and count all records."""
    grouped = {}
    for egg in eggs_data:
        name = egg.get('display_name') or egg.get('item_id') or 'Unknown Egg'
        item_id = egg.get('item_id', 'unknown')
        if name not in grouped:
            grouped[name] = {
                'count': 0,
                'item_id': item_id,
                'price': egg.get('price', 0),
                'multiplier': egg.get('multiplier', 1),
                'examples': []
            }
        grouped[name]['count'] += 1
        if len(grouped[name]['examples']) < 3:
            grouped[name]['examples'].append({
                'created_at': egg.get('created_at'),
                'date': egg.get('date')
            })
    return grouped


def organize_seeds(seeds_data):
    """Group seeds by display_name (fallback to item_id) and count all records."""
    grouped = {}
    for seed in seeds_data:
        name = seed.get('display_name') or seed.get('item_id') or 'Unknown Seed'
        item_id = seed.get('item_id', 'unknown')
        if name not in grouped:
            grouped[name] = {
                'count': 0,
                'item_id': item_id,
                'price': seed.get('price', 0),
                'multiplier': seed.get('multiplier', 1),
                'examples': []
            }
        grouped[name]['count'] += 1
        if len(grouped[name]['examples']) < 3:
            grouped[name]['examples'].append({
                'created_at': seed.get('created_at'),
                'date': seed.get('date')
            })
    return grouped


def has_bug_egg(eggs_grouped):
    """Detect if any grouped egg looks like 'bug egg' (case-insensitive)."""
    for egg_name, info in eggs_grouped.items():
        name_l = (egg_name or '').lower()
        item_id_l = (info.get('item_id') or '').lower()
        if 'bug egg' in name_l or 'bug_egg' in item_id_l or ('bug' in name_l and 'egg' in name_l):
            return True
    return False


def has_common_egg(eggs_grouped):
    """Detect if any grouped egg looks like 'common egg' (case-insensitive)."""
    for egg_name, info in eggs_grouped.items():
        name_l = (egg_name or '').lower()
        item_id_l = (info.get('item_id') or '').lower()
        if 'common egg' in name_l or 'common_egg' in item_id_l or ('common' in name_l and 'egg' in name_l):
            return True
    return False


def send_line_broadcast(message: str):
    token = os.environ.get(LINE_TOKEN_ENV, '').strip()
    if not token:
        print(f"⚠️ Skipped LINE broadcast: missing env {LINE_TOKEN_ENV}")
        return
    body = json.dumps({
        'messages': [
            {'type': 'text', 'text': message}
        ]
    }).encode('utf-8')
    req = Request(LINE_BROADCAST_URL, data=body, method='POST', headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    })
    try:
        with urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                print(f"⚠️ LINE broadcast HTTP {resp.status}")
    except (HTTPError, URLError) as e:
        print(f"⚠️ LINE broadcast failed: {e}")


def build_banner(message: str) -> str:
    width = 60
    top = "#" * width
    empty = "#" + " " * (width - 2) + "#"
    mid = "#" + message.center(width - 2) + "#"
    return "\n" + "\n".join([top, empty, mid, empty, top]) + "\n"


def print_banner(message):
    print(build_banner(message))


def display_seed_summary(seeds_data):
    print("🌱 SEED SHOP 🌱")
    print("-" * 50)
    if not seeds_data:
        print("❌ No seeds currently in stock!")
        return
    total_seeds = 0
    for seed_name, info in seeds_data.items():
        count = info['count']
        price = info['price']
        multiplier = info['multiplier']
        print(f"📦 {seed_name}")
        print(f"   Quantity: {count}")
        print(f"   Price: {price}")
        print(f"   Multiplier: {multiplier}x")
        print(f"   ID: {info['item_id']}")
        if info['examples']:
            newest = next(
                (e for e in sorted(info['examples'], key=lambda x: (x.get('created_at') or ''), reverse=True)),
                info['examples'][0])
            print(f"   Latest: {newest.get('created_at') or newest.get('date')}")
        print()
        total_seeds += count
    print(f"📊 TOTAL SEEDS IN STOCK: {total_seeds}")
    print()


def display_egg_summary(eggs_data):
    """Display organized egg data"""
    print("🥚 GROW A GARDEN EGG STOCK 🥚")
    print("=" * 50)
    print(f"📅 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    if not eggs_data:
        print("❌ No eggs currently in stock!")
        return

    # Attention banners (console + LINE)
    if has_bug_egg(eggs_data):
        banner_text = build_banner("BUG EGG!!!")
        print(banner_text)
        send_line_broadcast(banner_text)

    # Messaging API notification for common egg
    if has_common_egg(eggs_data):
        send_line_broadcast("COMMON EGG IN STOCK!!!")

    total_eggs = 0
    print("\n🥚 EGG STOCK")
    print("-" * 30)

    for egg_name, info in eggs_data.items():
        count = info['count']
        price = info['price']
        multiplier = info['multiplier']
        print(f"📦 {egg_name}")
        print(f"   Quantity: {count}")
        print(f"   Price: {price}")
        print(f"   Multiplier: {multiplier}x")
        print(f"   ID: {info['item_id']}")
        if info['examples']:
            newest = next(
                (e for e in sorted(info['examples'], key=lambda x: (x.get('created_at') or ''), reverse=True)),
                info['examples'][0])
            print(f"   Latest: {newest.get('created_at') or newest.get('date')}")
        print()
        total_eggs += count

    print("=" * 50)
    print(f"📊 TOTAL EGGS IN STOCK: {total_eggs}")
    print(f"📋 EGG TYPES AVAILABLE: {len(eggs_data)}")
    print("=" * 50)
    print("💡 Data source: [Gamersberg Grow A Garden Stock](https://www.gamersberg.com/grow-a-garden/stock)")


if __name__ == '__main__':
    try:
        data = fetch_stock()
        # Seeds
        seeds_only = filter_seeds(data)
        seeds_data = organize_seeds(seeds_only)
        display_seed_summary(seeds_data)
        # Eggs
        eggs_only = filter_eggs(data)
        eggs_data = organize_eggs(eggs_only)
        display_egg_summary(eggs_data)
    except Exception as e:
        print(f"❌ Error fetching stock data: {e}")
        print("💡 Check your internet connection or try again later.")