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
from mysql.connector.errors import IntegrityError, OperationalError, ProgrammingError
from typing import List


class DB_Base:
    """base for db handler"""

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
                seen_option BOOLEAN NOT NULL,
                cid_limit INT NOT NULL,
                custom_tag VARCHAR(255),
                audio_tag VARCHAR(255));
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


class DBHandler(DB_Base):
    """# handles the database"""

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
        except (OperationalError, ProgrammingError) as e:
            if retry_on_DBError:
                try:
                    self.cur.close()
                except:
                    pass
                self.connect_db()
                return self.add_user(uid=uid, name=name, retry_on_DBError=False)
            else:
                logger.error(f"{e.__class__}: {e}")
                raise Exception(str(e))
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

    def unblock_all(self, userid: str) -> None:
        """block or unblock user"""
        self.cur.execute(
            f'DELETE FROM {self.blocks_table} WHERE blocker_uid="{userid}"'
        )
        self.db.commit()

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

    def is_banned(self, uid: str) -> bool:
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

    def rm_cid(self, uid: str, cid: str) -> bool:
        self.cur.execute(
            f'DELETE FROM {self.cids_table} WHERE cid="{cid}" and uid="{uid}"'
        )
        self.db.commit()

    def get_cids(self, uid: str) -> List[str]:
        """get all the cids of a user"""
        self.cur.execute(
            f'SELECT cid FROM {self.cids_table} WHERE uid="{uid}" ' "ORDER BY id ASC"
        )
        return [item[0] for item in self.cur.fetchall()]

    def get_all_cids(self) -> List[str]:
        self.cur.execute(f"SELECT cid FROM {self.cids_table}")
        return self.cur.fetchall()

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
        """getes the warning state of user"""
        self.cur.execute(f'SELECT warning FROM {self.users_table} WHERE uid="{uid}"')
        return self.cur.fetchone()[0]

    def get_seen_status(self, uid: str) -> bool:
        """getes the seen option state of user"""
        self.cur.execute(
            f'SELECT seen_option FROM {self.users_table} WHERE uid="{uid}"'
        )
        return self.cur.fetchone()[0]

    def get_custom_tag(self, uid: str) -> str | None:
        """gets user's custom tag"""
        self.cur.execute(
            f"SELECT custom_tag FROM {self.users_table} " f'WHERE uid="{uid}"'
        )
        return self.cur.fetchone()[0]

    def get_audio_tag(self, uid: str) -> str | None:
        """gets the audio tag of user"""
        self.cur.execute(f'SELECT audio_tag FROM {self.users_table} WHERE uid="{uid}"')
        return self.cur.fetchone()[0]

    def set_name(self, uid: str, name: str) -> None:
        self.cur.execute(
            f'UPDATE {self.users_table} SET name=%s WHERE uid="{uid}"', (name,)
        )
        self.db.commit()

    def set_cid(self, new_cid: str, cid: str) -> None:
        self.cur.execute(
            f"UPDATE {self.cids_table} SET cid=%s WHERE cid='{cid}'", (new_cid,)
        )
        self.db.commit()

    def set_cid_limit(self, uid: str, cid_limit: int) -> None:
        self.cur.execute(
            f'UPDATE {self.users_table} SET cid_limit=%s WHERE uid="{uid}"',
            (cid_limit,),
        )
        self.db.commit()

    def set_warning(self, uid: str, warning: str) -> None:
        self.cur.execute(
            f'UPDATE {self.users_table} SET warning=%s WHERE uid="{uid}"',
            (warning,),
        )
        self.db.commit()

    def set_seen_option(self, uid: str, seen_option: bool) -> None:
        """sets seen_option for user"""
        try:
            self.cur.execute(
                f'UPDATE {self.users_table} SET seen_option=%s WHERE uid="{uid}"',
                (seen_option,),
            )
            self.db.commit()
        except IntegrityError:
            pass

    def set_custom_tag(self, uid: str, custom_tag: str) -> None:
        """sets custom tag for user"""
        try:
            self.cur.execute(
                f'UPDATE {self.users_table} SET custom_tag=%s WHERE uid="{uid}"',
                (custom_tag,),
            )
            self.db.commit()
        except IntegrityError:
            pass

    def set_audio_tag(self, uid: str, audio_tag: str) -> None:
        """sets audio tag for user"""
        try:
            self.cur.execute(
                f'UPDATE {self.users_table} SET audio_tag=%s WHERE uid="{uid}"',
                (audio_tag,),
            )
            self.db.commit()
        except IntegrityError:
            pass

    def user_status(self, uid: str) -> list:
        """gets ban status and cid limit of user"""
        self.cur.execute(
            f'SELECT is_banned, cid_limit FROM {self.users_table} WHERE uid="{uid}"'
        )
        return self.cur.fetchone()

    def user_count(self):
        self.cur.execute(f"SELECT COUNT(*) FROM {self.users_table}")
        return self.cur.fetchone()[0]


dbh = DBHandler()
