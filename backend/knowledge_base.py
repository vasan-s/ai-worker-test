"""Hardcoded knowledge base for places and weather forecasts."""

from datetime import date, timedelta
import random

PLACES = {
    "tokyo": {
        "city": "Tokyo",
        "country": "Japan",
        "currency": "JPY",
        "language": "Japanese",
        "best_season": "March-May (cherry blossoms), Oct-Nov (autumn)",
        "attractions": [
            "Shibuya Crossing",
            "Senso-ji Temple",
            "Tokyo Skytree",
            "Meiji Shrine",
            "Tsukiji Outer Market",
        ],
        "avg_hotel_price_usd": 180,
        "timezone": "JST (UTC+9)",
        "summary": "A dense, futuristic metropolis blending neon-lit skyscrapers with centuries-old temples.",
    },
    "paris": {
        "city": "Paris",
        "country": "France",
        "currency": "EUR",
        "language": "French",
        "best_season": "April-June, September-October",
        "attractions": [
            "Eiffel Tower",
            "Louvre Museum",
            "Notre-Dame Cathedral",
            "Montmartre",
            "Seine River cruises",
        ],
        "avg_hotel_price_usd": 220,
        "timezone": "CET (UTC+1)",
        "summary": "The City of Light, famed for art, cuisine, fashion, and iconic boulevards.",
    },
    "bali": {
        "city": "Bali",
        "country": "Indonesia",
        "currency": "IDR",
        "language": "Indonesian, Balinese",
        "best_season": "April-October (dry season)",
        "attractions": [
            "Uluwatu Temple",
            "Ubud rice terraces",
            "Tanah Lot",
            "Seminyak Beach",
            "Mount Batur sunrise hike",
        ],
        "avg_hotel_price_usd": 90,
        "timezone": "WITA (UTC+8)",
        "summary": "A tropical Indonesian island known for volcanic mountains, beaches, and Hindu temples.",
    },
    "new york": {
        "city": "New York",
        "country": "USA",
        "currency": "USD",
        "language": "English",
        "best_season": "April-June, September-November",
        "attractions": [
            "Statue of Liberty",
            "Central Park",
            "Times Square",
            "Metropolitan Museum of Art",
            "Brooklyn Bridge",
        ],
        "avg_hotel_price_usd": 290,
        "timezone": "EST (UTC-5)",
        "summary": "The city that never sleeps, a global hub for finance, culture, and entertainment.",
    },
    "dubai": {
        "city": "Dubai",
        "country": "UAE",
        "currency": "AED",
        "language": "Arabic, English",
        "best_season": "November-March",
        "attractions": [
            "Burj Khalifa",
            "Palm Jumeirah",
            "Dubai Mall",
            "Desert Safari",
            "Dubai Marina",
        ],
        "avg_hotel_price_usd": 200,
        "timezone": "GST (UTC+4)",
        "summary": "A glittering desert metropolis of skyscrapers, luxury shopping, and ultramodern architecture.",
    },
    "reykjavik": {
        "city": "Reykjavik",
        "country": "Iceland",
        "currency": "ISK",
        "language": "Icelandic",
        "best_season": "June-August (midnight sun), Sept-March (northern lights)",
        "attractions": [
            "Blue Lagoon",
            "Golden Circle",
            "Hallgrimskirkja",
            "Whale watching",
            "Northern Lights tours",
        ],
        "avg_hotel_price_usd": 250,
        "timezone": "GMT (UTC+0)",
        "summary": "Iceland's compact, colorful capital — a launching point for glaciers, geysers, and aurora.",
    },
}


# Per-city seasonal weather profile (avg high/low in celsius) by month index 1-12
_WEATHER_PROFILES = {
    "tokyo": {1: (10, 2), 2: (11, 3), 3: (14, 6), 4: (19, 11), 5: (23, 16), 6: (26, 20),
              7: (30, 24), 8: (31, 25), 9: (27, 21), 10: (22, 16), 11: (17, 9), 12: (12, 4)},
    "paris": {1: (7, 3), 2: (8, 3), 3: (12, 5), 4: (16, 7), 5: (20, 11), 6: (23, 13),
              7: (25, 15), 8: (25, 15), 9: (21, 12), 10: (16, 9), 11: (10, 5), 12: (7, 3)},
    "bali":  {1: (30, 24), 2: (30, 24), 3: (31, 24), 4: (31, 24), 5: (31, 24), 6: (30, 23),
              7: (29, 23), 8: (29, 22), 9: (30, 22), 10: (31, 23), 11: (31, 23), 12: (30, 24)},
    "new york": {1: (4, -3), 2: (6, -1), 3: (10, 2), 4: (16, 7), 5: (22, 13), 6: (27, 18),
                 7: (29, 21), 8: (28, 20), 9: (24, 16), 10: (18, 10), 11: (12, 5), 12: (6, 0)},
    "dubai": {1: (24, 14), 2: (26, 16), 3: (29, 18), 4: (34, 21), 5: (39, 26), 6: (41, 28),
              7: (42, 31), 8: (42, 31), 9: (40, 28), 10: (36, 24), 11: (30, 19), 12: (26, 15)},
    "reykjavik": {1: (3, -2), 2: (3, -2), 3: (4, -2), 4: (6, 1), 5: (10, 4), 6: (13, 7),
                  7: (14, 9), 8: (14, 8), 9: (11, 6), 10: (7, 3), 11: (4, 0), 12: (3, -1)},
}

_CONDITIONS_BY_TEMP = [
    (-10, "Snowy and frigid"),
    (5, "Cold and overcast"),
    (15, "Cool and partly cloudy"),
    (22, "Mild and pleasant"),
    (28, "Warm and sunny"),
    (100, "Hot and sunny"),
]


def list_place_keys() -> list[str]:
    return sorted(PLACES.keys())


def get_place(city: str) -> dict | None:
    return PLACES.get(city.strip().lower())


def _condition_for(temp_high: int) -> str:
    for cap, label in _CONDITIONS_BY_TEMP:
        if temp_high <= cap:
            return label
    return "Sunny"


def get_forecast(city: str, travel_date: str) -> dict | None:
    """Return a deterministic-ish forecast for the given city and ISO date string."""
    key = city.strip().lower()
    profile = _WEATHER_PROFILES.get(key)
    if profile is None:
        return None
    try:
        d = date.fromisoformat(travel_date)
    except ValueError:
        return None
    high, low = profile[d.month]
    # tiny daily variation seeded by date for repeatability
    rng = random.Random(f"{key}-{travel_date}")
    high_jitter = rng.randint(-2, 2)
    low_jitter = rng.randint(-2, 2)
    temp_high = high + high_jitter
    temp_low = low + low_jitter
    precip_chance = rng.randint(5, 60)
    return {
        "city": PLACES[key]["city"],
        "date": travel_date,
        "temp_high_c": temp_high,
        "temp_low_c": temp_low,
        "condition": _condition_for(temp_high),
        "precipitation_chance_pct": precip_chance,
        "recommendation": (
            "Pack layers and a waterproof jacket." if precip_chance > 40
            else "Light clothing should be fine, sunscreen recommended."
            if temp_high >= 25
            else "Comfortable clothing recommended."
        ),
    }
