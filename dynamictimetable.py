import tkinter as tk
from tkinter import simpledialog
import serial
import threading
import time
from datetime import datetime

# ==== Configuration ====
PORT = "COM3"  # Change to your actual COM port
BAUD = 9600

# Teachers and their RFID tags
teachers = {
    '4900F66712CA': 'MUTHAIYA',
    '4900E5DAB7C1': 'gowtham',
    '4900F4F6D893': 'saravanan',
    '49008283CB83': 'snehaa'
}

# Days and periods
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
periods = [f'Period {i+1}' for i in range(4)]

# Start time to simulate periods
start_time = time.time()

# Custom timetable with subject names and teacher tags
timetable = {
    'Monday': {
        'Period 1': {'subject': 'DSP', 'teacher': '4900F66712CA', 'status': 'Pending'},
        'Period 2': {'subject': 'DIP', 'teacher': '4900F4F6D893', 'status': 'Pending'},
        'Period 3': {'subject': 'DC', 'teacher': '49008283CB83', 'status': 'Pending'},
        'Period 4': {'subject': 'VLSI', 'teacher': '4900E5DAB7C1', 'status': 'Pending'}
    },
    'Tuesday': {
        'Period 1': {'subject': 'DIP', 'teacher': '4900F4F6D893', 'status': 'Pending'},
        'Period 2': {'subject': 'DC', 'teacher': '49008283CB83', 'status': 'Pending'},
        'Period 3': {'subject': 'DSP', 'teacher': '4900F66712CA', 'status': 'Pending'},
        'Period 4': {'subject': 'VLSI', 'teacher': '4900E5DAB7C1', 'status': 'Pending'}
    },
    'Wednesday': {
        'Period 1': {'subject': 'DSP', 'teacher': '4900F66712CA', 'status': 'Pending'},
        'Period 2': {'subject': 'DC', 'teacher': '49008283CB83', 'status': 'Pending'},
        'Period 3': {'subject': 'VLSI', 'teacher': '4900E5DAB7C1', 'status': 'Pending'},
        'Period 4': {'subject': 'DIP', 'teacher': '4900F4F6D893', 'status': 'Pending'}
    },
    'Thursday': {
        'Period 1': {'subject': 'VLSI', 'teacher': '4900E5DAB7C1', 'status': 'Pending'},
        'Period 2': {'subject': 'DIP', 'teacher': '4900F4F6D893', 'status': 'Pending'},
        'Period 3': {'subject': 'DSP', 'teacher': '4900F66712CA', 'status': 'Pending'},
        'Period 4': {'subject': 'DC', 'teacher': '49008283CB83', 'status': 'Pending'}
    },
    'Friday': {
        'Period 1': {'subject': 'DSP', 'teacher': '4900F66712CA', 'status': 'Pending'},
        'Period 2': {'subject': 'DC', 'teacher': '49008283CB83', 'status': 'Pending'},
        'Period 3': {'subject': 'VLSI', 'teacher': '4900E5DAB7C1', 'status': 'Pending'},
        'Period 4': {'subject': 'DIP', 'teacher': '4900F4F6D893', 'status': 'Pending'}
    }
}

# ==== Tkinter GUI Setup ====
root = tk.Tk()
root.title("RFID Dynamic Timetable")
frame = tk.Frame(root)
frame.pack(padx=10, pady=10)
gui_labels = {}

selected_cell = {'day': None, 'period': None}  # To track cell clicked

# Popup reference to allow closing
edit_popup = None

def update_gui():
    for widget in frame.winfo_children():
        widget.destroy()

    tk.Label(frame, text="Day/Period", font=('Arial', 10, 'bold')).grid(row=0, column=0)
    for col, period in enumerate(periods):
        tk.Label(frame, text=period, font=('Arial', 10, 'bold')).grid(row=0, column=col+1)

    for row, day in enumerate(days, start=1):
        tk.Label(frame, text=day, font=('Arial', 10, 'bold')).grid(row=row, column=0)
        for col, period in enumerate(periods):
            data = timetable[day][period]
            teacher_name = teachers.get(data['teacher'], "Unknown")
            label_text = f"{data['subject']}\n{teacher_name}\n{data['status']}"

            # Color coding based on status
            bg_color = "white"
            if data['status'] == "Taken":
                bg_color = "#a0f0a0"  # Light green
            elif data['status'] == "Substituted":
                bg_color = "#ffff99"  # Light yellow
            elif data['status'] == "Unassigned":
                bg_color = "#f08080"  # Light red

            label = tk.Label(frame, text=label_text, width=20, relief="ridge", padx=5, pady=5, bg=bg_color)
            label.grid(row=row, column=col+1)
            label.bind("<Button-1>", lambda e, d=day, p=period: on_cell_click(d, p))
            gui_labels[(day, period)] = label

def on_cell_click(day, period):
    status = timetable[day][period]['status']
    if status in ['Taken', 'Substituted']:
        print(f"Cannot edit. {day} - {period} is already marked as {status}.")
        return

    selected_cell['day'] = day
    selected_cell['period'] = period
    global edit_popup
    edit_popup = tk.Toplevel(root)
    edit_popup.title("Edit Subject")
    tk.Label(edit_popup, text=f"Enter new subject for {day} - {period}:").pack(padx=10, pady=5)
    entry = tk.Entry(edit_popup)
    entry.pack(padx=10, pady=5)
    def save_subject():
        new_subject = entry.get()
        if new_subject:
            timetable[day][period]['subject'] = new_subject
            update_gui()
            edit_popup.destroy()
    tk.Button(edit_popup, text="Save", command=save_subject).pack(pady=5)

def update_status(day, period, new_status, new_teacher=None):
    global edit_popup
    if new_teacher:
        timetable[day][period]['teacher'] = new_teacher
    timetable[day][period]['status'] = new_status
    update_gui()
    if edit_popup:
        edit_popup.destroy()
        edit_popup = None

def wait_for_substitute(day, period, original_tag):
    print(f"⏳ Waiting 2 minutes for substitute for {day} {period}...")
    start_time_wait = time.time()
    while time.time() - start_time_wait < 90:
        if ser and ser.in_waiting:
            new_tag = ser.readline().decode().strip().replace("Tag Detected: ", "")
            if new_tag and new_tag != original_tag and new_tag in teachers:
                print(f"Substitute {teachers[new_tag]} scanned!")
                update_status(day, period, 'Substituted', new_teacher=new_tag)
                return
        time.sleep(1)
    print(" No substitute found.")
    update_status(day, period, 'Unassigned')

def current_period():
    elapsed = time.time() - start_time
    day = datetime.now().strftime('%A')

    if day not in timetable:
        return None, None

    if elapsed < 180:
        return day, 'Period 1'
    elif elapsed < 360:
        return day, 'Period 2'
    elif elapsed < 540:
        return day, 'Period 3'
    elif elapsed < 720:
        return day, 'Period 4'
    else:
        return None, None

def check_rfid():
    global edit_popup
    while True:
        try:
            if ser and ser.in_waiting:
                tag = ser.readline().decode().strip().replace("Tag Detected: ", "")
                print(f" Scanned RFID: {tag}")

                if selected_cell['day'] and selected_cell['period']:
                    day = selected_cell['day']
                    period = selected_cell['period']
                else:
                    day, period = current_period()

                if day and period:
                    assigned = timetable[day][period]['teacher']
                    status = timetable[day][period]['status']

                    if status in ['Taken', 'Substituted']:
                        print(f" {day} {period} already marked as {status}.")
                        continue

                    if tag == assigned:
                        update_status(day, period, 'Taken')
                        print(f" {teachers[tag]} has taken their period.")
                    elif tag in teachers:
                        wait_for_substitute(day, period, original_tag=assigned)
                    else:
                        print(" Unknown RFID tag.")

                    selected_cell['day'] = None
                    selected_cell['period'] = None

                else:
                    print(" Not within any class period.")
            time.sleep(1)
        except Exception as e:
            print(" Error in RFID loop:", e)

# ==== Serial Port Setup ====
try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print(f" Connected to {PORT}")
except serial.SerialException:
    print(" Could not open serial port. RFID reading will be disabled.")
    ser = None

# ==== Start GUI + RFID Thread ====
update_gui()
threading.Thread(target=check_rfid, daemon=True).start()
root.mainloop()