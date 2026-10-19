from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .disposer import reg_to_dispose


@lru_cache(maxsize=None)
def get_engine(db_url: str, debug: bool) -> AsyncEngine:
    engine = create_async_engine(
        db_url,
        echo=debug,
        pool_size=10,
        pool_pre_ping=True,
    )

    reg_to_dispose(engine.dispose)

    return engine


@lru_cache(maxsize=None)
def get_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
    )
