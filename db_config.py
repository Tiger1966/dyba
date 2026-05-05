import os
import mysql.connector
from mysql.connector import pooling

# 从环境变量获取数据库连接信息
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "dianyin")

dbconfig = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "dianyin",
    "password": "kKGXPr5ZNxKrYET4",  # 这里就是你给我的真钥匙
    "database": "dianyin",
    "charset": "utf8mb4"
}

# 建立连接池（pool_size=10）
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="dianyin_pool",
        pool_size=10,
        pool_reset_session=True,
        **dbconfig
    )
except mysql.connector.Error as err:
    print(f"Error creating connection pool: {err}")
    connection_pool = None

def get_db():
    if not connection_pool:
        raise RuntimeError("Database connection pool is not initialized")
    
    # 从连接池中获取一个连接
    conn = connection_pool.get_connection()
    try:
        yield conn
    finally:
        # 使用完毕后将连接归还连接池
        conn.close()
