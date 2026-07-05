"""Alembic migration environment for DemandFlow (Feature F002).

Reads the target metadata from ``app.models.Base.metadata`` and the DB URL from
the ``DATABASE_URL`` environment variable (falling back to
``app.core.config.Settings.DATABASE_URL``).
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import the app's Base metadata + config so migrations share ORM definitions.
import os
import sys
from pathlib import Path

# Ensure project root is importable when alembic runs from project dir
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Base  # noqa: E402
from app.core.config import Settings  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def _get_url() -> str:
    """Resolve the DB URL: DATABASE_URL env var takes precedence, else Settings."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    return Settings().DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emit SQL to stdout."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connect to the DB and apply."""
    url = _get_url()
    # Build a section with the resolved URL so engine_from_config picks it up
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = url
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite-friendly ALTER support
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
