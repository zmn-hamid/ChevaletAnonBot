import os
import requests
from flask import Flask, Response

BASE_ADDRESS = os.environ["BASE_ADDRESS"]
BOT_HEALTH_ADDRESS = os.environ["BOT_HEALTH_ADDRESS"]
BOT_HEALTH_PORT = os.environ["BOT_HEALTH_PORT"]

app = Flask(__name__)


@app.route(BASE_ADDRESS, methods=["GET", "HEAD"])
def health_check():
    try:
        r = requests.get(f"http://0.0.0.0:{BOT_HEALTH_PORT}{BOT_HEALTH_ADDRESS}")
        if r.status_code != 200:
            raise Exception(r.status_code)
        return Response(status=200)
    except Exception as e:
        print(f"HEALTH ERROR: {e.__class__.__name__} | {e}")
        return Response(status=500)


if __name__ == "__main__":
    app.run()
