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
screen_size_bp = Blueprint('screen_size', __name__, url_prefix='/screen_size')

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

@screen_size_bp.route('/', methods=['GET'])
@login_required
def index():
    return render_template('screen_size.html')

@screen_size_bp.route('/save', methods=['POST'])
@login_required
def save_calculation():
    data = request.get_json()
    diagonal = data['diagonal']
    width = data['width']
    height = data['height']
    ratio = data['ratio']
    input_str = f"Diag: {diagonal}\" ({ratio})"
    result_str = f"{diagonal}\" | {width}\" × {height}\""
    add_to_recent_calculations(_("Bildschirmgröße"), input_str, result_str)
    return {'status': 'ok'}