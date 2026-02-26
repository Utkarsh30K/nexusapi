"""
Multi-tenancy verification script.

This script demonstrates that data isolation works correctly between organisations.
It creates two organisations with users and verifies that queries for one organisation
do not return data from another organisation.

Run this script after setting up the database to verify the demo gate:
"Four tables exist with correct relationships. A script creates two organisations 
and two users in different orgs. A query for org 1's users cannot return org 2's users."
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.organisation import Organisation
from app.models.user import User, UserRole
from app.models.credit import OrgCredit


async def setup_test_data():
    """
    Create two organisations and two users in different orgs.
    
    Returns:
        tuple: (org1_id, org2_id)
    """
    async with AsyncSessionLocal() as session:
        # Organisation 1 - Acme Corp
        org1 = Organisation(name="Acme Corp", domain="acme.com")
        session.add(org1)
        await session.flush()

        # User 1 belongs to Org 1
        user1 = User(
            email="john@acme.com",
            name="John Doe",
            organisation_id=org1.id,
            role=UserRole.ADMIN
        )
        session.add(user1)

        # Credits for Org 1
        credit1 = OrgCredit(organisation_id=org1.id, balance=1000)
        session.add(credit1)

        # Organisation 2 - Beta Inc
        org2 = Organisation(name="Beta Inc", domain="beta.com")
        session.add(org2)
        await session.flush()

        # User 2 belongs to Org 2
        user2 = User(
            email="jane@beta.com",
            name="Jane Smith",
            organisation_id=org2.id,
            role=UserRole.ADMIN
        )
        session.add(user2)

        # Credits for Org 2
        credit2 = OrgCredit(organisation_id=org2.id, balance=500)
        session.add(credit2)

        await session.commit()

        print(f"Created Organisation 1: {org1.name} (domain: {org1.domain})")
        print(f"Created User 1: {user1.email} (org_id: {user1.organisation_id})")
        print(f"Created OrgCredit for Org 1: balance={credit1.balance}")
        print()
        print(f"Created Organisation 2: {org2.name} (domain: {org2.domain})")
        print(f"Created User 2: {user2.email} (org_id: {user2.organisation_id})")
        print(f"Created OrgCredit for Org 2: balance={credit2.balance}")
        print()

        return org1.id, org2.id


async def test_org_isolation(org1_id: str, org2_id: str):
    """
    Verify that query for org 1's users cannot return org 2's users.
    """
    async with AsyncSessionLocal() as session:
        # Query users from Organisation 1
        stmt = select(User).where(User.organisation_id == org1_id)
        result = await session.execute(stmt)
        org1_users = result.scalars().all()

        # Query users from Organisation 2
        stmt = select(User).where(User.organisation_id == org2_id)
        result = await session.execute(stmt)
        org2_users = result.scalars().all()

        print("=== Multi-Tenancy Isolation Test ===")
        print()
        print(f"Users in Organisation 1 (Acme Corp): {len(org1_users)}")
        for user in org1_users:
            print(f"  - {user.email} (role: {user.role.value})")

        print()
        print(f"Users in Organisation 2 (Beta Inc): {len(org2_users)}")
        for user in org2_users:
            print(f"  - {user.email} (role: {user.role.value})")

        print()
        
        # Verify isolation
        assert len(org1_users) == 1, f"Expected 1 user in org 1, got {len(org1_users)}"
        assert len(org2_users) == 1, f"Expected 1 user in org 2, got {len(org2_users)}"
        assert org1_users[0].email == "john@acme.com"
        assert org2_users[0].email == "jane@beta.com"
        assert org1_users[0].organisation_id != org2_users[0].organisation_id

        print("✓ PASSED: Multi-tenancy isolation verified!")
        print("  - Org 1 can only see its own users")
        print("  - Org 2 can only see its own users")
        print("  - No data leakage between organisations")


async def test_credit_isolation(org1_id: str, org2_id: str):
    """Verify credit balance isolation between organisations."""
    async with AsyncSessionLocal() as session:
        # Query credits from Organisation 1
        stmt = select(OrgCredit).where(OrgCredit.organisation_id == org1_id)
        result = await session.execute(stmt)
        org1_credits = result.scalar_one_or_none()

        # Query credits from Organisation 2
        stmt = select(OrgCredit).where(OrgCredit.organisation_id == org2_id)
        result = await session.execute(stmt)
        org2_credits = result.scalar_one_or_none()

        print()
        print("=== Credit Balance Isolation Test ===")
        print()
        print(f"Organisation 1 (Acme Corp) credit balance: {org1_credits.balance}")
        print(f"Organisation 2 (Beta Inc) credit balance: {org2_credits.balance}")
        print()

        assert org1_credits.balance == 1000, f"Expected 1000, got {org1_credits.balance}"
        assert org2_credits.balance == 500, f"Expected 500, got {org2_credits.balance}"

        print("✓ PASSED: Credit isolation verified!")


async def main():
    """Main entry point for the test script."""
    print("Setting up test data...")
    print("=" * 50)
    org1_id, org2_id = await setup_test_data()

    await test_org_isolation(org1_id, org2_id)
    await test_credit_isolation(org1_id, org2_id)

    print()
    print("=" * 50)
    print("All multi-tenancy tests passed! ✓")


if __name__ == "__main__":
    asyncio.run(main())
