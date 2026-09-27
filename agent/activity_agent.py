import time
from datetime import datetime

import psutil
import requests
import win32gui
import win32process


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_URL = "http://127.0.0.1:8000/events"

CHECK_INTERVAL = 1.0


# ============================================================
# WINDOWS ACTIVITY DETECTION
# ============================================================

def get_active_window():

    try:

        # Get the currently focused window
        hwnd = win32gui.GetForegroundWindow()

        if not hwnd:
            return None

        # Get window title
        window_title = win32gui.GetWindowText(hwnd)

        # Get process ID associated with the window
        _, process_id = win32process.GetWindowThreadProcessId(hwnd)

        # Get process information
        process = psutil.Process(process_id)

        process_name = process.name()

        return {
            "application": process_name,
            "window_title": window_title,
            "process_id": process_id,
        }

    except Exception as error:

        print(
            f"[ERROR] Could not read active window: {error}"
        )

        return None


# ============================================================
# EVENT CREATION
# ============================================================

def create_event(window_info):

    return {

        "timestamp": datetime.now().isoformat(),

        "application": window_info["application"],

        "event_type": "APPLICATION_FOCUS",

        "window_title": window_info["window_title"],

        "metadata": {
            "process_id": window_info["process_id"]
        },
    }


# ============================================================
# SEND EVENT TO BACKEND
# ============================================================

def send_event(event):

    try:

        response = requests.post(
            BACKEND_URL,
            json=event,
            timeout=2,
        )

        if response.status_code == 200:

            print(
                "[EVENT]",
                event["application"],
                "→",
                event["window_title"],
            )

        else:

            print(
                "[ERROR] Backend returned:",
                response.status_code,
            )

    except requests.exceptions.RequestException:

        print(
            "[ERROR] Could not connect to WorkFlowOS backend."
        )


# ============================================================
# MAIN AGENT LOOP
# ============================================================

def main():

    print()
    print("=" * 50)
    print("       WorkFlowOS Activity Agent")
    print("=" * 50)
    print()
    print("Monitoring desktop activity...")
    print()
    print("Press CTRL+C to stop.")
    print()

    previous_window = None

    while True:

        window_info = get_active_window()

        if window_info:

            current_window = (
                window_info["application"],
                window_info["window_title"],
            )

            # Only send an event when the active
            # application/window changes.
            if current_window != previous_window:

                event = create_event(window_info)

                send_event(event)

                previous_window = current_window

        time.sleep(CHECK_INTERVAL)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()