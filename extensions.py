from flask_sqlalchemy import SQLAlchemy
import redis
from redis.retry import Retry
from redis.backoff import NoBackoff

db = SQLAlchemy()
redis_client = redis.Redis(
    host="localhost", port=6379, db=1, decode_responses=True,
    socket_connect_timeout=1, socket_timeout=1,
    retry=Retry(NoBackoff(), retries=0)
)
