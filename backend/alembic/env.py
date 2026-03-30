from __future__ import annotations

import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from db.base import Base
from models import entities  # noqa: F401


config = context.config

_base_dir = Path(__file__).resolve().parent.parent
load_dotenv(_base_dir / ".env")
load_dotenv(_base_dir.parent / ".env")

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _build_database_url() -> str:
    direct = (os.getenv("DATABASE_URL", "") or "").strip()
    if direct:
        return direct

    db_user = (os.getenv("DB_USER", "postgres") or "postgres").strip()
    db_password = (os.getenv("DB_PASSWORD", "") or "").strip()
    db_host = (os.getenv("DB_HOST", "localhost") or "localhost").strip()
    db_port = (os.getenv("DB_PORT", "5432") or "5432").strip()
    db_name = (os.getenv("DB_NAME", "sitp_german_ai_agent") or "sitp_german_ai_agent").strip()
    auth = f"{db_user}:{db_password}" if db_password else db_user
    return f"postgresql+psycopg://{auth}@{db_host}:{db_port}/{db_name}"


config.set_main_option("sqlalchemy.url", _build_database_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
