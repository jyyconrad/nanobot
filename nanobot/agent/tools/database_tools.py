"""
Database 工具 - 执行数据库操作
"""

from typing import Any, Dict
from nanobot.agent.tools.base import Tool


class MySQLQueryTool(Tool):
    """MySQL 查询工具"""

    name = "mysql_query"
    description = "执行 MySQL 查询"

    parameters = {
        "host": {
            "type": "string",
            "description": "MySQL 主机地址",
            "required": False,
            "default": "localhost",
        },
        "port": {
            "type": "integer",
            "description": "MySQL 端口",
            "required": False,
            "default": 3306,
        },
        "user": {
            "type": "string",
            "description": "MySQL 用户名",
            "required": True,
        },
        "password": {
            "type": "string",
            "description": "MySQL 密码",
            "required": True,
        },
        "database": {
            "type": "string",
            "description": "数据库名称",
            "required": True,
        },
        "query": {
            "type": "string",
            "description": "SQL 查询语句",
            "required": True,
        },
    }

    async def execute(
        self,
        host: str = "localhost",
        port: int = 3306,
        user: str = None,
        password: str = None,
        database: str = None,
        query: str = None,
    ) -> str:
        """执行 MySQL 查询"""
        try:
            import mysql.connector

            # 建立连接
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
            )

            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)

            # 根据查询类型返回结果
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                response = f"查询成功，返回 {len(results)} 条结果:\n"
                for row in results:
                    response += f"{row}\n"
            else:
                # 插入、更新、删除等
                conn.commit()
                response = f"操作成功，影响行数: {cursor.rowcount}"

            cursor.close()
            conn.close()

            return response

        except Exception as e:
            return f"MySQL 查询失败: {str(e)}"


class PostgreSQLQueryTool(Tool):
    """PostgreSQL 查询工具"""

    name = "postgresql_query"
    description = "执行 PostgreSQL 查询"

    parameters = {
        "host": {
            "type": "string",
            "description": "PostgreSQL 主机地址",
            "required": False,
            "default": "localhost",
        },
        "port": {
            "type": "integer",
            "description": "PostgreSQL 端口",
            "required": False,
            "default": 5432,
        },
        "user": {
            "type": "string",
            "description": "PostgreSQL 用户名",
            "required": True,
        },
        "password": {
            "type": "string",
            "description": "PostgreSQL 密码",
            "required": True,
        },
        "database": {
            "type": "string",
            "description": "数据库名称",
            "required": True,
        },
        "query": {
            "type": "string",
            "description": "SQL 查询语句",
            "required": True,
        },
    }

    async def execute(
        self,
        host: str = "localhost",
        port: int = 5432,
        user: str = None,
        password: str = None,
        database: str = None,
        query: str = None,
    ) -> str:
        """执行 PostgreSQL 查询"""
        try:
            import psycopg2

            # 建立连接
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
            )

            cursor = conn.cursor()
            cursor.execute(query)

            # 根据查询类型返回结果
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                response = f"查询成功，返回 {len(results)} 条结果:\n"
                for row in results:
                    response += f"{row}\n"
            else:
                # 插入、更新、删除等
                conn.commit()
                response = f"操作成功，影响行数: {cursor.rowcount}"

            cursor.close()
            conn.close()

            return response

        except Exception as e:
            return f"PostgreSQL 查询失败: {str(e)}"
