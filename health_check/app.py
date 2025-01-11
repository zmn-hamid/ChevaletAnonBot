import os
import socket
from flask import Flask, Response

BASE_ADDRESS = os.environ["BASE_ADDRESS"]
BOT_HEALTH_PORT = int(os.environ["BOT_HEALTH_PORT"])

app = Flask(__name__)


def bot_is_running(host, port):
    """port is open meaning the bot is running"""
    _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _sock.settimeout(3)
    result = _sock.connect_ex((host, port))
    _sock.close()
    return result == 0


@app.route(BASE_ADDRESS, methods=["GET", "HEAD"])
def health_check():
    try:
        assert bot_is_running("localhost", BOT_HEALTH_PORT)
        return Response(status=200)
    except Exception as e:
        print(f"HEALTH ERROR: {e.__class__.__name__} | {e}")
        return Response(status=500)


if __name__ == "__main__":
    app.run()
