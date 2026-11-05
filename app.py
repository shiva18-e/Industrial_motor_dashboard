import os, time, threading
from collections import deque
from functools import wraps
from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-this-secret-before-deploying")
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "change-me")
DEVICE_API_KEY = os.environ.get("DEVICE_API_KEY", "change-device-key")

lock = threading.Lock()
latest = {
    "temperature": 0.0, "current": 0.0, "voltage": 0.0,
    "vibration": 0.0, "motor_on": False, "health": "WAITING",
    "message": "Waiting for Raspberry Pi data", "updated_at": None
}
history = deque(maxlen=60)

PAGE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Industrial Motor Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
:root{--bg:#090f1b;--panel:#111c2e;--panel2:#15243a;--text:#e8eef8;--muted:#91a2bb;--cyan:#35c8e6;--green:#35d49a;--yellow:#ffc857;--red:#ff647c}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(135deg,#08101d,#0d1930);color:var(--text);font-family:Inter,Arial,sans-serif}
header{padding:22px 4%;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #22314a;background:#0b1424}
h1{font-size:clamp(20px,3vw,29px);margin:0} .sub{color:var(--muted);font-size:13px;margin-top:6px}
.wrap{max-width:1400px;margin:auto;padding:26px 4%}.top{display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.pill{padding:9px 14px;border-radius:30px;background:#1b2a40;color:var(--muted);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-top:22px}
.card{background:linear-gradient(145deg,var(--panel),var(--panel2));border:1px solid #243550;border-radius:17px;padding:20px;box-shadow:0 12px 30px #0002}
.label{color:var(--muted);font-size:13px}.value{font-size:clamp(27px,4vw,38px);font-weight:700;margin:13px 0 5px}.unit{font-size:15px;color:var(--muted);font-weight:500}
.note{font-size:12px;color:var(--muted)}.section{display:grid;grid-template-columns:1.6fr 1fr;gap:16px;margin-top:16px}
.chartbox{height:310px}.status{font-weight:700;font-size:22px;margin:14px 0}.good{color:var(--green)}.warn{color:var(--yellow)}.bad{color:var(--red)}.waiting{color:var(--cyan)}
.alert{padding:14px;border-radius:12px;background:#0c1728;border:1px solid #263750;line-height:1.5}
footer{color:var(--muted);font-size:12px;text-align:center;padding:25px}
button{background:#1c9fbe;border:0;color:#04121b;padding:10px 15px;border-radius:9px;font-weight:700;cursor:pointer}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}.section{grid-template-columns:1fr}}
@media(max-width:520px){.grid{grid-template-columns:1fr 1fr}.card{padding:14px}.value{font-size:25px}.wrap{padding:18px 4%}}
</style></head>
<body>
<header><div><h1>⚙ Industrial Motor Monitoring</h1><div class="sub">IIoT-based Predictive Maintenance System · Raspberry Pi 4</div></div>
<div class="top"><span class="pill" id="connection">Connecting…</span><button onclick="location.href='/logout'">Logout</button></div></header>
<main class="wrap">
<div class="top"><span class="pill">LIVE MONITORING</span><span class="pill">Last update: <b id="updated">--</b></span></div>
<div class="grid">
<div class="card"><div class="label">TEMPERATURE</div><div class="value"><span id="temp">--</span> <span class="unit">°C</span></div><div class="note">Motor temperature</div></div>
<div class="card"><div class="label">CURRENT</div><div class="value"><span id="current">--</span> <span class="unit">A</span></div><div class="note">Motor current</div></div>
<div class="card"><div class="label">VOLTAGE</div><div class="value"><span id="voltage">--</span> <span class="unit">V</span></div><div class="note">Supply voltage</div></div>
<div class="card"><div class="label">VIBRATION</div><div class="value"><span id="vibration">--</span> <span class="unit">units</span></div><div class="note">Raw sensor level (calibrate to mm/s if required)</div></div>
</div>
<div class="section">
<div class="card"><div class="label">LIVE SENSOR TRENDS</div><div class="chartbox"><canvas id="trend"></canvas></div></div>
<div class="card"><div class="label">MOTOR & AI CONDITION</div><div class="status" id="motor">Waiting for data</div><div class="label">AI MODULE STATUS</div><div class="status waiting" id="health">WAITING</div><div class="alert" id="message">Waiting for Raspberry Pi sensor data.</div></div>
</div>
</main><footer>Industrial IIoT Dashboard · Data refreshes automatically every 2 seconds</footer>
<script>
const labels=[], temp=[], current=[], voltage=[], vibration=[];
const ctx=document.getElementById('trend');
const chart=new Chart(ctx,{type:'line',data:{labels,datasets:[
{label:'Temperature °C',data:temp,borderColor:'#35c8e6',tension:.3},
{label:'Current A',data:current,borderColor:'#35d49a',tension:.3},
{label:'Voltage V',data:voltage,borderColor:'#ffc857',tension:.3},
{label:'Vibration',data:vibration,borderColor:'#ff647c',tension:.3}
]},options:{responsive:true,maintainAspectRatio:false,animation:false,plugins:{legend:{labels:{color:'#dce6f5'}}},scales:{x:{ticks:{color:'#91a2bb'},grid:{color:'#243550'}},y:{ticks:{color:'#91a2bb'},grid:{color:'#243550'}}}}});
function put(id,value){document.getElementById(id).textContent=value}
async function refresh(){
 try{
  const r=await fetch('/api/data'); if(!r.ok) throw new Error('No session'); const d=await r.json();
  put('temp',Number(d.temperature).toFixed(1)); put('current',Number(d.current).toFixed(2));
  put('voltage',Number(d.voltage).toFixed(1)); put('vibration',Number(d.vibration).toFixed(2));
  put('motor',d.motor_on?'MOTOR RUNNING':'MOTOR STOPPED');
  const h=String(d.health||'WAITING').toUpperCase(); put('health',h); 
  const hc=document.getElementById('health'); hc.className='status '+(h==='NORMAL'?'good':(h==='WARNING'?'warn':(h==='CRITICAL'?'bad':'waiting')));
  put('message',d.message||'No alert'); put('updated',d.updated_at||'No data yet'); put('connection','● CLOUD CONNECTED');
  const stamp=new Date().toLocaleTimeString(); labels.push(stamp);temp.push(d.temperature);current.push(d.current);voltage.push(d.voltage);vibration.push(d.vibration);
  if(labels.length>20){labels.shift();temp.shift();current.shift();voltage.shift();vibration.shift()} chart.update();
 }catch(e){put('connection','● DISCONNECTED');}
}
refresh(); setInterval(refresh,2000);
</script></body></html>
"""

LOGIN = r"""
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dashboard Login</title>
<style>body{background:#091321;color:#e8eef8;font-family:Arial;display:grid;place-items:center;min-height:100vh;margin:0}.box{background:#142238;padding:30px;border:1px solid #2b3b55;border-radius:16px;width:min(90%,360px)}input,button{width:100%;padding:12px;margin-top:12px;border-radius:8px;border:0}button{background:#35c8e6;font-weight:bold;cursor:pointer}.err{color:#ff647c}</style></head>
<body><form class="box" method="post"><h2>Motor Dashboard</h2><p>Sign in to view live motor data.</p>{% if error %}<p class="err">{{error}}</p>{% endif %}<input type="password" name="password" placeholder="Dashboard password" required><button>Login</button></form></body></html>
"""

def logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/", methods=["GET"])
@logged_in
def home():
    return render_template_string(PAGE)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        error = "Incorrect password"
    return render_template_string(LOGIN, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/ingest", methods=["POST"])
def ingest():
    if request.headers.get("X-API-Key") != DEVICE_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    required = ["temperature", "current", "voltage", "vibration"]
    if any(k not in data for k in required):
        return jsonify({"error": "Missing sensor field"}), 400
    try:
        clean = {
            "temperature": float(data["temperature"]),
            "current": float(data["current"]),
            "voltage": float(data["voltage"]),
            "vibration": float(data["vibration"]),
            "motor_on": bool(data.get("motor_on", False)),
            "health": str(data.get("health", "WAITING")).upper(),
            "message": str(data.get("message", "Sensor data received"))[:180],
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }
    except (TypeError, ValueError):
        return jsonify({"error": "Sensor values must be numeric"}), 400
    with lock:
        latest.update(clean)
        history.append(clean.copy())
    return jsonify({"ok": True})

@app.route("/api/data")
@logged_in
def get_data():
    with lock:
        return jsonify(latest)

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
