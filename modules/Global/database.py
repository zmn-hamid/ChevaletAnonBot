from typing import List

from psycopg2 import pool

from config import (
    DB_HOST,
    DB_NAME,
    DB_PASS,
    DB_USER,
    DEFAULT_AUDIO_TAG,
    DEFAULT_CID_LIMIT,
    MAX_NAME_LENGTH,
    MAX_TRY_ADD_CID,
)
from modules.Global.cid_gen import generate_cid
from modules.Global.log import logger


class DB_Base:
    """base for db handler"""

    def __init__(self) -> None:
        # table names
        self.users_table = "users"
        self.blocks_table = "blocks"
        self.cids_table = "cids"
        self.reports_table = "reports"

        self._connection_pool: pool.SimpleConnectionPool

    def connect_db(self) -> None:
        """connects to database"""
        self._connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=30,
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            options="-c client_encoding=UTF8",
        )

    def get_connection(self):
        conn = self._connection_pool.getconn()
        conn.autocommit = True  # Enable autocommit
        return conn

    def put_connection(self, conn):
        self._connection_pool.putconn(conn)

    def make_tables(self) -> None:
        """creates the tables if they don't exist"""
        conn = self.get_connection()
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.users_table} (
                        id SERIAL PRIMARY KEY,
                        uid VARCHAR(255) NOT NULL UNIQUE,
                        name VARCHAR(255) NOT NULL,
                        is_banned BOOLEAN NOT NULL DEFAULT FALSE,
                        warning BOOLEAN NOT NULL DEFAULT TRUE,
                        seen_option BOOLEAN NOT NULL DEFAULT FALSE,
                        wpp BOOLEAN NOT NULL DEFAULT TRUE,
                        cid_limit INTEGER NOT NULL DEFAULT {DEFAULT_CID_LIMIT},
                        custom_tag VARCHAR(255),
                        audio_tag VARCHAR(255) DEFAULT '{DEFAULT_AUDIO_TAG}',
                        chevaletid VARCHAR(255));
                    """
                )
                cur.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.blocks_table} (
                        id SERIAL PRIMARY KEY,
                        blocker_uid VARCHAR(255) NOT NULL,
                        blocked_uid VARCHAR(255) NOT NULL,
                        CONSTRAINT unique_pair UNIQUE (blocker_uid, blocked_uid));
                    """
                )
                cur.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.cids_table} (
                        id SERIAL PRIMARY KEY,
                        uid VARCHAR(255) NOT NULL,
                        cid VARCHAR(255) NOT NULL UNIQUE);
                    """
                )
                cur.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.reports_table} (
                        id SERIAL PRIMARY KEY,
                        reported_id VARCHAR(255) NOT NULL);
                    """
                )
                conn.commit()
        finally:
            self.put_connection(conn)


class DBHandler(DB_Base):
    """# handles the database"""

    def __init__(self, cur, conn) -> None:
        super().__init__()
        self.cur = cur
        self.db = conn

    def add_user(self, uid: str, name: str) -> bool:
        """
        # adds user to the database using UPSERT
        the defaults:
        - user id
        - full name
        - not banned
        - not notifying the cid (source)
        - no seen option
        - with webpage preview
        - 2 max cids
        - no custom tag
        - audio tag: [ناشناس]

        Returns True if user was inserted, False if already exists
        """
        self.cur.execute(
            f"""INSERT INTO {self.users_table}
                (uid, name, is_banned, warning, seen_option, wpp, cid_limit, custom_tag, audio_tag, chevaletid)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (uid) DO NOTHING""",
            (
                str(uid),
                str(name)[:MAX_NAME_LENGTH],
                False,
                True,
                False,
                True,
                DEFAULT_CID_LIMIT,
                None,
                DEFAULT_AUDIO_TAG,
                None,
            ),
        )
        return self.cur.rowcount > 0

    def add_block(self, blocker_uid: str, blocked_uid: str) -> bool:
        """
        Blocks the given user using UPSERT.
        Returns True if block was created, False if already exists.
        """
        self.cur.execute(
            f"""INSERT INTO {self.blocks_table} (blocker_uid, blocked_uid)
                VALUES (%s, %s)
                ON CONFLICT (blocker_uid, blocked_uid) DO NOTHING""",
            (
                str(blocker_uid),
                str(blocked_uid),
            ),
        )
        return self.cur.rowcount > 0

    def remove_block(self, blocker_uid: str, blocked_uid: str) -> bool:
        """removes a block"""
        self.cur.execute(
            f"DELETE FROM {self.blocks_table} WHERE blocker_uid=%s and blocked_uid=%s",
            (str(blocker_uid), str(blocked_uid)),
        )
        return True

    def unblock_all(self, userid: str) -> None:
        """block or unblock user"""
        self.cur.execute(
            f"DELETE FROM {self.blocks_table} WHERE blocker_uid=%s", (str(userid),)
        )

    def is_blocked(self, blocker_uid: str, blocked_uid: str) -> bool:
        """checks if a user is blocked"""
        self.cur.execute(
            f"SELECT * FROM {self.blocks_table} WHERE blocker_uid=%s and blocked_uid=%s",
            (str(blocker_uid), str(blocked_uid)),
        )
        output = self.cur.fetchall()
        if len(output):
            return True
        else:
            return False

    def is_banned(self, uid: str) -> bool:
        """checks if a user is banned"""
        self.cur.execute(
            f"SELECT is_banned from {self.users_table} WHERE uid=%s", (str(uid),)
        )
        return self.cur.fetchall()[0][0]

    def ban_action(self, uid: str, ban: bool) -> None:
        """ban or unban user"""
        try:
            self.add_user(uid, "-")
        except:
            pass

        self.cur.execute(
            f"UPDATE {self.users_table} SET is_banned=%s WHERE uid=%s",
            (ban, str(uid)),
        )

    def add_cid(self, uid: int, cid: int, try_counter: int = 0) -> bool:
        """
        Adds cid for user using UPSERT with retry logic.
        If cid collision occurs, automatically generates a new cid and retries.
        Returns True if successful, False if max retries exceeded.
        """
        if try_counter >= MAX_TRY_ADD_CID:
            return False

        self.cur.execute(
            f"""INSERT INTO {self.cids_table} (uid, cid)
                VALUES (%s, %s)
                ON CONFLICT (cid) DO NOTHING""",
            (str(uid), str(cid)),
        )

        if self.cur.rowcount > 0:
            # Successfully inserted
            return True
        else:
            # CID collision occurred, retry with new CID
            try_counter += 1
            return self.add_cid(uid, generate_cid(), try_counter)

    def rm_cid(self, uid: str, cid: str) -> bool:
        self.cur.execute(
            f"DELETE FROM {self.cids_table} WHERE cid=%s and uid=%s",
            (str(cid), str(uid)),
        )

    def get_all_uids(self) -> List[List[str]]:
        """returns all the uids"""
        self.cur.execute(f"SELECT uid FROM {self.users_table}")
        return self.cur.fetchall()

    def get_cids(self, uid: str) -> List[str]:
        """get all the cids of a user"""
        self.cur.execute(
            f"SELECT cid FROM {self.cids_table} WHERE uid=%s ORDER BY id ASC",
            (str(uid),),
        )
        return [item[0] for item in self.cur.fetchall()]

    def get_all_cids(self) -> List[str]:
        self.cur.execute(f"SELECT cid FROM {self.cids_table}")
        return self.cur.fetchall()

    def get_name(self, uid: str) -> str | None:
        """gets the preview name of a user"""
        self.cur.execute(
            f"SELECT name FROM {self.users_table} WHERE uid=%s", (str(uid),)
        )
        output = self.cur.fetchall()
        if len(output):
            return output[0][0]
        else:
            return None

    def get_uid(self, cid: str) -> str | None:
        """
        gets the uid based on a cid
        """
        logger.warning(
            "depricated method: DBHandler.get_uid. use DBHandler.get_uid_by_cid instead"
        )
        self.cur.execute(f"SELECT uid FROM {self.cids_table} WHERE cid=%s", (str(cid),))
        output = self.cur.fetchall()
        if len(output):
            return output[0][0]
        else:
            return None

    def get_uid_by_cid(self, cid: str) -> str | None:
        """
        gets the uid based on a cid
        """
        self.cur.execute(f"SELECT uid FROM {self.cids_table} WHERE cid=%s", (str(cid),))
        output = self.cur.fetchall()
        if len(output):
            return output[0][0]
        else:
            return None

    def get_uid_by_chevaletid(self, chevaletid: str) -> str | None:
        """gets the uid based on chevaletid"""
        self.cur.execute(
            f"SELECT uid FROM {self.users_table} WHERE chevaletid=%s",
            (str(chevaletid),),
        )
        output = self.cur.fetchall()
        if len(output):
            return output[0][0]
        else:
            return None

    def get_chevaletid_by_uid(self, uid: str) -> str | None:
        """gets the chevaletid based on uid"""
        self.cur.execute(
            f"SELECT chevaletid FROM {self.users_table} WHERE uid=%s", (str(uid),)
        )
        output = self.cur.fetchall()
        if len(output):
            return output[0][0]
        else:
            return None

    def get_all_chevaletids(self) -> List[str]:
        self.cur.execute(f"SELECT chevaletid FROM {self.users_table}")
        return self.cur.fetchall()

    def get_cid_limit(self, uid: str) -> int:
        """gets the cid limit for a user"""
        self.cur.execute(
            f"SELECT cid_limit FROM {self.users_table} WHERE uid=%s", (str(uid),)
        )
        return self.cur.fetchone()[0]

    def get_warning(self, uid: str) -> bool:
        """getes the warning state of user"""
        self.cur.execute(
            f"SELECT warning FROM {self.users_table} WHERE uid=%s", (str(uid),)
        )
        return self.cur.fetchone()[0]

    def get_seen_status(self, uid: str) -> bool:
        """getes the seen option state of user"""
        self.cur.execute(
            f"SELECT seen_option FROM {self.users_table} WHERE uid=%s", (str(uid),)
        )
        return self.cur.fetchone()[0]

    def get_wpp(self, uid: str) -> bool:
        """getes the webpage preview state of user"""
        self.cur.execute(
            f"SELECT wpp FROM {self.users_table} WHERE uid=%s", (str(uid),)
        )
        return self.cur.fetchone()[0]

    def get_custom_tag(self, uid: str) -> str | None:
        """gets user's custom tag"""
        self.cur.execute(
            f"SELECT custom_tag FROM {self.users_table} WHERE uid=%s", (str(uid),)
        )
        return self.cur.fetchone()[0]

    def get_audio_tag(self, uid: str) -> str | None:
        """gets the audio tag of user"""
        self.cur.execute(
            f"SELECT audio_tag FROM {self.users_table} WHERE uid=%s", (str(uid),)
        )
        return self.cur.fetchone()[0]

    def set_name(self, uid: str, name: str) -> None:
        self.cur.execute(
            f"UPDATE {self.users_table} SET name=%s WHERE uid=%s", (name, str(uid))
        )

    def set_cid(self, new_cid: str, cid: str) -> None:
        self.cur.execute(
            f"UPDATE {self.cids_table} SET cid=%s WHERE cid=%s",
            (str(new_cid), str(cid)),
        )

    def set_cid_limit(self, uid: str, cid_limit: int) -> None:
        self.cur.execute(
            f"UPDATE {self.users_table} SET cid_limit=%s WHERE uid=%s",
            (str(cid_limit), str(uid)),
        )

    def set_warning(self, uid: str, warning: bool) -> None:
        self.cur.execute(
            f"UPDATE {self.users_table} SET warning=%s WHERE uid=%s",
            (warning, str(uid)),
        )

    def set_seen_option(self, uid: str, seen_option: bool) -> None:
        """sets seen_option for user"""
        self.cur.execute(
            f"UPDATE {self.users_table} SET seen_option=%s WHERE uid=%s",
            (seen_option, str(uid)),
        )

    def set_wpp(self, uid: str, wpp: bool) -> None:
        """sets wpp for user"""
        self.cur.execute(
            f"UPDATE {self.users_table} SET wpp=%s WHERE uid=%s",
            (wpp, str(uid)),
        )

    def set_custom_tag(self, uid: str, custom_tag: str | None) -> None:
        """sets custom tag for user"""
        self.cur.execute(
            f"UPDATE {self.users_table} SET custom_tag=%s WHERE uid=%s",
            (custom_tag, str(uid)),
        )

    def set_audio_tag(self, uid: str, audio_tag: str | None) -> None:
        """sets audio tag for user"""
        self.cur.execute(
            f"UPDATE {self.users_table} SET audio_tag=%s WHERE uid=%s",
            (audio_tag, str(uid)),
        )

    def set_chevaletid(self, uid: str, chevaletid: str) -> None:
        """sets chevaletid for user"""
        self.cur.execute(
            f"UPDATE {self.users_table} SET chevaletid=%s WHERE uid=%s",
            (str(chevaletid), str(uid)),
        )
        return True

    def user_status(self, uid: str) -> list:
        """gets ban status and cid limit of user"""
        self.cur.execute(
            f"SELECT is_banned, cid_limit FROM {self.users_table} WHERE uid=%s",
            (str(uid),),
        )
        return self.cur.fetchone()

    def user_count(self):
        self.cur.execute(f"SELECT COUNT(*) FROM {self.users_table}")
        return self.cur.fetchone()[0]

    def add_report_id(self, report_id: str):
        self.cur.execute(
            f"INSERT INTO {self.reports_table} VALUES (DEFAULT, %s)", (str(report_id),)
        )
        return self.get_report_id(report_id)

    def del_report_id(self, report_id: str):
        count = self.get_report_id(report_id)
        if count:
            self.cur.execute(
                f"DELETE FROM {self.reports_table} WHERE reported_id=%s",
                (str(report_id),),
            )
        return count

    def get_report_id(self, report_id: str):
        self.cur.execute(
            f"SELECT COUNT(*) FROM {self.reports_table} WHERE reported_id=%s",
            (str(report_id),),
        )
        return self.cur.fetchone()[0]

    def get_all_reports(self):
        self.cur.execute(f"SELECT reported_id FROM {self.reports_table}")
        _reports = [item[0] for item in self.cur.fetchall()]
        reports = {}
        for r in _reports:
            if r in reports.keys():
                reports[r] += 1
            else:
                reports[r] = 1
        return reports


db_base = DB_Base()
db_base.connect_db()
db_base.make_tables()
