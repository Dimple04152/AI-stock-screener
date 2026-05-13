import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create a connection pool or simple client
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None

def get_cache(key: str):
    if not redis_client: return None
    try:
        val = redis_client.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None

def set_cache(key: str, value: dict, ttl: int = 300):
    if not redis_client: return
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception:
        pass
