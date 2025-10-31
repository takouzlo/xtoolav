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

viewing_distance_bp = Blueprint('viewing_distance', __name__, url_prefix='/viewing_distance')

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

@viewing_distance_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    if request.method == 'POST':
        try:
            size_inch = float(request.form['size'])
            resolution = request.form['resolution']
            height_m = (size_inch * 0.0254) * (9 / 16) / 1.148
            if resolution == '1080':
                min_dist = round(1.5 * height_m, 1)
                ideal = round(2.0 * height_m, 1)
                max_dist = round(2.5 * height_m, 1)
            elif resolution == '2160':
                min_dist = round(1.0 * height_m, 1)
                ideal = round(1.5 * height_m, 1)
                max_dist = round(2.0 * height_m, 1)
            else:
                min_dist = round(0.75 * height_m, 1)
                ideal = round(1.0 * height_m, 1)
                max_dist = round(1.5 * height_m, 1)
            result = {'min': min_dist, 'ideal': ideal, 'max': max_dist}
            add_to_recent_calculations(
                _("Sichtabstand"),
                f"{size_inch}\" {resolution}",
                _("Min: %(min)s m, Ideal: %(ideal)s m", min=min_dist, ideal=ideal)
            )
        except:
            flash(_("Fehler bei der Berechnung."), "error")
    return render_template('viewing_distance.html', result=result)