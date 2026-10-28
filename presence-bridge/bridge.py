#!/usr/bin/env python3
"""
SwitchBot Presence Sensor (mmWave) -> HTTP bridge for Skill Dojo.
Reads BLE advertisements directly — no hub required.
Serves:  http://127.0.0.1:8765/presence
Returns: {"occupied": bool, "since": "<iso>", "lastSeen": "<iso>", "lastOccupied": "<iso>"}

Occupancy encoding in manufacturer data (MFR_ID 0x0969), byte[8]:
  Even value (0x00, 0x02, 0x04 ...) = OCCUPIED
  Odd value  (0x01, 0x03, 0x05 ...) = UNOCCUPIED
  byte[8] is a transition counter; parity flips on each state change.

The sensor's unoccupied timer (set to ~3 min in app) means BLE goes odd after
~3 min of stillness. The page uses a 4-min stale window so the session stays
alive through brief inactivity.

False-positive filter: the sensor occasionally triggers "occupied" from air
movement, fans, etc.  We only accept a new occupied run as real presence after
OCC_CONFIRM_SECS seconds of continuous occupied packets.  Once confirmed, every
subsequent occupied packet refreshes lastOccupied normally (no extra delay).
A single unoccupied packet immediately resets the confirmation window.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import web
from bleak import BleakScanner

# ── CONFIGURATION ────────────────────────────────────────────────────
MAC  = "B0:E9:FE:E9:08:C9"
PORT = 8765
OFFLINE_WARN_SECS = 120
CORS_ORIGIN = "https://yahli215.github.io"
OCC_CONFIRM_SECS = 10   # seconds of continuous occupied before lastOccupied updates
# ─────────────────────────────────────────────────────────────────────

log_file = Path(__file__).parent / "bridge.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("presence-bridge")

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

state: dict = {
    "occupied":     False,
    "since":        _now(),
    "lastSeen":     None,
    "lastOccupied": None,
}

MFR_ID = 0x0969
_occ_run_start: float | None = None   # monotonic time when current occupied run began
_occ_confirmed: bool = False           # True once the run has lasted OCC_CONFIRM_SECS

def _parse(adv) -> bool | None:
    raw = adv.manufacturer_data.get(MFR_ID)
    if raw and len(raw) >= 9:
        occupied = not bool(raw[8] & 0x01)   # even = occupied, odd = unoccupied
        log.info("mfr[8]=0x%02x -> occupied=%s  (full: %s)", raw[8], occupied, raw.hex())
        return occupied
    return None

def _on_adv(device, adv):
    global _occ_run_start, _occ_confirmed
    if device.address.upper() != MAC.upper():
        return
    occupied = _parse(adv)
    ts = _now()
    state["lastSeen"] = ts
    if occupied is None:
        return

    now = time.monotonic()
    if occupied:
        if _occ_run_start is None:
            # Start of a new occupied run — don't confirm yet
            _occ_run_start = now
            _occ_confirmed = False
            log.info("Occupied run started — waiting %ds to confirm", OCC_CONFIRM_SECS)
        elif not _occ_confirmed and (now - _occ_run_start) >= OCC_CONFIRM_SECS:
            _occ_confirmed = True
            log.info("Occupied confirmed after %.0fs — accepting as real presence",
                     now - _occ_run_start)
        if _occ_confirmed:
            state["lastOccupied"] = ts
    else:
        if _occ_run_start is not None:
            log.info("Occupied run ended after %.0fs (%s)",
                     now - _occ_run_start,
                     "confirmed" if _occ_confirmed else "NOT confirmed — treated as false positive")
        _occ_run_start = None
        _occ_confirmed = False

    if occupied != state["occupied"]:
        log.info("Presence changed: %s -> %s", state["occupied"], occupied)
        state["occupied"] = occupied
        state["since"] = ts

_CORS_HEADERS = {
    "Access-Control-Allow-Origin":          CORS_ORIGIN,
    "Access-Control-Allow-Methods":         "GET, OPTIONS",
    "Access-Control-Allow-Headers":         "*",
    "Access-Control-Allow-Private-Network": "true",
    "Cache-Control":                        "no-store",
}

async def _handle(req: web.Request) -> web.Response:
    if req.method == "OPTIONS":
        return web.Response(status=204, headers=_CORS_HEADERS)
    return web.Response(
        text=json.dumps(state),
        content_type="application/json",
        headers=_CORS_HEADERS,
    )

async def main():
    log.info("Starting BLE scanner, watching %s", MAC)
    scanner = BleakScanner(_on_adv)
    await scanner.start()

    app = web.Application()
    app.router.add_route("*", "/presence", _handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", PORT).start()
    log.info("Bridge ready -> http://127.0.0.1:%d/presence", PORT)

    import datetime as dt
    while True:
        await asyncio.sleep(60)
        ls = state["lastSeen"]
        if ls:
            age = (dt.datetime.now(dt.timezone.utc)
                   - dt.datetime.fromisoformat(ls)).total_seconds()
            if age > OFFLINE_WARN_SECS:
                log.warning("No packet from %s for %.0f s", MAC, age)

asyncio.run(main())
