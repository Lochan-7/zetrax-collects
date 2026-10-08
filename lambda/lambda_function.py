import json
import random
import uuid
import boto3
from datetime import datetime, timezone

CARDS = [
    {"name": "Magikarp",             "rarity": "Common",     "hp": 30,  "type": "Water"},
    {"name": "Pidgey",               "rarity": "Common",     "hp": 40,  "type": "Flying"},
    {"name": "Caterpie",             "rarity": "Common",     "hp": 40,  "type": "Bug"},
    {"name": "Rattata",              "rarity": "Common",     "hp": 40,  "type": "Normal"},
    {"name": "Weedle",               "rarity": "Common",     "hp": 40,  "type": "Bug"},
    {"name": "Pikachu",              "rarity": "Uncommon",   "hp": 60,  "type": "Electric"},
    {"name": "Bulbasaur",            "rarity": "Uncommon",   "hp": 70,  "type": "Grass"},
    {"name": "Charmander",           "rarity": "Uncommon",   "hp": 70,  "type": "Fire"},
    {"name": "Squirtle",             "rarity": "Uncommon",   "hp": 70,  "type": "Water"},
    {"name": "Eevee",                "rarity": "Uncommon",   "hp": 60,  "type": "Normal"},
    {"name": "Snorlax",              "rarity": "Rare",       "hp": 160, "type": "Normal"},
    {"name": "Gyarados",             "rarity": "Rare",       "hp": 150, "type": "Water"},
    {"name": "Dragonite",            "rarity": "Rare",       "hp": 150, "type": "Dragon"},
    {"name": "Blastoise",            "rarity": "Rare",       "hp": 140, "type": "Water"},
    {"name": "Venusaur",             "rarity": "Rare",       "hp": 140, "type": "Grass"},
    {"name": "Charizard",            "rarity": "Ultra Rare", "hp": 170, "type": "Fire"},
    {"name": "Mewtwo",               "rarity": "Ultra Rare", "hp": 180, "type": "Psychic"},
    {"name": "Rayquaza",             "rarity": "Ultra Rare", "hp": 180, "type": "Dragon"},
    {"name": "Mew",                  "rarity": "Secret Rare","hp": 200, "type": "Psychic"},
    {"name": "Pikachu Illustrator",  "rarity": "Chase",      "hp": 999, "type": "Electric"},
]

RARITY_WEIGHTS = {"Common": 55, "Uncommon": 25, "Rare": 13, "Ultra Rare": 5, "Secret Rare": 1.5, "Chase": 0.5}
RARITY_ORDER = ["Common", "Uncommon", "Rare", "Ultra Rare", "Secret Rare", "Chase"]
RARE_PLUS_MIN_IDX = RARITY_ORDER.index("Rare")

dynamodb = boto3.client("dynamodb")
TABLE = "zetrax-pack-history"


def draw_one():
    rarities = list(RARITY_WEIGHTS.keys())
    weights = list(RARITY_WEIGHTS.values())
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
    pool = [c for c in CARDS if c["rarity"] == chosen_rarity]
    return random.choice(pool)


def save_pack(pack_id, cards, rarest):
    dynamodb.put_item(
        TableName=TABLE,
        Item={
            "pack_id":   {"S": pack_id},
            "opened_at": {"S": datetime.now(timezone.utc).isoformat()},
            "cards":     {"S": json.dumps(cards)},
            "rarest":    {"S": rarest},
        }
    )


def get_recent_packs(limit=8):
    resp = dynamodb.scan(TableName=TABLE, Limit=100)
    packs = []
    for item in resp.get("Items", []):
        packs.append({
            "pack_id":   item["pack_id"]["S"],
            "opened_at": item["opened_at"]["S"],
            "rarest":    item.get("rarest", {"S": "Common"})["S"],
            "cards":     json.loads(item.get("cards", {"S": "[]"})["S"]),
        })
    packs.sort(key=lambda p: p["opened_at"], reverse=True)
    return packs[:limit]


def get_stats():
    """Scan the whole table to compute aggregate stats."""
    total = 0
    rare_plus = 0
    chases = 0
    paginator = dynamodb.get_paginator("scan")
    for page in paginator.paginate(TableName=TABLE, ProjectionExpression="rarest"):
        for item in page.get("Items", []):
            total += 1
            rarity = item.get("rarest", {"S": "Common"})["S"]
            try:
                idx = RARITY_ORDER.index(rarity)
                if idx >= RARE_PLUS_MIN_IDX:
                    rare_plus += 1
                if rarity == "Chase":
                    chases += 1
            except ValueError:
                pass
    return {
        "total_packs": total,
        "rare_plus": rare_plus,
        "chases": chases,
    }


def response(body):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}
    stats = get_stats()

    if params.get("history") == "1":
        return response({"recent": get_recent_packs(8), "stats": stats})

    pack = [draw_one() for _ in range(5)]
    rarest = max([c["rarity"] for c in pack], key=lambda r: RARITY_ORDER.index(r))
    pack_id = str(uuid.uuid4())[:8]
    save_pack(pack_id, pack, rarest)
    return response({"pack": pack, "recent": get_recent_packs(8), "stats": stats})
