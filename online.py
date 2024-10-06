import os
import time
import random
import asyncio
import pyfiglet
from pathlib import Path
from quotexapi.config import (
    email,
    password,
    email_pass,
    user_data_dir
)
from quotexapi.stable_api import Quotex
from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI()

__author__ = "Owner HR"
__version__ = "19.0.0"
__message__ = f"""
Created By Trading With HR 2024
"""

USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"

custom_font = pyfiglet.Figlet(font="ansi_shadow")
ascii_art = custom_font.renderText("TWHR")
art_effect = f"""{ascii_art}
{__message__}
"""

print(art_effect)

client = Quotex(
    email=email,
    password=password,
    lang="pt",  # Default pt -> Português.
    email_pass=email_pass,  # If you use gmail and 2FA enabled.
    user_data_dir=user_data_dir  # Path to the playwright's cache.
)

client.debug_ws_enable = False

# This function establishes a connection to the Quotex API
async def connect(attempts=5):
    check, reason = await client.connect()
    if not check:
        attempt = 0
        while attempt <= attempts:
            if not client.check_connect():
                check, reason = await client.connect()
                if check:
                    print("Successfully reconnected!!!")
                    break
                else:
                    print("Error reconnecting.")
                    attempt += 1
                    if Path(os.path.join(".", "session.json")).is_file():
                        Path(os.path.join(".", "session.json")).unlink()
                    print(f"Trying to reconnect, {attempt} attempt at {attempts}")
            elif not check:
                attempt += 1
            else:
                break
            await asyncio.sleep(5)
        return check, reason
    print(reason)
    return check, reason


# Endpoint to test the connection
@app.get("/test_connection")
async def test_connection():
    await client.connect()
    is_connected = client.check_connect()
    client.close()
    return {"connected": is_connected}


# Endpoint to get candle data progressively
@app.get("/get_candle_progressive")
async def get_candle_progressive(asset: str = "EURJPY_otc", size: int = 10):
    check_connect, reason = await client.connect()
    if check_connect:
        offset = 3600  # in seconds
        period = 60  # in seconds [5, 10, 15, 30, 60, 120, etc.]
        end_from_time = time.time()
        list_candles = []

        for i in range(size):
            candles = await client.get_candles(asset, end_from_time, offset, period)
            if len(candles) > 0:
                end_from_time = int(candles["data"][0]["time"]) - 1
                list_candles.append(candles["data"])
        client.close()
        return {"candles": list_candles}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {reason}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
