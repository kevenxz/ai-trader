import asyncio
from app.db.connection import execute_query

async def create_table():
    query = """
    CREATE TABLE IF NOT EXISTS realtime_tracking_config (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES ai_trading_orders(id) ON DELETE CASCADE,
        is_enabled BOOLEAN DEFAULT true,
        tracking_interval VARCHAR(10) DEFAULT '1m',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    await execute_query(query)
    print("Table created successfully")

    index_query = "CREATE INDEX IF NOT EXISTS idx_realtime_order_id ON realtime_tracking_config(order_id);"
    await execute_query(index_query)
    print("Index created successfully")

if __name__ == "__main__":
    asyncio.run(create_table())
