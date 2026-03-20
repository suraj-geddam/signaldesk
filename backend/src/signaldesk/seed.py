from __future__ import annotations

from argparse import ArgumentParser, Namespace
from asyncio import run
from dataclasses import dataclass
from os import getenv

import asyncpg
from asyncpg import Connection
from passlib.context import CryptContext

from signaldesk.bootstrap import initialize_database

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class SeedUser:
    username: str
    password: str
    role: str


def _parser() -> ArgumentParser:
    parser = ArgumentParser(description="Seed SignalDesk data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    users = subparsers.add_parser("users", help="Seed auth users.")
    users.add_argument("--database-url", default=getenv("DATABASE_URL"))
    users.add_argument("--admin-username", default="admin")
    users.add_argument("--admin-password")
    users.add_argument("--member-username", default="member")
    users.add_argument("--member-password")
    users.add_argument(
        "--use-demo-passwords",
        action="store_true",
        help="Seed demo local passwords (admin123/member123).",
    )

    return parser


def _users_from_args(args: Namespace) -> list[SeedUser]:
    if args.use_demo_passwords:
        admin_password = "admin123"
        member_password = "member123"
    else:
        admin_password = args.admin_password
        member_password = args.member_password

    if not args.database_url:
        raise SystemExit("DATABASE_URL or --database-url is required.")
    if not admin_password or not member_password:
        raise SystemExit(
            "Provide --admin-password and --member-password, or use --use-demo-passwords.",
        )

    return [
        SeedUser(args.admin_username, admin_password, "admin"),
        SeedUser(args.member_username, member_password, "member"),
    ]


async def seed_users(connection: Connection, users: list[SeedUser]) -> None:
    payload = [
        (user.username, password_context.hash(user.password), user.role) for user in users
    ]
    await connection.executemany(
        """
        INSERT INTO users (username, password_hash, role)
        VALUES ($1, $2, $3)
        ON CONFLICT (username) DO UPDATE
        SET password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role
        """,
        payload,
    )


def seed_default_test_users(database_url: str) -> None:
    async def _seed() -> None:
        connection = await asyncpg.connect(database_url)
        try:
            await initialize_database(connection)
            await seed_users(
                connection,
                [
                    SeedUser("admin", "admin123", "admin"),
                    SeedUser("member", "member123", "member"),
                ],
            )
        finally:
            await connection.close()

    run(_seed())


async def _main(args: Namespace) -> None:
    if args.command != "users":
        raise SystemExit(f"Unsupported seed command: {args.command}")

    users = _users_from_args(args)
    connection = await asyncpg.connect(args.database_url)
    try:
        await initialize_database(connection)
        await seed_users(connection, users)
    finally:
        await connection.close()


def main() -> None:
    args = _parser().parse_args()
    run(_main(args))


if __name__ == "__main__":
    main()
