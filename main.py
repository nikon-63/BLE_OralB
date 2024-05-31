# Imports 
import asyncio
import threading
from bleak import BleakClient, BleakError
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
from datetime import datetime
import json
import os

# Notification characteristics and toothbrush address found from testing
notify_characteristics = [
    "a0f0ff08-5047-4d53-8208-4f72616c2d42"
]

# For chnaging the toothbrush address for testing
# 1 == Small 
# 2 == Big
toothbrush_wanted = 1

if toothbrush_wanted == 1:
    toothbrush_address = "212B5F11-23E1-ED1E-6CE0-2F09CE4E619C"
else:
    toothbrush_address = "B106DC31-05CA-292E-C97F-8FB7A9F36404"


# For logging the brushing data
brushing_sessions = []
session_end_times = []
last_notification_time = None
previous_time_value = 0
total_time = 0

# File path for storing brushing data
data_file_path = 'brushing_data.json'

# Load brushing data from file
def load_brushing_data():
    global brushing_sessions, session_end_times
    if os.path.exists(data_file_path):
        with open(data_file_path, 'r') as file:
            data = json.load(file)
            brushing_sessions = data.get('brushing_sessions', [])
            session_end_times = data.get('session_end_times', [])

# Save brushing data to file
def save_brushing_data():
    data = {
        'brushing_sessions': brushing_sessions,
        'session_end_times': session_end_times
    }
    with open(data_file_path, 'w') as file:
        json.dump(data, file)

def time_value(raw_data): # Function that takes the value from a0f0ff08-5047-4d53-8208-4f72616c2d42 and turns it into the time
    data = raw_data / 256
    return round(data)

def numeric(data): # Takes the data from a0f0ff08-5047-4d53-8208-4f72616c2d42 in bytes and turns into number
    return int.from_bytes(data, byteorder='little')

# For handling the notifications from the toothbrush and calculating the time
async def BLE_notification(sender, data):
    global last_notification_time, current_session_max_time, previous_time_value, total_time
    
    # Getting the time value from the data
    char_uuid = sender.uuid
    numeric_value = numeric(data)
    current_time_value = time_value(numeric_value)

    # The toothbrush resets its timer after 60 seconds so this handles that
    if current_time_value < previous_time_value:
        # Handle the wrap-around by adding the time left in the previous period to the current time value
        total_time += (60 - previous_time_value) + current_time_value
    else:
        # Normal increment
        total_time += current_time_value - previous_time_value

    previous_time_value = current_time_value

    # Printing the data for testing and to check its working
    print(f"Notification from {char_uuid}: Byte value: {data} Numerical value: {numeric_value} Calculated time value: {current_time_value} Total time: {total_time}")

    last_notification_time = asyncio.get_event_loop().time()

    if total_time > current_session_max_time:
        current_session_max_time = total_time

    # Updates the UI
    update_time(total_time)

# Checks to see if the toothbrush is still connected handles stopping the session if it is not
async def BLE_monitor(client):
    global last_notification_time, current_session_max_time, total_time, previous_time_value

    # checks if the toothbrush is still connected
    while client.is_connected:
        if last_notification_time is not None:
            # If there is no notification for 30 seconds it stops the session and logs the data
            elapsed_time = asyncio.get_event_loop().time() - last_notification_time
            if elapsed_time > 30:
                print("No notification for 30 seconds. Stopping the current session.")
                if current_session_max_time > 0:
                    # Log the session only if it's greater than 0
                    brushing_sessions.append(current_session_max_time)
                    session_end_times.append(datetime.now().strftime("%H:%M:%S"))
                    print(f"Brushing session ended. Duration: {current_session_max_time} seconds")
                    print(f"Brushing sessions: {brushing_sessions}")
                    print(f"Session end times: {session_end_times}")
                    # Save data to file
                    save_brushing_data()
                    # Update the bar chart with the new session
                    bar_chart()
                # Reset variables
                current_session_max_time = 0
                total_time = 0
                previous_time_value = 0
                last_notification_time = None
        await asyncio.sleep(1)

# Connects the toothbrush 
async def BLE_connect(address):
    global current_session_max_time, total_time, previous_time_value, last_notification_time
    while True:
        try:
            async with BleakClient(address) as client:
                current_session_max_time = 0
                total_time = 0
                previous_time_value = 0
                last_notification_time = None
                
                for char_uuid in notify_characteristics: # Starts listening for notifications from the toothbrush if it is connected
                    await client.start_notify(char_uuid, BLE_notification)
                print(f"Toothbrush connected. Monitoring for brushing session...")

                await BLE_monitor(client) # Starts the BLE_monitor function to check if the toothbrush is still connected or 30 seconds have passed

                if client.is_connected: 
                    try:
                        for char_uuid in notify_characteristics:
                            await client.stop_notify(char_uuid) 
                    except Exception as e:
                        print(f"Error while stopping notifications: {e}")

                if current_session_max_time > 0:
                    brushing_sessions.append(current_session_max_time) # Logs the session
                    session_end_times.append(datetime.now().strftime("%H:%M:%S"))  # Log the end time of the session
                    print(f"Brushing session ended. Duration: {current_session_max_time} seconds")
                    print(f"Brushing sessions: {brushing_sessions}")
                    print(f"Session end times: {session_end_times}")
                    save_brushing_data()
                    # Update the bar chart with the new brushing session 
                    bar_chart()

        except BleakError as e: # If the toothbrush disconnects it will try to reconnect and print an error
            print(f"Disconnected or failed to connect, retrying... Error: {e}")
            await asyncio.sleep(5)

async def main():
    await BLE_connect(toothbrush_address)

def run_asyncio_loop():
    asyncio.run(main())

def update_time(time_value): # Function takes the current brushing session time and updates the UI
    minutes, seconds = divmod(time_value, 60) # Splits in to minutes and seconds
    time_formatted = f"{minutes:02}:{seconds:02}"
    current_time_var.set(time_formatted)
    circle_canvas.itemconfig(current_time_text, text=f"Current Time\n{time_formatted}") # Updates the UI

def bar_chart(): # Sends the data to the bar chart after a brushing session
    ax.clear() 
    bars = ax.bar(session_end_times, brushing_sessions, color='blue')
    ax.set_title("Brushing Sessions")
    ax.set_xlabel("Brushing Session")
    ax.set_ylabel("Time (seconds)")
    for bar in bars: 
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.05, int(yval), ha='center', va='bottom')
    canvas.draw()

# For the UI
root = tk.Tk()
root.title("Toothbrush Monitoring")

# Loads data from the json file so past data is showen
load_brushing_data()

# Current Time Frame
current_time_frame = tk.Frame(root)
current_time_frame.pack(side=tk.LEFT, padx=20, pady=20)
current_time_var = tk.StringVar()
current_time_var.set("00:00")

circle_canvas = tk.Canvas(current_time_frame, width=300, height=300)
circle_canvas.create_oval(10, 10, 290, 290, outline="black")
current_time_text = circle_canvas.create_text(150, 150, text="Current Time\n00:00", font=("Helvetica", 24), justify="center")
circle_canvas.pack()

# Chart
fig = Figure(figsize=(5, 4), dpi=100)
ax = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.RIGHT, padx=20, pady=20)

# Loading past data
bar_chart()

asyncio_thread = threading.Thread(target=run_asyncio_loop)
asyncio_thread.start()

root.mainloop()

