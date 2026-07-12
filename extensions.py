from flask_sqlalchemy import SQLAlchemy
import redis

db = SQLAlchemy()
redis_client = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)
