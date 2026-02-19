from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_httpauth import HTTPBasicAuth
import os
import json
import hashlib
from pathlib import Path

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
auth = HTTPBasicAuth()

# In-memory store for remote states (similar to telemetry.py)
_remote_states = {}

@auth.verify_password
def verify(username, password):
    # Get password from environment for security
    expected_pass = os.environ.get('TELEMETRY_PASS', 'admin') 
    return username == 'admin' and password == expected_pass

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "heidi-telemetry-plus"})

@app.route('/report', methods=['POST'])
@auth.login_required
def report():
    try:
        data = request.json
        run_id = data.get("run_id")
        if not run_id:
            return jsonify({"error": "missing run_id"}), 400
        
        # Store state
        _remote_states[run_id] = data
        
        # Broadcast via WebSocket for real-time dashboard updates
        socketio.emit('state_update', data)
        
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/runs', methods=['GET'])
def list_runs():
    # This would ideally merge with local runs, but for now returns active remote ones
    return jsonify(list(_remote_states.values()))

@app.route('/status', methods=['GET'])
def get_status():
    run_id = request.args.get('run_id')
    if not run_id:
        return jsonify({"error": "missing run_id"}), 400
    
    state = _remote_states.get(run_id)
    if not state:
        return jsonify({"error": "run not found"}), 404
        
    return jsonify(state)

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    # Client wants to subscribe to a specific run
    run_id = data.get('run_id')
    print(f"Client {request.sid} subscribed to {run_id}")

def start_server(host='0.0.0.0', port=7779):
    print(f"[INFO] Starting Advanced Telemetry Server on {host}:{port}")
    socketio.run(app, host=host, port=port)

if __name__ == '__main__':
    start_server()
