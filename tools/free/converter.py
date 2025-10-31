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

converter_bp = Blueprint('converter', __name__, url_prefix='/converter')

def add_to_recent_calculations(calc_type, input_data, result):
    if 'recent_calculations' not in session:
        session['recent_calculations'] = []
    session['recent_calculations'].append({
        'type': calc_type,
        'input': input_data,
        'result': result,
        'timestamp': datetime.now().strftime("%H:%M")
    })
    if len(session['recent_calculations']) > 10:
        session['recent_calculations'] = session['recent_calculations'][-10:]
    session.modified = True

@converter_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    ndi_result = None
    if request.method == 'POST':
        tool = request.form.get('tool')
        if tool == 'ndi':
            resolution = request.form['resolution']
            fps = int(request.form['fps'])
            base_bandwidth = {'1280x720': 50, '1920x1080': 100, '3840x2160': 300}
            res_key = resolution.split()[0]
            bw = base_bandwidth.get(res_key, 100)
            adjusted_bw = bw * (fps / 30)
            ndi_result = _(
                "Geschätzte Bandbreite: <strong>%.0f Mbps</strong><br>"
                "Empfohlenes Netzwerk: <strong>Gigabit-Ethernet</strong>"
            ) % adjusted_bw
            add_to_recent_calculations("NDI", f"{resolution} @ {fps}fps", ndi_result)
    return render_template('converter.html', ndi_result=ndi_result)