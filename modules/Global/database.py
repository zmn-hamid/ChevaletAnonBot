import mysql.connector
from mysql.connector.errors import IntegrityError


class DBHandler:
    def __init__(self):
        self.users_table = "users"
        self.blocks_table = "blocks"
        self.cids_table = "cids"

        self.cid_count = 0

    def connect_db(self):
        self.db = mysql.connector.connect(
            host="localhost", user="root", password="hamid1780", database="mydatabase"
        )
        self.cur = self.db.cursor()

    def make_tables(self):
        self.cur.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.users_table} (
                uid VARCHAR(255) NOT NULL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                is_banned BOOLEAN NOT NULL);
            """
        )
        self.cur.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.blocks_table} (
                blocker_uid VARCHAR(255) NOT NULL,
                blocked_uid VARCHAR(255) NOT NULL,
                CONSTRAINT unique_pair UNIQUE (blocker_uid, blocked_uid));
            """
        )
        self.cur.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.cids_table} (
                uid VARCHAR(255) NOT NULL,
                cid VARCHAR(255) NOT NULL UNIQUE);
            """
        )

    def calc_cid_count(self):
        self.cur.execute(f"SELECT uid FROM {self.users_table}")
        self.cid_count = len(self.cur.fetchall())

    def add_user(self, uid: str, name):
        try:
            self.cur.execute(
                f"""INSERT INTO {self.users_table}
                    VALUES ("{uid}", "{name}", FALSE)"""
            )
            self.db.commit()
            return True
        except IntegrityError:
            return False

    def add_block(self, blocker_uid: str, blocked_uid: str):
        try:
            self.cur.execute(
                f"""INSERT INTO {self.blocks_table}
                                VALUES ("{str(blocker_uid)}", "{str(blocked_uid)}")"""
            )
            self.db.commit()
            return True
        except IntegrityError:
            pass

    def remove_block(self, blocker_uid: str, blocked_uid: str):
        try:
            self.cur.execute(
                f"""DELETE FROM {self.blocks_table}
                    WHERE blocker_uid="{str(blocker_uid)}"
                    and blocked_uid="{str(blocked_uid)}"
                    """
            )
            self.db.commit()
            return True
        except IntegrityError:
            pass

    def user_is_banned(self, uid: str):
        self.cur.execute(
            f"""SELECT is_banned from {self.users_table}
                             WHERE uid="{uid}"
                             """
        )
        return self.cur.fetchall()[0][0]

    def ban_action(self, uid: str, ban=True):
        ban_translation = "TRUE" if ban else "FALSE"
        self.cur.execute(
            f"""INSERT INTO {self.users_table}
                             VALUES ("{uid}", {ban_translation})
                             ON CONFLICT (uid) DO UPDATE
                             SET is_banned=EXCLUDED.is_banned"""
        )
        self.db.commit()

    def add_cid(self, uid, cid):
        try:
            self.cur.execute(
                f"""INSERT INTO {self.cids_table}
                                VALUES ("{str(uid)}", "{str(cid)}")"""
            )
            self.db.commit()
            return True
        except IntegrityError:
            pass

    def get_cids(self, uid):
        self.cur.execute(
            f'''SELECT cid FROM {self.cids_table}
                             WHERE uid="{uid}"'''
        )
        return [item[0] for item in self.cur.fetchall()]

    def get_name(self, uid):
        self.cur.execute(
            f"""SELECT name FROM {self.users_table}
                WHERE uid="{uid}"
            """
        )
        output = self.cur.fetchall()
        if len(output):
            return output[0][0]
        else:
            return None

    def get_uid(self, cid):
        self.cur.execute(
            f'''SELECT uid FROM {self.cids_table}
                             WHERE cid="{cid}"'''
        )
        output = self.cur.fetchall()
        if len(output):
            return output[0][0]
        else:
            return None


dbh = DBHandler()
dbh.connect_db()
dbh.make_tables()
dbh.calc_cid_count()
