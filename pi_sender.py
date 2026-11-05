"""
Run this on Raspberry Pi 4.
Install first: python3 -m pip install requests

IMPORTANT:
This starter sends DEMO values. Replace read_sensors() with your
actual DS18B20 / current / voltage / vibration sensor-reading code.
"""
import time, random, requests

CLOUD_URL = "https://YOUR-APP-NAME.onrender.com"
DEVICE_API_KEY = "PASTE_THE_DEVICE_API_KEY_FROM_RENDER"

def read_sensors():
    # DEMO DATA ONLY — replace these values with actual sensor readings.
    return {
        "temperature": round(35 + random.uniform(-1.5, 1.5), 1),
        "current": round(0.7 + random.uniform(-0.05, 0.05), 2),
        "voltage": round(12.0 + random.uniform(-0.2, 0.2), 1),
        "vibration": round(0.20 + random.uniform(0, 0.08), 2),
        "motor_on": True
    }

def evaluate_condition(data):
    # Example threshold rules only. Set limits based on your motor and sensor calibration.
    if data["temperature"] >= 70 or data["current"] >= 2.0 or data["vibration"] >= 1.0:
        return "CRITICAL", "Abnormal reading detected. Inspect the motor."
    if data["temperature"] >= 55 or data["current"] >= 1.5 or data["vibration"] >= 0.6:
        return "WARNING", "Motor readings are above the example normal range."
    return "NORMAL", "Motor readings are within the example limits."

def main():
    endpoint = CLOUD_URL.rstrip("/") + "/api/ingest"
    headers = {"X-API-Key": DEVICE_API_KEY, "Content-Type": "application/json"}
    while True:
        try:
            data = read_sensors()
            data["health"], data["message"] = evaluate_condition(data)
            response = requests.post(endpoint, json=data, headers=headers, timeout=10)
            print(response.status_code, response.text)
        except Exception as exc:
            print("Cloud upload failed:", exc)
        time.sleep(2)

if __name__ == "__main__":
    main()
