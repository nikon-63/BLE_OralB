# BLE Toothbrush 

Having never really played Bluetooth Low Energy (BLE) before, I wanted to explore this communication protocol by investigating how Oral-B toothbrushes interact with their app. Know that this communication happens over BLE. This introduction project aims to understand how BLE works and build a Python script to record the brushing session time using the information sent from the toothbrush. 

## Project Files

- **Research.ipynb** — Provides an overview of how the time messages sent from the toothbrush were discovered and understood.
- **scan_BLE.py** — Scans for BLE devices and identifies the addresses of nearby toothbrushes.
- **main.py** — A Python script that reads BLE messages from the toothbrush, displaying current brushing time and past brushing sessions.
- **main_cli.py** — The same Python script as `main.py`, but without a graphical user interface (CLI version).
