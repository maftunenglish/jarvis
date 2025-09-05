# body/tools/system_control.py
import datetime

def get_time():
    """Returns the current system time in a friendly format."""
    now = datetime.datetime.now()
    return now.strftime("The current time is %I:%M %p.")

def get_date():
    """Returns the current system date in a friendly format."""
    now = datetime.datetime.now()
    return now.strftime("Today is %A, %B %d, %Y.")