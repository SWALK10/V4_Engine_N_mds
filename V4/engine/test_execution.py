# Simple test script to verify execution environment
from datetime import datetime

print("Test script started.")

try:
    with open("test_output.txt", "w") as f:
        f.write(f"Test executed successfully at: {datetime.now()}\n")
    print("Test script finished successfully.")
except Exception as e:
    print(f"Test script failed: {e}")
