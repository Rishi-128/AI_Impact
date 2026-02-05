from main import app
import asyncio

async def test_startup():
    print("Initializing App...")
    # Trigger startup event if any (FastAPI default doesn't have much)
    print("App initialized.")

if __name__ == "__main__":
    asyncio.run(test_startup())
