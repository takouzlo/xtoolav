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
poe_bp = Blueprint('poe', __name__, url_prefix='/poe')

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

@poe_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    device_names = {
        '7': _('IP-Telefon'),
        '15': _('IP-Kamera'),
        '20': _('PTZ-Kamera'),
        '30': _('Wireless AP'),
        '60': _('4K-NDI-Kamera'),
        'custom': _('Benutzerdefiniert')
    }
    if request.method == 'POST':
        try:
            switch_power = float(request.form['switch_power'])
            device_type = request.form['device_type']
            if device_type == 'custom':
                power_per_device = float(request.form['custom_power'])
            else:
                power_per_device = float(device_type)
            available_power = switch_power * 0.85
            count = int(available_power // power_per_device)
            used = count * power_per_device
            result = {
                'available': f"{available_power:.1f}",
                'count': count,
                'warning': None
            }
            if count == 0:
                result['warning'] = _("Nicht genug Leistung für dieses Gerät.")
            elif used / switch_power > 0.8:
                result['warning'] = _("Achtung: Fast volle Auslastung.")
            selected_device_name = device_names.get(device_type, device_type)
            add_to_recent_calculations(
                _("PoE"),
                f"{switch_power}W Switch, {selected_device_name}W Gerät",
                f"{result['count']} Geräte ({result['available']}W verfügbar)"
            )
        except:
            flash(_("Fehler bei der Berechnung."), "error")
    return render_template('poe.html', result=result)