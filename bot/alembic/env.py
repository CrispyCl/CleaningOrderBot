from logging.config import fileConfig

from alembic import context
import alembic_postgresql_enum  # noqa: F401
from sqlalchemy import create_engine
from sqlalchemy import pool

from config import load_config
from database import Base
from models import Order, User  # noqa: F401


db_config = load_config()
database_url = db_config.postgres.get_database_url()

config = context.config
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(
        database_url.replace("postgresql+asyncpg", "postgresql"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()


__all__ = ["run_migrations_online"]
