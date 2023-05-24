import asyncio
import aiomysql
from sql_app.database import DB_HOST, DB_USER, DB_PASSWD, DB_PORT, DB_NAME

async def check_mysql_connection():
    """
    1.创建数据库连接池
    2. 执行一个简单的 SQL 查询
    3.  检查查询结果
    Returns:

    """
    if not (DB_HOST and DB_USER and DB_PASSWD and DB_PORT and DB_NAME):
        return {"code": 50000, "message": "MySQL 数据库连接异常,数据库配置缺少", "status": False}
    try:
        pool = await aiomysql.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWD,
            db=DB_NAME,
            autocommit=True
        )
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT 1')
                result = await cursor.fetchone()
                if result[0] == 1:
                    return {"code": 20000, "message": "MySQL 数据库连接正常", "status": True}
                else:
                    return {"code": 50000, "message": "MySQL 数据库连接异常", "status": False}
    except Exception as e:
        detail = "无法连接到 MySQL 数据库"
        return {"code": 50000, "message": detail, "status": False}
