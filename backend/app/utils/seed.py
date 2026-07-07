import asyncio

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models import Category

GLOBAL_CATEGORIES = [
    "Groceries",
    "Rent",
    "Utilities",
    "Transport",
    "Dining",
    "Entertainment",
    "Healthcare",
    "Shopping",
    "Travel",
    "Education",
    "Sports",
]


async def seed_categories() -> None:
    async with async_session_factory() as db:
        for name in GLOBAL_CATEGORIES:
            result = await db.execute(
                select(Category).where(
                    Category.name == name, Category.is_global.is_(True)
                )
            )
            if not result.scalar_one_or_none():
                db.add(Category(name=name, is_global=True))

        await db.commit()
        print(f"Seeded {len(GLOBAL_CATEGORIES)} global categories.")


if __name__ == "__main__":
    asyncio.run(seed_categories())
