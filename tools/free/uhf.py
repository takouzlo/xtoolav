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
uhf_bp = Blueprint('uhf', __name__, url_prefix='/uhf')

@uhf_bp.route('/')
@login_required
def index():
    channels = [{'ch': i, 'freq': round(470 + (i - 1) * 8, 1)} for i in range(1, 51)]
    return render_template('uhf.html', uhf_channels=channels)