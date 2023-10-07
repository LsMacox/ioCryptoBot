from enver import getenv
import mysql.connector
from logger import logger

class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host=getenv('DB_HOST'),
            port=getenv('DB_PORT'),
            user=getenv('DB_USERNAME'),
            password=getenv('DB_PASSWORD'),
            database=getenv('DB_DATABASE')
        )
        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        if exc_type is not None:
            self.connection.rollback()
            logger.error(f"[DB] An error occurred: {exc_value}. Rolling back transaction.")
        else:
            self.connection.commit()
        self.connection.close()

    def commit(self):
        self.connection.commit()

    def fetch_by_id(self, table, unique_field, unique_value):
        self.cursor.execute(f'''
            SELECT * FROM {table}
            WHERE {unique_field} = %s
        ''', (unique_value,))
        return self.cursor.fetchone()

    def fetch_all(self, table, fields="*"):
        if isinstance(fields, list):
            fields_str = ", ".join(fields)
        else:
            fields_str = fields

        self.cursor.execute(f'''
            SELECT {fields_str} FROM {table}
        ''')
        return self.cursor.fetchall()

    def upsert(self, table, unique_field, unique_value, data):
        set_query = ", ".join([f"{key} = %s" for key in data.keys()])
        values = list(data.values()) + [unique_value]

        self.cursor.execute(f'''
            UPDATE {table}
            SET {set_query}
            WHERE {unique_field} = %s
        ''', values)

        if self.cursor.rowcount == 0:
            columns = ", ".join([unique_field] + list(data.keys()))
            placeholders = ", ".join(['%s'] * (len(data) + 1))
            values = [unique_value] + list(data.values())

            self.cursor.execute(f'''
                INSERT INTO {table} ({columns})
                VALUES ({placeholders})
            ''', values)

    def insert(self, table, data):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(['%s'] * len(data))
        values = list(data.values())

        self.cursor.execute(f'''
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
        ''', values)

        return self.cursor.lastrowid

    def fetch_nearest_pump(self, user_id, exchanger_name, symbol):
        query = """
        SELECT cp.*
        FROM coin_pumps AS cp
        WHERE cp.symbol = %s AND cp.exchanger_name = %s
        ORDER BY ABS(TIMESTAMPDIFF(SECOND, cp.created_at, (
            SELECT ulcp.last_pump
            FROM user_last_coin_pump AS ulcp
            WHERE ulcp.user_id = %s
            AND ulcp.symbol = %s
            AND ulcp.exchanger_name = %s
            LIMIT 1
        )))
        LIMIT 1;
        """

        self.cursor.execute(query, (symbol, exchanger_name, user_id, symbol, exchanger_name))
        return self.cursor.fetchone()

    def fetch_latest_pump(self, exchanger_name, symbol):
        query = """
        SELECT cp.*
        FROM coin_pumps AS cp
        WHERE cp.symbol = %s
        AND cp.exchanger_name = %s
        ORDER BY cp.created_at DESC
        LIMIT 1;
        """

        self.cursor.execute(query, (symbol, exchanger_name))
        return self.cursor.fetchone()

    def fetch_latest_user_pump(self, user_id, exchanger_name, symbol):
        query = """
           SELECT cp.*
           FROM user_last_coin_pump AS cp
           WHERE cp.user_id = %s 
           AND cp.symbol = %s
           AND cp.exchanger_name = %s
           ORDER BY cp.last_pump DESC
           LIMIT 1;
           """

        self.cursor.execute(query, (user_id, symbol, exchanger_name))
        return self.cursor.fetchone()
