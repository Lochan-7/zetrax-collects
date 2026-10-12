import json
import random
import uuid
import boto3
from datetime import datetime, timezone

MAIN_IMG = "https://dz3we2x72f7ol.cloudfront.net/expansions/30th-celebration/en-us/2M6P_EN_{n}-2x.png"
CLASSIC_IMG = "https://dz3we2x72f7ol.cloudfront.net/expansions/30th-celebration/en-us/2M6P_Classic_EN_{n}-2x.png"

# God pack: 0.1% chance of a jackpot pack with fixed layout
GOD_PACK_RATE = 0.001

# Slot 5: Pikachu subset (always, shiny) - cards 023-052
PIKACHU_RANGE = list(range(23, 53))

# All actual Pokemon ex cards in the main set (from Lochan's gallery check)
POKEMON_EX_NUMBERS = [15, 21, 53, 54, 64, 66, 70, 71, 90, 92, 102, 109]

# Fillers = main set cards EXCLUDING Pikachu subset AND Pokemon ex cards
_PIKACHU_SET = set(PIKACHU_RANGE)
_EX_SET = set(POKEMON_EX_NUMBERS)
FILLER_NUMBERS = [n for n in range(1, 129) if n not in _PIKACHU_SET and n not in _EX_SET]

# Slot 4 hit pool - weights sum to 100
# Shiny flag per category (normal cards are NOT shiny; special categories are)
HIT_POOL = [
    {"category": "Pokemon ex",            "weight": 30, "range": POKEMON_EX_NUMBERS,    "img": MAIN_IMG, "shiny": True},
    {"category": "Normal",                "weight": 48, "range": FILLER_NUMBERS,        "img": MAIN_IMG, "shiny": False},
    {"category": "Illustration Rare",     "weight": 12, "range": list(range(129, 147)), "img": MAIN_IMG, "shiny": True},
    {"category": "Special Illustration",  "weight": 5,  "range": list(range(147, 157)), "img": MAIN_IMG, "shiny": True},
    {"category": "Classic Collection",    "weight": 4,  "range": list(range(1, 31)),    "img": CLASSIC_IMG, "shiny": True},
    {"category": "Futuristic Rare",       "weight": 1,  "range": list(range(157, 159)), "img": MAIN_IMG, "shiny": True},
]

RARITY_ORDER = ["Filler", "Normal", "Pikachu", "Pokemon ex", "Classic Collection",
                "Illustration Rare", "Special Illustration", "Futuristic Rare"]

dynamodb = boto3.client("dynamodb")
TABLE = "zetrax-pack-history"


def draw_filler():
    num = random.choice(FILLER_NUMBERS)
    return {"number": num, "rarity": "Filler", "shiny": False, "image": MAIN_IMG.format(n=num)}


def draw_pikachu():
    num = random.choice(PIKACHU_RANGE)
    return {"number": num, "rarity": "Pikachu", "shiny": True, "image": MAIN_IMG.format(n=num)}


def draw_hit():
    weights = [h["weight"] for h in HIT_POOL]
    chosen = random.choices(HIT_POOL, weights=weights, k=1)[0]
    num = random.choice(chosen["range"])
    return {
        "number": num,
        "rarity": chosen["category"],
        "shiny": chosen["shiny"],
        "image": chosen["img"].format(n=num),
    }


def _pick(cat, rng, img):
    num = random.choice(rng)
    return {"number": num, "rarity": cat, "shiny": True, "image": img.format(n=num)}


def draw_god_pack():
    # Fixed order per spec: 2 Illustration Rare, 1 Special Illustration, 1 Classic, 1 Futuristic
    # Uses sampling without replacement so the two Illustration Rares are distinct
    ill = random.sample(range(129, 147), 2)
    spec = random.choice(range(147, 157))
    classic = random.choice(range(1, 31))
    futuristic = random.choice(range(157, 159))
    def card(cat, num, img):
        return {"number": num, "rarity": cat, "shiny": True, "image": img.format(n=num)}
    return [
        card("Illustration Rare", ill[0], MAIN_IMG),
        card("Illustration Rare", ill[1], MAIN_IMG),
        card("Special Illustration", spec, MAIN_IMG),
        card("Classic Collection", classic, CLASSIC_IMG),
        card("Futuristic Rare", futuristic, MAIN_IMG),
    ]


def _dedup_draw(draw_fn, used_images, tries=60):
    """Call draw_fn until it returns a card whose image isn't already used."""
    for _ in range(tries):
        card = draw_fn()
        if card["image"] not in used_images:
            used_images.add(card["image"])
            return card
    used_images.add(card["image"])
    return card


def draw_pack():
    if random.random() < GOD_PACK_RATE:
        return draw_god_pack(), True
    used = set()
    pack = [_dedup_draw(draw_filler, used) for _ in range(3)]
    pack.append(_dedup_draw(draw_hit, used))
    pack.append(_dedup_draw(draw_pikachu, used))
    return pack, False


def save_pack(pack_id, cards, rarest, god_pack):
    dynamodb.put_item(
        TableName=TABLE,
        Item={
            "pack_id":   {"S": pack_id},
            "opened_at": {"S": datetime.now(timezone.utc).isoformat()},
            "cards":     {"S": json.dumps(cards)},
            "rarest":    {"S": rarest},
            "god_pack":  {"BOOL": god_pack},
        }
    )


def response(body):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    # Debug mode: force god pack with ?god=1 for testing
    params = (event.get("queryStringParameters") or {}) if event else {}
    if params.get("god") == "1":
        pack, is_god = draw_god_pack(), True
    else:
        pack, is_god = draw_pack()

    rarest = max(pack, key=lambda c: RARITY_ORDER.index(c["rarity"]) if c["rarity"] in RARITY_ORDER else 0)["rarity"]
    pack_id = str(uuid.uuid4())[:8]
    try:
        save_pack(pack_id, pack, rarest, is_god)
    except Exception as e:
        print(f"save_pack failed: {e}")
    return response({"pack_id": pack_id, "pack": pack, "rarest": rarest, "god_pack": is_god})
