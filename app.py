import os
import time
import signal
import sys
from datetime import datetime

running = True

def handle_shutdown(signum, frame):
    global running
    print(f"Received signal {signum}. Shutting down gracefully.", flush=True)
    running = False

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

interval = int(os.getenv("HEARTBEAT_INTERVAL", "5"))
crash_after = int(os.getenv("CRASH_AFTER", "0"))

print("Testpress worker started.", flush=True)

count = 0

while running:
    count += 1
    print(f"Heartbeat {count} - {datetime.now()}", flush=True)

    if crash_after and count >= crash_after:
        print("Simulating application crash.", flush=True)
        sys.exit(1)

    time.sleep(interval)

print("Testpress worker stopped.", flush=True)
