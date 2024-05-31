import asyncio
from bleak import BleakScanner

# This script scans for BLE devices for 10 seconds then prints findings
# Uses this script to identify the address of the toothbrush
# Make sure to have the toothbrush on during the scan

red = "\033[91m"
black = "\033[0m"

async def scan_BLE(time_seconds=10): # Change the number of seconds to scan for
    print(f"Scanning for {time_seconds} seconds make sure the toothbrush is on")
    devices = await BleakScanner.discover(timeout=time_seconds)
    return devices

async def main():
    devices = await scan_BLE()
    print("Found devices:")
    for device in devices:
        name = device.name or "None"
        address = device.address
        rssi = device.rssi
        if "Oral-B" in name or "Toothbrush" in name or "Oral-B Toothbrush" in name:
            print(f"{red}Name: {name}, Address: {address}, RSSI: {rssi}{black}")
        else:
            print(f"Name: {name}, Address: {address}, RSSI: {rssi}")

asyncio.run(main())
