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
import math
from datetime import datetime

audio_niveau_bp = Blueprint('audio_niveau', __name__, url_prefix='/audio_niveau')

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

@audio_niveau_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    if request.method == 'POST':
        try:
            value = float(request.form['value'])
            unit = request.form['unit']
            dbu = dbv = v = mv = None
            if unit == 'dbu':
                dbu = value
                v = 0.775 * (10 ** (value / 20))
            elif unit == 'dbv':
                dbv = value
                v = 1.0 * (10 ** (value / 20))
                dbu = 20 * math.log10(v / 0.775)
            elif unit == 'v':
                v = value
                dbu = 20 * math.log10(v / 0.775)
                dbv = 20 * math.log10(v)
            elif unit == 'mv':
                v = value / 1000
                dbu = 20 * math.log10(v / 0.775)
                dbv = 20 * math.log10(v)
            mv = v * 1000
            result = {
                'dbu': f"{dbu:.2f} dBu",
                'dbv': f"{dbv:.2f} dBV",
                'v': f"{v:.3f} V",
                'mv': f"{mv:.1f} mV"
            }
            add_to_recent_calculations(_("Audio-Niveau"), f"{value} {unit.upper()}", f"{dbu:.2f} dBu")
        except:
            flash(_("Fehler bei der Konvertierung."), "error")
    return render_template('audio_niveau.html', result=result)