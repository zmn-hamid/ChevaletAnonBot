# global imports
from shortuuid import ShortUUID as suid
import random, string


def generate_cid(suid_length: int = 10) -> str:
    """
    # generates custom id
    method:
        short uuid (12 chars) +
        2 random letter
    """
    generated_id = suid().random(length=suid_length)
    element1 = random.choice(list(string.ascii_lowercase))
    element2 = random.choice(list(string.ascii_lowercase))
    return f"{generated_id}{element1}{element2}"
