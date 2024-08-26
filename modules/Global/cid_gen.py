# project imports
from modules.Global.database import dbh

# global imports
from shortuuid import ShortUUID as suid
import time, random, string


def generate_cid() -> str:
    """
    # generates custom id
    method:
        short uuid (10 chars) +
        1 rand letter +
        last digit from time() +
        the current cid counter
    """
    element1 = random.choice(list(string.ascii_lowercase))
    element2 = str(time.time())[-1]
    generated_id = suid().random(length=10)
    dbh.cid_count += 1
    return f"{generated_id}{element1}{element2}{dbh.cid_count}"
