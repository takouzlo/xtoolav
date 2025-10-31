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

pinouts_bp = Blueprint('pinouts', __name__, url_prefix='/pinouts')

@pinouts_bp.route('/')
@login_required
def index():
    return render_template('pinouts.html')