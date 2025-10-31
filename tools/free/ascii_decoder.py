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
import unicodedata

ascii_decoder_bp = Blueprint('ascii_decoder', __name__, url_prefix='/ascii_decoder')

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

@ascii_decoder_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    char_input = ''
    if request.method == 'POST':
        text = request.form['char'].strip()
        if len(text) != 1:
            flash(_("Bitte geben Sie genau ein Zeichen ein."), "warning")
        else:
            char_input = text
            code = ord(char_input)
            html_entities = {
                '&': '&amp;', '<': '<', '>': '>',
                '"': '&quot;', "'": '&#39;',
                '©': '&copy;', '®': '&reg;',
                '€': '&euro;', '£': '&pound;', '¥': '&yen;'
            }
            html = html_entities.get(char_input, f'&#{code};')
            try:
                name = unicodedata.name(char_input)
            except:
                name = _("Unbenannt")
            result = {
                'char': char_input, 'dec': str(code), 'hex': f"{code:X}",
                'oct': f"{code:o}", 'html': html, 'name': name
            }
            add_to_recent_calculations(
                _("ASCII-Decodierer"),
                f"'{char_input}'",
                f"DEC={code}, HEX={code:X}, HTML={html}"
            )
    return render_template('ascii_decoder.html', result=result, char_input=char_input)