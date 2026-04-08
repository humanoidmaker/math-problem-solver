from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DB_NAME]
    await db.users.create_index("email", unique=True)
    await db.problems.create_index("user_id")
    await db.problems.create_index("created_at")


async def close_db():
    global client
    if client:
        client.close()


def get_db():
    return db
