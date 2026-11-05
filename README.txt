INDUSTRIAL MOTOR CLOUD DASHBOARD — SETUP

WHAT THIS PACKAGE DOES
- A dark responsive dashboard for laptop and mobile.
- Flask web application deployed to Render.
- Raspberry Pi sends readings to the cloud using HTTPS.
- Dashboard shows temperature, current, voltage, vibration, motor status and example condition status.
- Login password protects the dashboard; API key protects device uploads.

PART 1 — DEPLOY THE DASHBOARD
1. Create a GitHub account if you do not already have one.
2. Create a NEW public or private GitHub repository named industrial-motor-dashboard.
3. Upload app.py, requirements.txt and render.yaml from this folder.
4. Sign in to https://render.com using GitHub.
5. Choose New + -> Blueprint, select your repository, and deploy.
6. Render asks for two secret values:
   DASHBOARD_PASSWORD = choose a strong password for opening the dashboard.
   DEVICE_API_KEY = create a long random key, for example using Python:
       python -c "import secrets; print(secrets.token_urlsafe(32))"
7. Save the values. Wait for deployment to finish.
8. Open the Render URL, such as https://industrial-motor-dashboard.onrender.com
9. Log in using DASHBOARD_PASSWORD.

PART 2 — CONNECT THE RASPBERRY PI
1. Copy pi_sender.py to the Raspberry Pi.
2. Install requests:
       python3 -m pip install requests
3. Edit pi_sender.py:
   CLOUD_URL = "https://YOUR-APP-NAME.onrender.com"
   DEVICE_API_KEY = "the same DEVICE_API_KEY saved in Render"
4. For a first test, leave the demo read_sensors() values unchanged.
5. Run:
       python3 pi_sender.py
6. Open the cloud dashboard and confirm that values update.
7. Stop the sender with Ctrl+C.

PART 3 — USE REAL SENSOR VALUES
Replace the DEMO DATA section in read_sensors() in pi_sender.py with your sensor code.
The function must return numeric values in these units:
  temperature: degrees Celsius
  current: amperes
  voltage: volts
  vibration: calibrated engineering units, or clearly label it as raw sensor units
  motor_on: True or False

IMPORTANT HARDWARE NOTES
- Do not connect 5V sensor outputs directly to Raspberry Pi GPIO; Pi GPIO is 3.3V only.
- Use suitable ADC/interface circuitry for analog sensors; Raspberry Pi has no built-in analog input.
- Check sensor module output range, isolation and calibration before connecting to a motor supply.
- Do not use this demo threshold logic as a certified protection system. Use correctly rated hardware protection and verify safe limits for your motor.
- This starter uses in-memory readings. Render free instances can sleep and restart; the dashboard history resets on restart. For permanent history, connect a database such as Supabase or managed PostgreSQL.
- A free Render instance may take a short time to wake after inactivity.

TROUBLESHOOTING
- Dashboard says disconnected: refresh after the Render service wakes; check deployment logs.
- Raspberry Pi gets 401: make sure DEVICE_API_KEY matches exactly.
- Dashboard stays at WAITING: ensure pi_sender.py is running and CLOUD_URL is correct.
- Do not share your dashboard password or API key publicly.
