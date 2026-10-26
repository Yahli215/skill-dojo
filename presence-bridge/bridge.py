#!/usr/bin/env python3
"""
SwitchBot Presence Sensor (mmWave) → HTTP bridge for Skill Dojo.
Serves:  http://127.0.0.1:8765/presence
Returns: {"occupied": bool, "since": "<iso>", "lastSeen": "<iso>"}

Setup:
  1. Run discover.py to find your sensor's MAC address.
  2. Paste it into the MAC line below.
  3. Run this script (or install.bat to auto-start on login).
"""

import asyncio
import json
import logging
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import web
from bleak import BleakScanner

# ── CONFIGURATION ────────────────────────────────────────────────────
MAC  = "B0:E9:FE:E9:08:C9"   # SwitchBot mmWave sensor
PORT = 8765

# How long without a packet before we log a stale-sensor warning
OFFLINE_WARN_SECS = 120

# CORS: allow requests from Skill Dojo (GitHub Pages)
CORS_ORIGIN = "https://yahli215.github.io"
# ─────────────────────────────────────────────────────────────────────

# ── LOGGING ──────────────────────────────────────────────────────────
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

# ── STATE ─────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

state: dict = {
    "occupied": False,
    "since":    _now(),
    "lastSeen": None,      # None until first packet
}

# ── PARSER ────────────────────────────────────────────────────────────
# SwitchBot mmWave Presence Sensor uses service data UUID fd3d:
#   byte[0] = sequence / flags
#   byte[1] = device type
#   byte[2] = status bits  →  bit 6 (0x40) = person present
#
# If byte 2 bit 6 doesn't flip for you, the raw bytes are logged below
# so you can identify the correct byte — let the developer know and it
# can be updated to your revision's offset.

SERVICE_UUID_SUFFIX = "fd3d"
MFR_ID = 0x0969


def _parse(adv) -> bool | None:
    """Return True=occupied, False=empty, None=unrecognised packet."""
    # Primary: service data
    for uuid, data in adv.service_data.items():
        if SERVICE_UUID_SUFFIX in uuid.lower() and len(data) >= 3:
            occupied = bool(data[2] & 0x40)
            log.debug("fd3d svc %s → occupied=%s", data.hex(), occupied)
            return occupied

    # Fallback: manufacturer data 0x0969
    raw = adv.manufacturer_data.get(MFR_ID)
    if raw and len(raw) >= 3:
        occupied = bool(raw[2] & 0x40)
        log.debug("mfr 0969 %s → occupied=%s", raw.hex(), occupied)
        return occupied

    # Cannot parse — log raw so the user can identify the correct byte
    svc = {k[-4:]: v.hex() for k, v in adv.service_data.items()}
    mfr = {hex(k): v.hex() for k, v in adv.manufacturer_data.items()}
    log.warning("Cannot parse presence from %s — raw svc=%s mfr=%s",
                adv.local_name or "?", svc, mfr)
    return None


# ── BLE CALLBACK ──────────────────────────────────────────────────────
def _on_adv(device, adv):
    if device.address.upper() != MAC.upper():
        return

    occupied = _parse(adv)
    ts = _now()

    state["lastSeen"] = ts

    if occupied is None:
        return                          # packet seen but not parseable; still update lastSeen

    if occupied != state["occupied"]:
        log.info("Presence changed: %s → %s", state["occupied"], occupied)
        state["occupied"] = occupied
        state["since"] = ts


# ── HTTP SERVER ───────────────────────────────────────────────────────
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


# ── MAIN ──────────────────────────────────────────────────────────────
async def main():
    if "XX:XX" in MAC:
        log.error("Set your sensor MAC in bridge.py (run discover.py first).")
        sys.exit(1)

    log.info("Starting BLE scanner, watching %s", MAC)
    scanner = BleakScanner(_on_adv)
    await scanner.start()

    # HTTPS — needed because github.io is served over HTTPS and Chrome blocks
    # HTTP fetches to loopback (Private Network Access policy).
    cert_dir = Path(__file__).parent
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.load_cert_chain(cert_dir / "cert.pem", cert_dir / "key.pem")

    app = web.Application()
    app.router.add_route("*", "/presence", _handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", PORT, ssl=ssl_ctx).start()
    log.info("HTTPS bridge ready → https://127.0.0.1:%d/presence", PORT)
    log.info("FIRST-TIME SETUP: visit https://127.0.0.1:%d/presence in Chrome "
             "and click Advanced → Proceed to accept the self-signed cert.", PORT)

    # Heartbeat — warn if sensor goes quiet
    import datetime as dt
    while True:
        await asyncio.sleep(60)
        ls = state["lastSeen"]
        if ls:
            age = (dt.datetime.now(dt.timezone.utc)
                   - dt.datetime.fromisoformat(ls)).total_seconds()
            if age > OFFLINE_WARN_SECS:
                log.warning("No packet from %s for %.0f s — battery or range issue?",
                            MAC, age)


asyncio.run(main())
