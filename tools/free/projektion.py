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

projektion_bp = Blueprint('projektion', __name__, url_prefix='/projektion')

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

@projektion_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    if request.method == 'POST':
        try:
            size = float(request.form['size'])
            ratio = float(request.form['ratio'])
            throw_str = request.form['throw']
            min_tr, max_tr = map(float, throw_str.split('-')) if '-' in throw_str else [float(throw_str)]*2
            diagonal_m = size * 0.0254
            height = diagonal_m / ((1 + ratio*ratio)**0.5)
            result = {
                'min': f"{min_tr * height * 100 / 2.54:.2f}",
                'max': f"{max_tr * height * 100 / 2.54:.2f}"
            }
            add_to_recent_calculations(
                _("Projektion"),
                f"{size}\"",
                f"{result['min']} – {result['max']} m"
            )
        except:
            flash(_("Fehler bei der Berechnung."), "error")
    return render_template('projektion.html', result=result)