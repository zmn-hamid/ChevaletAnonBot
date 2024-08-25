import logging

from config import LOG_LEVEL

logger = logging.getLogger("SirSebastian")
log_format = logging.Formatter("[%(levelname)-9s][%(asctime)s] %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_format)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler("logs.log", "w", "utf-8")
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

logger.setLevel(LOG_LEVEL)
