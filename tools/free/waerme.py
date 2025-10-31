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

waerme_bp = Blueprint('waerme', __name__, url_prefix='/waerme')

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

@waerme_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    if request.method == 'POST':
        try:
            power = float(request.form['power'])
            btu = power * 3.41
            kcal = power * 0.86
            cooling = btu * 1.2
            result = {
                'watt': f"{power:.0f} W",
                'btu': f"{btu:.0f} BTU/h",
                'kcal': f"{kcal:.0f} kcal/h",
                'cooling': f"{cooling:.0f} BTU/h"
            }
            add_to_recent_calculations(_("Wärme"), f"{power}W", f"{btu:.0f} BTU/h")
        except:
            flash(_("Fehler bei der Berechnung."), "error")
    return render_template('waerme.html', result=result)