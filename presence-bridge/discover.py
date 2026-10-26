#!/usr/bin/env python3
"""
Run this to find your SwitchBot Presence Sensor's MAC address and raw advertisement bytes.
Sit at your desk while this runs so the sensor broadcasts "occupied".

Usage:
    python discover.py
"""
import asyncio
from bleak import BleakScanner

SWITCHBOT_SERVICE_UUIDS = {
    "cba20d00-224d-11e6-9fb8-0002a5d5c51b",
    "0000fd3d-0000-1000-8000-00805f9b34fb",
}
SWITCHBOT_MFR_ID = 0x0969


async def main():
    print("Scanning for 12 seconds — stay at your desk...\n")
    devices = await BleakScanner.discover(timeout=12, return_adv=True)

    found = []
    for addr, (device, adv) in devices.items():
        name = device.name or ""
        is_sb = (
            SWITCHBOT_MFR_ID in adv.manufacturer_data
            or any(u in {s.lower() for s in adv.service_uuids}
                   for u in SWITCHBOT_SERVICE_UUIDS)
            or "switchbot" in name.lower()
        )
        if is_sb:
            found.append((addr, name, adv))

    if not found:
        print("No SwitchBot devices detected.")
        print("Make sure the sensor is powered on and within ~3 m of this laptop.")
        return

    print(f"Found {len(found)} SwitchBot device(s):\n")
    for addr, name, adv in found:
        print(f"  MAC : {addr}")
        print(f"  Name: {name or '(unnamed)'}")
        print(f"  RSSI: {adv.rssi} dBm")
        for uuid, data in adv.service_data.items():
            print(f"  Service data [{uuid[-4:]}]: {data.hex()}  bytes={list(data)}")
        for mid, data in adv.manufacturer_data.items():
            print(f"  Mfr data [0x{mid:04x}]:      {data.hex()}  bytes={list(data)}")
        print()

    print("Copy the MAC of your presence sensor into bridge.py (the MAC= line at the top).")


asyncio.run(main())
