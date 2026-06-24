from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionLocal
from schemas.models import User, Roles, Permission
from auth.security import get_hash
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio
from core.config import getSettings

fake = Faker()

ROLES = {
    "admin": [
        "users:read",
        "users:update",
        "users:delete",
        "conversations:create",
        "conversations:read",
        "conversations:delete",
        "documents:create",
        "documents:read",
        "documents:delete",
        "ai:embed",
        "ai:search",
        "ai:chat",
        "ticket:manage",
    ],
    "users": [
        "users:read",
        "users:update",
        "conversations:create",
        "conversations:read",
        "conversations:delete",
        "documents:create",
        "documents:read",
        "documents:delete",
        "ai:embed",
        "ai:search",
        "ai:chat",
    ],
}


async def seed_permissions(db: AsyncSession) -> dict[str, Permission]:
    """Create all permissions"""
    all_perms = {p for perm in ROLES.values() for p in perm}
    result = {}
    for name in all_perms:
        perm_result = await db.execute(
            select(Permission).where(Permission.name == name)
        )
        perm = perm_result.scalar_one_or_none()
        if not perm:
            resource, action = name.split(":", 1)
            perm = Permission(name=name, resource=resource, action=action)
            db.add(perm)
        result[name] = perm
    await db.commit()
    return result


async def seed_roles(db: AsyncSession, perms: dict) -> dict[str, Roles]:
    """Create roles if they don't exist. Return name-to-Roles mapping."""
    result = {}
    for role_name, perm_name in ROLES.items():
        # Idempotent: check before inserting
        stmt = (
            select(Roles)
            .options(selectinload(Roles.permissions))
            .where(Roles.name == role_name)
        )
        role_result = await db.execute(stmt)
        role = role_result.scalar_one_or_none()
        if role is None:
            role = Roles(name=role_name)
            db.add(role)
            # await db.flush()
        existing_perm_names = {p.name for p in role.permissions}
        for pname in perm_name:
            if pname not in existing_perm_names:
                role.permissions.append(perms[pname])
        result[role_name] = role
    await db.commit()
    return result


async def seed_admin_user(
    db: AsyncSession,
    roles: dict[str, Roles],
    *,
    email: str | None = None,
    password: str | None = None,
) -> User | None:
    """Create default admin when missing. Skips if that email already exists."""
    settings = getSettings()
    email = (email or settings.ADMIN_EMAIL).strip().lower()
    password = password or settings.ADMIN_PASSWORD
    if not email or not password:
        print("Skipping admin seed: set ADMIN_EMAIL and ADMIN_PASSWORD")
        return None

    admin_role = roles.get("admin")
    if admin_role is None:
        raise RuntimeError("admin role missing — run seed_roles first")

    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.email == email)
    )
    if result.scalar_one_or_none() is not None:
        print(f"Admin seed skipped: user already exists ({email})")
        return None

    user = User(email=email, password=get_hash(password))
    user.roles.append(admin_role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    print(f"Admin seed created: {email}")
    return user


def seed_users(
    db: AsyncSession,
    roles: dict[str, Roles],
    count: int = 10,
) -> list[User]:
    """Create fake users if fewer than count exist."""
    existing = db.query(User).count()
    if existing >= count:
        return db.query(User).all()
    users = []
    role_values = list(roles.values())
    for _ in range(count - existing):
        user = User(
            id=uuid4(),
            username=fake.user_name(),
            email=fake.email(),
            password=get_hash("dummypass12345"),
        )
        db.add(user)
        role = fake.random_element(role_values)

        user.roles.append(role)

        db.add(user)
        users.append(user)
    db.commit()
    return users


async def run_seed():
    async with SessionLocal() as db:
        try:
            perms = await seed_permissions(db)
            roles = await seed_roles(db, perms)
            admin = await seed_admin_user(db, roles)

            print("Seeded successfully:")
            print(f"- {len(perms)} permissions, {len(roles)} roles")
            if admin:
                print(f"- 1 admin user ({admin.email})")
        except Exception as e:
            await db.rollback()
            print(f"Seed failed: {e}")


if __name__ == "__main__":
    asyncio.run(run_seed())
