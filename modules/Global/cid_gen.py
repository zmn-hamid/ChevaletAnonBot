# global imports
from shortuuid import ShortUUID as suid
import time, random, string


def generate_cid() -> str:
    """
    # generates custom id
    method:
        short uuid (12 chars) +
        2 random letter
    """
    generated_id = suid().random(length=10)
    element1 = random.choice(list(string.ascii_lowercase))
    element2 = random.choice(list(string.ascii_lowercase))
    return f"{generated_id}{element1}{element2}"
