# tools/free/audio.py
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

audio_bp = Blueprint('audio', __name__, url_prefix='/audio')

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

@audio_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    if request.method == 'POST':
        try:
            sensitivity = float(request.form['sensitivity'])
            power = float(request.form['power'])
            distance = float(request.form['distance'])
            spl = sensitivity + 10 * math.log10(power) - 20 * math.log10(distance)

            if spl < 60:
                interpretation = _("Leise – gut für Besprechungen")
            elif spl < 85:
                interpretation = _("Mittel – normale Konferenz")
            elif spl < 100:
                interpretation = _("Laut – Vorträge, Events")
            else:
                interpretation = _("Sehr laut – Schutz empfohlen")

            result = f"{spl:.1f} dB – {interpretation}"
            add_to_recent_calculations(
                _("Audio"),
                f"{sensitivity}dB, {power}W, {distance}m",
                result
            )
        except:
            flash(_("Fehler bei der Berechnung."), "error")
    return render_template('audio.html', result=result)