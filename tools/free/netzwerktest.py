import os

from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from flask_login import login_required
from flask_babel import gettext as _
import threading
import queue
import subprocess
import socket
import re
import time
from datetime import datetime

netzwerktest_bp = Blueprint('netzwerktest', __name__, url_prefix='/netzwerktest')

@netzwerktest_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    if request.method == 'POST':
        host = request.form['host'].strip()
        port = request.form.get('port', '').strip()
        port = int(port) if port.isdigit() else None
        ping_ok = False
        ping_time = None
        try:
            proc = subprocess.run(
                ['ping', '-n', '1', host] if os.name == 'nt' else ['ping', '-c', '1', host],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5
            )
            output = proc.stdout.decode('utf-8', errors='replace') or proc.stdout.decode('cp850', errors='replace')
            if proc.returncode == 0:
                match = __import__('re').search(r'time[=<](\d+)', output)
                ping_time = match.group(1) if match else "ok"
                ping_ok = True
        except: pass
        port_open = None
        if port:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result_port = sock.connect_ex((host, port))
                port_open = (result_port == 0)
                sock.close()
            except: port_open = False
        result = {'success': ping_ok or (port_open is True), 'ping': ping_time, 'port': port, 'port_open': port_open}
    return render_template('netzwerktest.html', result=result)