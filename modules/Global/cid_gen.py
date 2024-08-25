# project imports
from modules.Global.database import dbh

# global imports
from shortuuid import ShortUUID as suid
import time, random, string


def generate_cid():
    element2 = str(time.time())[-1]
    element1 = random.choice(list(string.ascii_lowercase))
    generated_id = suid().random(length=10)
    dbh.cid_count += 1
    return f"{generated_id}{element1}{element2}{dbh.cid_count}"
