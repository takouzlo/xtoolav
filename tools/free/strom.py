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
strom_bp = Blueprint('strom', __name__, url_prefix='/strom')

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

@strom_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    if request.method == 'POST':
        try:
            power = float(request.form['power'])
            voltage = float(request.form.get('voltage', 230))
            phases = request.form.get('phases', 'single')
            if phases == 'single':
                current = power / voltage
                type_str = _("Einphasig")
            else:
                current = power / (voltage * 1.732)
                type_str = _("Dreiphasig")
            if current < 10:
                cable = "1,5 mm²"
                fuse = "10 A"
            elif current < 16:
                cable = "2,5 mm²"
                fuse = "16 A"
            elif current < 20:
                cable = "4 mm²"
                fuse = "20 A"
            else:
                cable = "6 mm² oder mehr"
                fuse = "25 A+"
            result = {
                'current': f"{current:.2f} A",
                'type': type_str,
                'cable': cable,
                'fuse': fuse
            }
            add_to_recent_calculations(
                _("Strom"),
                f"{power}W, {voltage}V, {phases}",
                f"I = {result['current']}, Kabel: {result['cable']}, Sicherung: {result['fuse']}"
            )
        except:
            flash(_("Fehler bei der Berechnung."), "error")
    return render_template('strom.html', result=result)