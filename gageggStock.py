import json
from urllib.request import urlopen, Request

API = 'https://vextbzatpprnksyutbcp.supabase.co/rest/v1/growagarden_stock?select=*&type=eq.egg_stock&active=eq.true&order=created_at.desc'

def fetch():
    req = Request(API, headers={'User-Agent': 'Mozilla/5.0','apikey':'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZleHRiemF0cHBybmtzeXV0YmNwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NjYzMTIsImV4cCI6MjA2OTQ0MjMxMn0.apcPdBL5o-t5jK68d9_r9C7m-8H81NQbTXK0EW0o800'})
    with urlopen(req, timeout=8) as r:
        respon = json.load(r)
        return respon

def organize_eggs(data):
    """Organize egg stock data by type"""
    egg_types = {}
    
    for item in data:
        egg_name = item.get('display_name', 'Unknown Egg')
        item_id = item.get('item_id', 'unknown')
        
        if egg_name not in egg_types:
            egg_types[egg_name] = {
                'count': 0,
                'item_id': item_id,
                'price': item.get('price', 0),
                'multiplier': item.get('multiplier', 1)
            }
        egg_types[egg_name]['count'] += 1
    
    return egg_types

def display_stock(egg_types):
    """Display organized egg stock"""
    print("🥚 EGG STOCK STATUS 🥚")
    print("=" * 40)
    
    if not egg_types:
        print("No eggs currently in stock!")
        return
    
    for egg_name, info in egg_types.items():
        count = info['count']
        price = info['price']
        multiplier = info['multiplier']
        
        print(f"📦 {egg_name}")
        print(f"   Quantity: {count}")
        print(f"   Price: {price}")
        print(f"   Multiplier: {multiplier}x")
        print(f"   ID: {info['item_id']}")
        print("-" * 30)
    
    # Summary
    total_eggs = sum(info['count'] for info in egg_types.values())
    print(f"\n📊 TOTAL EGGS IN STOCK: {total_eggs}")
    print(f"📋 EGG TYPES AVAILABLE: {len(egg_types)}")

if __name__ == '__main__':
    data = fetch()
    egg_types = organize_eggs(data)
    display_stock(egg_types)