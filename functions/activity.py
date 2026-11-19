
import os
from datetime import datetime


ACTIVITY_FILE = "data/activity_log.txt"


def save_activity(api_name, status, status_code):
    """Append a timestamped activity entry to the activity log file."""
    os.makedirs("data", exist_ok=True)

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(ACTIVITY_FILE, "a") as file:
        file.write(
            date + " | " + api_name + " | " +
            status + " | " + str(status_code) + "\n"
        )

    print("Activity saved successfully!")


def get_activity():
    """Read and return all lines stored in the activity log file."""
    if not os.path.exists(ACTIVITY_FILE):
        return []

    with open(ACTIVITY_FILE, "r") as file:
        activities = file.readlines()

    return activities
