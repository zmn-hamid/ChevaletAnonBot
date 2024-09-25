# project imports
from config import (
    DB_USER,
    DB_PASS,
    DB_NAME,
    MAX_TRY_ADD_CID,
    DEFAULT_CID_LIMIT,
    MAX_NAME_LENGTH,
    DEFAULT_AUDIO_TAG,
)
from modules.Global.log import logger

# global imports
import mysql.connector
from mysql.connector import pooling
from mysql.connector.pooling import PooledMySQLConnection
from mysql.connector.cursor import MySQLCursor
from mysql.connector.errors import IntegrityError, OperationalError, ProgrammingError
from typing import List


class DB_Base:
    """base for db handler"""

    def __init__(self) -> None:
        # table names
        self.users_table = "users"
        self.blocks_table = "blocks"
        self.cids_table = "cids"

        self.connection_pool: pooling.MySQLConnectionPool

        # # init runs
        # self.connect_db()
        # self.make_tables()

    def connect_db(self) -> None:
        """connects to database"""
        self.connection_pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            pool_reset_session=True,
            host="localhost",
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        )

    def make_tables(self) -> None:
        """creates the tables if they don't exist"""
        with self.connection_pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.users_table} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        uid VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        is_banned BOOLEAN NOT NULL,
                        warning BOOLEAN NOT NULL,
                        seen_option BOOLEAN NOT NULL,
                        cid_limit INT NOT NULL,
                        custom_tag VARCHAR(255),
                        audio_tag VARCHAR(255));
                    """
                )
                cur.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.blocks_table} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        blocker_uid VARCHAR(255) NOT NULL,
                        blocked_uid VARCHAR(255) NOT NULL,
                        CONSTRAINT unique_pair UNIQUE (blocker_uid, blocked_uid));
                    """
                )
                cur.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.cids_table} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        uid VARCHAR(255) NOT NULL,
                        cid VARCHAR(255) NOT NULL UNIQUE);
                    """
                )


class DBHandler(DB_Base):
    """# handles the database"""

    def __init__(self, cur: MySQLCursor, conn: PooledMySQLConnection) -> None:
        self.cur = cur
        self.db = conn

    def add_user(self, uid: str, name, retry_on_DBError: bool = True) -> bool:
        """
        # adds user to the database
        the defaults:
        - user id
        - full name
        - not banned
        - not notifying the cid (source)
        - 2 max cids
        """
        try:
            self.cur.execute(
                f"INSERT INTO {self.users_table} VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    str(uid),
                    str(name)[:MAX_NAME_LENGTH],
                    False,
                    True,
                    False,
                    DEFAULT_CID_LIMIT,
                    None,
                    DEFAULT_AUDIO_TAG,
                ),
            )
            self.db.commit()

            return True
        except IntegrityError:
            return False


DB_Base()
