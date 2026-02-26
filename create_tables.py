"""
Script to create all database tables.

This script creates all tables defined in the models.
Run this after starting PostgreSQL with Docker.
"""
import asyncio
from sqlalchemy import text
from app.database import engine
from app.models.base import Base
from app.models.organisation import Organisation
from app.models.user import User
from app.models.credit import OrgCredit, CreditTransaction


async def create_all_tables():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        # Import all models to register them with Base
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully!")


async def drop_all_tables():
    """Drop all tables in the database (for testing)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("All tables dropped!")


async def main():
    """Main entry point."""
    print("Creating database tables...")
    await create_all_tables()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
