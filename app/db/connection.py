# app/db/connection.py
"""PostgreSQL Database Connection Management using asyncpg"""

import os
import logging
from typing import Optional, List, Dict, Any
import asyncpg
from asyncpg import Pool
import yaml

logger = logging.getLogger(__name__)


def _load_db_config() -> Dict[str, Any]:
    """Load database configuration from ai_config.yaml"""
    # Try multiple config paths
    config_paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'ai_integration', 'ai_config.yaml'),
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ai_integration', 'ai_config.yaml'),
        'ai_integration/ai_config.yaml',
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    db_config = config.get('database', {})
                    logger.info(f"Loaded database config from: {config_path}")
                    return {
                        "host": db_config.get("host", "localhost"),
                        "port": int(db_config.get("port", 5432)),
                        "database": db_config.get("name", "trading_db"),
                        "user": db_config.get("user", "postgres"),
                        "password": db_config.get("password", "postgres"),
                        "min_size": int(db_config.get("pool_min", 5)),
                        "max_size": int(db_config.get("pool_max", 20)),
                    }
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {str(e)}")
    
    # Fallback to environment variables
    logger.info("Fallback to environment variables for database config")
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "database": os.getenv("POSTGRES_DB", "trading_db"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "min_size": int(os.getenv("POSTGRES_POOL_MIN", "5")),
        "max_size": int(os.getenv("POSTGRES_POOL_MAX", "20")),
    }


# Database configuration
DB_CONFIG = _load_db_config()

# Global connection pool
_pool: Optional[Pool] = None


async def get_db_pool() -> Pool:
    """Get or create database connection pool"""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                database=DB_CONFIG["database"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                min_size=DB_CONFIG["min_size"],
                max_size=DB_CONFIG["max_size"],
            )
            logger.info(f"Database pool created: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        except Exception as e:
            logger.error(f"Failed to create database pool: {str(e)}")
            raise
    return _pool


async def close_db_pool():
    """Close database connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


async def execute_query(query: str, *args) -> str:
    """Execute a query that doesn't return rows (INSERT, UPDATE, DELETE)"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(query, *args)
        return result


async def fetch_one(query: str, *args) -> Optional[Dict[str, Any]]:
    """Fetch a single row"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def fetch_all(query: str, *args) -> List[Dict[str, Any]]:
    """Fetch all rows"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def fetch_val(query: str, *args) -> Any:
    """Fetch a single value"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)


async def execute_many(query: str, args_list: List[tuple]) -> None:
    """Execute a query multiple times with different arguments"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.executemany(query, args_list)


async def init_database():
    """Initialize database tables from schema file"""
    import os
    schema_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'schema.sql')
    
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(schema_sql)
            logger.info("Database schema initialized")
    else:
        logger.warning(f"Schema file not found: {schema_path}")
