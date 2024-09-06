# project imports
from config import (
    DB_USER,
    DB_PASS,
    DB_NAME,
    MAX_TRY_ADD_CID,
    DEFAULT_CID_LIMIT,
    MAX_NAME_LENGTH,
)

# global imports
import mysql.connector
from mysql.connector.errors import IntegrityError
from typing import List


class DBHandler:
    """# handles the database"""

    def __init__(self) -> None:
        # table names
        self.users_table = "users"
        self.blocks_table = "blocks"
        self.cids_table = "cids"

        # init runs
        self.connect_db()
        self.make_tables()

    def connect_db(self) -> None:
        """connects to database"""
        self.db = mysql.connector.connect(
            host="localhost", user=DB_USER, password=DB_PASS, database=DB_NAME
        )
        self.cur = self.db.cursor()

    def make_tables(self) -> None:
        """creates the tables if they don't exist"""
        self.cur.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.users_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                is_banned BOOLEAN NOT NULL,
                warning BOOLEAN NOT NULL,
                cid_limit INT NOT NULL);
            """
        )
        self.cur.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.blocks_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                blocker_uid VARCHAR(255) NOT NULL,
                blocked_uid VARCHAR(255) NOT NULL,
                CONSTRAINT unique_pair UNIQUE (blocker_uid, blocked_uid));
            """
        )
        self.cur.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.cids_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(255) NOT NULL,
                cid VARCHAR(255) NOT NULL UNIQUE);
            """
        )

    def add_user(self, uid: str, name) -> bool:
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
                f"INSERT INTO {self.users_table} VALUES (NULL, %s, %s, %s, %s, %s)",
                (str(uid), str(name)[:MAX_NAME_LENGTH], False, True, DEFAULT_CID_LIMIT),
            )
            self.db.commit()
            return True
        except IntegrityError:
            return False

    def add_block(self, blocker_uid: str, blocked_uid: str) -> bool:
        """blocks the given user"""
        try:
            self.cur.execute(
                f"INSERT INTO {self.blocks_table} VALUES (NULL, %s, %s)",
                (
                    str(blocker_uid),
                    str(blocked_uid),
                ),
            )
            self.db.commit()
            return True
        except IntegrityError:
            return False

    def remove_block(self, blocker_uid: str, blocked_uid: str) -> bool:
        """removes a block"""
        try:
            self.cur.execute(
                f"DELETE FROM {self.blocks_table} "
                f'WHERE blocker_uid="{blocker_uid}" '
                f'and blocked_uid="{blocked_uid}"'
            )
            self.db.commit()
            return True
        except IntegrityError:
            return False

    def is_blocked(self, blocker_uid: str, blocked_uid: str) -> bool:
        """checks if a user is blocked"""
        self.cur.execute(
            f'SELECT * FROM {self.blocks_table} WHERE blocker_uid="{blocker_uid}" '
            f'and blocked_uid="{blocked_uid}"'
        )
        output = self.cur.fetchall()
        if len(output):
            return True
        else:
            return False

    def user_is_banned(self, uid: str) -> bool:
        """checks if a user is banned"""
        self.cur.execute(f'SELECT is_banned from {self.users_table} WHERE uid="{uid}"')
        return self.cur.fetchall()[0][0]

    def ban_action(self, uid: str, ban: bool) -> None:
        """ban or unban user"""
        ban_translation = "TRUE" if ban else "FALSE"
        self.cur.execute(
            f"INSERT INTO {self.users_table} VALUES (NULL, %s, %s) "
            f"ON CONFLICT (uid) DO UPDATE "
            f"SET is_banned=EXCLUDED.is_banned",
            (str(uid), ban_translation),
        )
        self.db.commit()

    def add_cid(self, uid: int, cid: int, try_counter: int = 0) -> bool:
        """add cid for user"""
        if try_counter >= MAX_TRY_ADD_CID:
            return False
        try:
            self.cur.execute(
                f"INSERT INTO {self.cids_table} VALUES (NULL, %s, %s)",
                (str(uid), str(cid)),
            )
            self.db.commit()
            return True
        except IntegrityError:
            try_counter += 1
            return self.add_cid(uid, cid, try_counter)

    def get_cids(self, uid: str) -> List[str]:
        """get all the cids of a user"""
        self.cur.execute(
            f'SELECT cid FROM {self.cids_table} WHERE uid="{uid}" ' "ORDER BY id ASC"
        )
        return [item[0] for item in self.cur.fetchall()]

    def get_name(self, uid: str) -> str | None:
        """gets the preview name of a user"""
        self.cur.execute(f'SELECT name FROM {self.users_table} WHERE uid="{uid}"')
        output = self.cur.fetchall()
        if len(output):
            return output[0][0]
        else:
            return None

    def get_uid(self, cid: str) -> str | None:
        """gets the uid based on a cid"""
        self.cur.execute(f'SELECT uid FROM {self.cids_table} WHERE cid="{cid}"')
        output = self.cur.fetchall()
        if len(output):
            return output[0][0]
        else:
            return None

    def get_cid_limit(self, uid: str) -> int:
        """gets the cid limit for a user"""
        self.cur.execute(f'SELECT cid_limit FROM {self.users_table} WHERE uid="{uid}"')
        return self.cur.fetchone()[0]

    def get_warning(self, uid: str) -> bool:
        self.cur.execute(f'SELECT warning FROM {self.users_table} WHERE uid="{uid}"')
        return self.cur.fetchone()[0]

    def user_status(self, uid: str) -> list:
        self.cur.execute(
            f'SELECT is_banned, cid_limit FROM {self.users_table} WHERE uid="{uid}"'
        )
        return self.cur.fetchone()


dbh = DBHandler()
