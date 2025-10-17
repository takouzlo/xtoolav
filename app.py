from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request, session, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_babel import Babel, gettext as _
import os
import math
import pdfkit
import subprocess
import socket
import re
import uuid
import threading
import queue
import time
import json
import unicodedata

# Importer la config et les modèles
from config import Config
from models import db, User

# Stockage global des scans (clé = session_id ou timestamp)
active_scans = {}

# Initialisation
app = Flask(__name__)
app.config.from_object(Config)

# Base de données
db.init_app(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = _("Bitte melden Sie sich an, um fortzufahren.")

config = pdfkit.configuration(wkhtmltopdf=Config.WKHTMLTOPDF_PATH)


def get_locale():
    print("🔍 Recherche de la langue...")

    if 'lang' in session:
        print(f"✅ Langue depuis session: {session['lang']}")
        return session['lang']

    try:
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            lang = current_user.language
            if lang:
                session['lang'] = lang
                print(f"✅ Langue depuis user: {lang}")
                return lang
    except Exception as e:
        print("❌ Erreur user:", e)

    default_lang = request.accept_languages.best_match(['de', 'fr']) or 'de'
    session['lang'] = default_lang
    print(f"🌍 Langue par défaut: {default_lang}")
    return default_lang


# Babel pour traduction
babel = Babel(app, locale_selector=get_locale)


# Charger l'utilisateur
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Créer les tables
@app.before_request
def create_tables():
    if not os.path.exists('db.sqlite'):
        db.create_all()


def add_to_recent_calculations(calc_type, input_data, result):
    if 'recent_calculations' not in session:
        session['recent_calculations'] = []

    session['recent_calculations'].append({
        'type': calc_type,
        'input': input_data,
        'result': result,
        'timestamp': datetime.now().strftime("%H:%M")
    })

    # Garder seulement les 10 derniers
    if len(session['recent_calculations']) > 10:
        session['recent_calculations'] = session['recent_calculations'][-10:]

    session.modified = True  # Important pour que Flask sauvegarde


# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(_("Erfolgreich eingeloggt!"), "success")
            return redirect(url_for('dashboard'))
        else:
            flash(_("Benutzername oder Passwort falsch."), "error")
    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        language = request.form.get('language', 'de')

        if User.query.filter_by(username=username).first():
            flash(_("Benutzername bereits vergeben."), "error")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash(_("E-Mail bereits registriert."), "error")
            return redirect(url_for('register'))

        user = User(username=username, email=email, language=language)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash(_("Registrierung erfolgreich! Sie können sich jetzt anmelden."), "success")
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_("Sie wurden erfolgreich abgemeldet."), "info")
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    tools = [
        {
            'title': _("Konverter"),
            'desc': _("Auflösungen, Kabel, NDI-Bandbreite"),
            'url': url_for('converter'),
            'icon': '🔄'
        },
        {
            'title': _("Audio-Rechner"),
            'desc': _("dB, Lautstärke, Empfindlichkeit"),
            'url': url_for('audio'),
            'icon': '🔊'
        },
        {
            'title': _("Pinouts"),
            'desc': _("XLR, RJ45, BNC Belegung"),
            'url': url_for('pinouts'),
            'icon': '🔌'
        },
        {
            'title': _("Stromrechner"),
            'desc': _("Strom, Sicherung, Kabelquerschnitt"),
            'url': url_for('strom'),
            'icon': '🔌'
        },
        {
            'title': _("PoE-Rechner"),
            'desc': _("Power over Ethernet (Kamera, Telefon)"),
            'url': url_for('poe'),
            'icon': '🔌'
        },
        {
            'title': _("Sichtabstand"),
            'desc': _("Optimale Distanz für 1080p, 4K, 8K"),
            'url': url_for('viewing_distance'),
            'icon': '📏'
        },
        {
            'title': _("Bilddiagonalen"),
            'desc': _("Umrechnung cm/Zoll, Breite/Höhe"),
            'url': url_for('screen_size'),
            'icon': '📏'
        },
        {
            'title': _("Netzwerktest"),
            'desc': _("Ping und Port-Prüfung"),
            'url': url_for('netzwerktest'),
            'icon': '📡'
        },
        {
            'title': "UHF",
            'desc': _("Kanäle für kabellose Mikrofone"),
            'url': url_for('uhf'),
            'icon': '📻'
        },
        {
            'title': _("Projektion"),
            'desc': _("Projektionsdistanz berechnen"),
            'url': url_for('projektion'),
            'icon': '📽️'
        },
        {
            'title': "dBu/dBV",
            'desc': _("Audio-Niveau-Konvertierung"),
            'url': url_for('audio_niveau'),
            'icon': '🔊'
        },
        {
            'title': _("Wärme"),
            'desc': _("Wärmeabgabe von Geräten"),
            'url': url_for('waerme'),
            'icon': '🌡️'
        },
        {
            'title': _("Netzwerk-Scanner"),
            'desc': _("IP, MAC, Hostname finden"),
            'url': url_for('netzwerk_scanner'),
            'icon': '🔍'
        },
        {
            'title': _("ASCII-Decodierer"),
            'desc': _("DEC, HEX, OCT, HTML Entity"),
            'url': url_for('ascii_decoder'),
            'icon': '🔣'
        },
        {
            'title': "Dante Assistant",
            'desc': _("Erkennen und verwalten Sie Dante-Geräte"),
            'url': url_for('dante_assistant'),
            'icon': '🌐'
        }
    ]
    return render_template('dashboard.html', tools=tools)


# --- À compléter : autres outils ---
@app.route('/converter', methods=['GET', 'POST'])
@login_required
def converter():
    ndi_result = None

    if request.method == 'POST':
        tool = request.form.get('tool')

        if tool == 'ndi':
            resolution = request.form['resolution']
            fps = int(request.form['fps'])
            # Approximation NDI bandwidth (Mbps)
            base_bandwidth = {
                '1280x720': 50,
                '1920x1080': 100,
                '3840x2160': 300
            }
            res_key = resolution.split()[0]  # ex: "1920x1080"
            bw = base_bandwidth.get(res_key, 100)
            adjusted_bw = bw * (fps / 30)  # scaling

            ndi_result = _(
                "Geschätzte Bandbreite: <strong>%.0f Mbps</strong><br>"
                "Empfohlenes Netzwerk: <strong>Gigabit-Ethernet</strong><br>"
                "Für 4 Kameras gleichzeitig: <strong>10GbE oder VLANs erwägen</strong>"
            ) % adjusted_bw

            add_to_recent_calculations(
                "NDI" if current_user.language == 'de' else "NDI",
                f"{resolution} @ {fps}fps",
                ndi_result
            )

    return render_template('converter.html', ndi_result=ndi_result)


@app.route('/audio', methods=['GET', 'POST'])
@login_required
def audio():
    result = None
    if request.method == 'POST':
        try:
            sensitivity = float(request.form['sensitivity'])
            power = float(request.form['power'])
            distance = float(request.form['distance'])

            # Calcul SPL
            spl = sensitivity + 10 * math.log10(power) - 20 * math.log10(distance)

            # Interprétation
            if spl < 60:
                interpretation = _("Leise – gut für Besprechungen")
            elif spl < 85:
                interpretation = _("Mittel – normale Konferenz")
            elif spl < 100:
                interpretation = _("Laut – Vorträge, Events")
            elif spl < 115:
                interpretation = _("Sehr laut – Schutz empfohlen")
            else:
                interpretation = _("Gefährlich – Gehörschutz erforderlich!")

            result = f"{spl:.1f} dB – {interpretation}"
            add_to_recent_calculations(
                _("Audio") if current_user.language == 'fr' else "Audio",
                f"{sensitivity}dB, {power}W, {distance}m",
                result
            )
        except Exception as e:
            flash(_("Fehler bei der Berechnung."), "error")

    return render_template('audio.html', result=result)


@app.route('/pinouts')
@login_required
def pinouts():
    return render_template('pinouts.html')


@app.route('/setlang/<lang>')
@login_required
def set_language(lang):
    if lang not in ['de', 'fr']:
        flash(_("Ungültige Sprache"), "error")
        return redirect(request.referrer or url_for('dashboard'))

    # Mettre à jour l'utilisateur
    current_user.language = lang
    db.session.commit()

    # Rafraîchir current_user dans la session
    login_user(current_user, force=True)  # Force reload

    # Optionnel : sauvegarder en session
    session['lang'] = lang

    flash(_("Sprache auf {lang} geändert").format(
        lang="Deutsch" if lang == 'de' else "Français"
    ), "success")

    print(f"language: {lang}")

    return redirect(request.referrer or url_for('dashboard'))


@app.route('/export_pdf')
@login_required
def export_pdf():
    # Générer le HTML à partir du template
    data = {
        'title': _("Technische Konfiguration") if current_user.language == 'de' else "Configuration technique",
        'user': current_user.username,
        'calculs': session.get('recent_calculations', []),
        'date': datetime.now().strftime("%d %B %Y à %H:%M")  # Français
        if current_user.language == 'fr' else
        datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")  # Allemand
    }
    html = render_template('pdf_template.html', data=data)

    # Générer le PDF
    try:
        pdf = pdfkit.from_string(html, False, configuration=config)
        if config is None:
            flash(_("wkhtmltopdf nicht gefunden. PDF-Export deaktiviert."), "warning")
            return redirect(url_for('dashboard'))
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=mttools_export.pdf'
        return response
    except Exception as e:
        flash(_("Fehler beim PDF-Export: ") + str(e), "error")
        return redirect(url_for('dashboard'))


@app.route('/strom', methods=['GET', 'POST'])
@login_required
def strom():
    result = None
    if request.method == 'POST':
        try:
            power = float(request.form['power'])
            voltage = float(request.form.get('voltage', 230))  # Standard DE: 230V
            phases = request.form.get('phases', 'single')

            if phases == 'single':
                current = power / voltage
                type_str = _("Einphasig")
            else:
                current = power / (voltage * 1.732)  # 3-phase
                type_str = _("Dreiphasig")

            # Recommandation câble (cuivre, <50m)
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
            phase_label = _("Dreiphasig") if phases == 'three' else _("Einphasig")
            add_to_recent_calculations(
                _("Strom") if current_user.language == 'fr' else "Strom",
                f"{power}W, {voltage}V, {phases}~{phase_label}",
                f"I = {result['current']}, Kabel: {result['cable']}, Sicherung: {result['fuse']}"
            )
        except:
            flash(_("Fehler bei der Berechnung. Bitte gültige Werte eingeben."), "error")

    return render_template('strom.html', result=result)


@app.route('/poe', methods=['GET', 'POST'])
@login_required
def poe():
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
                power_per_device = float(request.form['device_type'])

            # Réserve de 15% (recommandé)
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
                result['warning'] = _("Achtung: Fast volle Auslastung. Risiko bei Peak-Last.")

            selected_device_name = device_names.get(device_type, device_type)

            add_to_recent_calculations(
                _("PoE") if current_user.language == 'fr' else "PoE",
                f"{switch_power}W Switch, {device_type}W : {selected_device_name}W Gerät",
                f"{result['count']} Geräte ({result['available']}W verfügbar)"
            )

        except Exception as e:
            flash(_("Fehler bei der Berechnung."), "error")

    return render_template('poe.html', result=result)


@app.route('/viewing_distance', methods=['GET', 'POST'])
@login_required
def viewing_distance():
    result = None
    if request.method == 'POST':
        try:
            size_inch = float(request.form['size'])
            resolution = request.form['resolution']

            # Convertir pouces en mètres (hauteur écran)
            # Hypothèse: écran 16:9
            height_m = (size_inch * 0.0254) * (9 / 16) / 1.148  # ~facteur 16:9

            # Règles de distance
            if resolution == '1080':
                min_dist = round(1.5 * height_m, 1)
                ideal = round(2.0 * height_m, 1)
                max_dist = round(2.5 * height_m, 1)
            elif resolution == '2160':  # 4K
                min_dist = round(1.0 * height_m, 1)
                ideal = round(1.5 * height_m, 1)
                max_dist = round(2.0 * height_m, 1)
            else:  # 8K
                min_dist = round(0.75 * height_m, 1)
                ideal = round(1.0 * height_m, 1)
                max_dist = round(1.5 * height_m, 1)

            result = {
                'min': min_dist,
                'ideal': ideal,
                'max': max_dist
            }

            add_to_recent_calculations(
                _("Sichtabstand") if current_user.language == 'de' else "Distance écran",
                f"{size_inch}\" {request.form['resolution']}",
                _("Min: %(min)s m, Ideal: %(ideal)s m, Max: %(max)s m",
                  min=result['min'], ideal=result['ideal'], max=result['max'])
            )
        except:
            flash(_("Fehler bei der Berechnung."), "error")

    return render_template('viewing_distance.html', result=result)


@app.route('/netzwerktest', methods=['GET', 'POST'])
@login_required
def netzwerktest():
    result = None
    if request.method == 'POST':
        host = request.form['host'].strip()
        port = request.form.get('port', '').strip()
        port = int(port) if port.isdigit() else None

        ping_ok = False
        ping_time = None

        try:
            # Exécuter ping
            proc = subprocess.run(
                ['ping', '-n', '1', host] if os.name == 'nt' else ['ping', '-c', '1', host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )

            # 🔥 Décoder la sortie en évitant l'erreur charmap
            try:
                output = proc.stdout.decode('utf-8', errors='replace')
            except:
                output = proc.stdout.decode('cp850', errors='replace')  # Meilleur support Windows

            if proc.returncode == 0:
                # Extraire le temps
                if 'time=' in output:
                    import re
                    match = re.search(r'time[=<](\d+)', output)
                    ping_time = match.group(1) if match else "??"
                else:
                    ping_time = "ok"
                ping_ok = True
        except Exception as e:
            print(f"Ping error: {e}")
            pass

        # Port check
        port_open = None
        if port:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result_port = sock.connect_ex((host, port))
                port_open = (result_port == 0)
                sock.close()
            except:
                port_open = False

        result = {
            'success': ping_ok or (port_open is True),
            'ping': ping_time,
            'port': port,
            'port_open': port_open
        }

        # Historique
        input_str = f"{host}" + (f":{port}" if port else "")
        res_str = f"Ping: {ping_time}ms" + (f", Port {port} {'open' if port_open else 'closed'}" if port else "")
        add_to_recent_calculations(
            _("Netzwerk") if current_user.language == 'de' else "Réseau",
            input_str,
            res_str
        )

    return render_template('netzwerktest.html', result=result)


@app.route('/uhf')
@login_required
def uhf():
    # UHF Kanäle Europa (Beispiel)
    channels = []
    base = 470
    for i in range(1, 51):
        freq = base + (i - 1) * 8
        channels.append({'ch': i, 'freq': round(freq, 1)})

    return render_template('uhf.html', uhf_channels=channels)


@app.route('/projektion', methods=['GET', 'POST'])
@login_required
def projektion():
    result = None
    if request.method == 'POST':
        try:
            size = float(request.form['size'])
            ratio = float(request.form['ratio'])
            throw_str = request.form['throw']
            # Supporte "1.5" ou "1.2-1.5"
            if '-' in throw_str:
                min_tr, max_tr = map(float, throw_str.split('-'))
            else:
                min_tr = max_tr = float(throw_str)

            # Hauteur en m
            diagonal_m = size * 0.0254
            height = diagonal_m / ((1 + ratio * ratio) ** 0.5) * 1  # 16:9 etc.

            min_dist = min_tr * height * 100 / 2.54  # En m
            max_dist = max_tr * height * 100 / 2.54

            result = {
                'min': f"{min_dist:.2f}",
                'max': f"{max_dist:.2f}"
            }

            add_to_recent_calculations(
                _("Projektion") if current_user.language == 'de' else "Projection",
                f"{size}\" {('16:9' if ratio == 1.78 else '16:10')}",
                f"{result['min']} – {result['max']} m"
            )
        except:
            flash(_("Fehler bei der Berechnung."), "error")
    return render_template('projektion.html', result=result)


import math


@app.route('/audio_niveau', methods=['GET', 'POST'])
@login_required
def audio_niveau():
    result = None
    if request.method == 'POST':
        try:
            value = float(request.form['value'])
            unit = request.form['unit']
            dbu = dbv = v = mv = None

            if unit == 'dbu':
                dbu = value
                v = 0.775 * (10 ** (value / 20))
            elif unit == 'dbv':
                dbv = value
                v = 1.0 * (10 ** (value / 20))
                dbu = 20 * math.log10(v / 0.775)
            elif unit == 'v':
                v = value
                dbu = 20 * math.log10(v / 0.775)
                dbv = 20 * math.log10(v)
            elif unit == 'mv':
                v = value / 1000
                dbu = 20 * math.log10(v / 0.775)
                dbv = 20 * math.log10(v)

            mv = v * 1000

            result = {
                'dbu': f"{dbu:.2f} dBu",
                'dbv': f"{dbv:.2f} dBV",
                'v': f"{v:.3f} V",
                'mv': f"{mv:.1f} mV"
            }

            add_to_recent_calculations(
                _("Audio-Niveau"),
                f"{value} {unit.upper()}",
                f"{dbu:.2f} dBu"
            )
        except:
            flash(_("Fehler bei der Konvertierung."), "error")
    return render_template('audio_niveau.html', result=result)


@app.route('/waerme', methods=['GET', 'POST'])
@login_required
def waerme():
    result = None
    if request.method == 'POST':
        try:
            power = float(request.form['power'])
            btu = power * 3.41
            kcal = power * 0.86
            cooling = btu * 1.2  # 20% reserve

            result = {
                'watt': f"{power:.0f} W",
                'btu': f"{btu:.0f} BTU/h",
                'kcal': f"{kcal:.0f} kcal/h",
                'cooling': f"{cooling:.0f} BTU/h"
            }

            add_to_recent_calculations(
                _("Wärme") if current_user.language == 'de' else "Chaleur",
                f"{power}W",
                f"{btu:.0f} BTU/h"
            )
        except:
            flash(_("Fehler bei der Berechnung."), "error")
    return render_template('waerme.html', result=result)


@app.route('/screen_size')
@login_required
def screen_size():
    return render_template('screen_size.html')


@app.route('/save_screen_calculation', methods=['POST'])
@login_required
def save_screen_calculation():
    data = request.get_json()
    diagonal = data['diagonal']
    width = data['width']
    height = data['height']
    ratio = data['ratio']

    input_str = f"Diag: {diagonal}\" ({ratio})"

    if 'viewing' in data:
        result_str = f"{data['viewing']} | {diagonal}\""
        input_str += " + Abstand"
    else:
        result_str = f"{diagonal}\" | {width}\" × {height}\""

    add_to_recent_calculations(
        _("Bildschirmgröße") if current_user.language == 'de' else "Taille écran",
        input_str,
        result_str
    )
    return {'status': 'ok'}


@app.route('/ascii_decoder', methods=['GET', 'POST'])
@login_required
def ascii_decoder():
    result = None
    char_input = ''
    if request.method == 'POST':
        text = request.form['char'].strip()
        if len(text) != 1:
            flash(_("Bitte geben Sie genau ein Zeichen ein."), "warning")
        else:
            char_input = text
            code = ord(char_input)

            # HTML entities (liste partielle des plus courantes)
            html_entities = {
                '&': '&amp;',
                '<': '<',
                '>': '>',
                '"': '&quot;',
                "'": '&#39;',
                '©': '&copy;',
                '®': '&reg;',
                '€': '&euro;',
                '£': '&pound;',
                '¥': '&yen;'
            }
            html = html_entities.get(char_input, f'&#{code};')

            # Nom du caractère (si disponible)
            try:
                name = unicodedata.name(char_input)
            except:
                name = _("Unbenannt") if current_user.language == 'de' else "Unnamed"

            result = {
                'char': char_input,
                'dec': str(code),
                'hex': f"{code:X}",
                'oct': f"{code:o}",
                'html': html,
                'name': name
            }

            # Sauvegarder dans historique
            add_to_recent_calculations(
                _("ASCII-Decodierer"),
                f"'{char_input}'",
                f"DEC={code}, HEX={code:X}, HTML={html}"
            )
    return render_template('ascii_decoder.html', result=result, char_input=char_input)


@app.route('/dante_assistant', methods=['GET'])
@login_required
def dante_assistant():
    devices = []
    error = None

    try:
        # Exécuter dante-discover
        result = subprocess.run(
            ['dante-discover', '--list-devices', '--format=json'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                for dev in data.get('devices', []):
                    devices.append({
                        'name': dev.get('name', 'Unknown'),
                        'ip': dev.get('ip_address', '—'),
                        'mac': dev.get('mac_address', '—'),
                        'model': dev.get('model_name', '—'),
                        'firmware': dev.get('firmware_version', '—'),
                        'channels_in': dev.get('rx_channel_count', 0),
                        'channels_out': dev.get('tx_channel_count', 0)
                    })
            except json.JSONDecodeError:
                error = _("Fehler beim Lesen der JSON-Daten. Prüfen Sie die Ausgabe von dante-discover.")
        else:
            error = _("Keine Geräte gefunden oder dante-discover nicht installiert.")
    except FileNotFoundError:
        error = _("❌ dante-discover nicht gefunden. Installieren Sie Dante Controller.")
    except subprocess.TimeoutExpired:
        error = _("Zeitüberschreitung bei der Netzwerkprüfung.")
    except Exception as e:
        error = f"Fehler: {str(e)}"

    return render_template('dante_assistant.html', devices=devices, error=error)


def get_network_interfaces():
    """
    Détecte les interfaces réseau et retourne une liste de dictionnaires
    """

    def get_subnet(ip):
        parts = ip.split('.')
        return f"{'.'.join(parts[:3])}.0/24"

    interfaces = []

    # Obtenir l'IP principale via connexion
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 53))
            local_ip = s.getsockname()[0]
            interfaces.append({
                'name': 'Standard Interface',
                'ip': local_ip,
                'subnet': get_subnet(local_ip)
            })
    except:
        pass

    # Ajouter autres IPs du hostname
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[-1]:
            if ip.startswith("127"):
                continue
            subnet = get_subnet(ip)
            if not any(i['subnet'] == subnet for i in interfaces):
                name = "Wi-Fi" if "192.168.1" in ip else "Ethernet" if "10." in ip else f"Interface ({ip.split('.')[0]})"
                interfaces.append({
                    'name': name,
                    'ip': ip,
                    'subnet': subnet
                })
    except:
        pass

    return interfaces or [{'name': 'localhost', 'ip': '127.0.0.1', 'subnet': '127.0.0.0/24'}]


@app.route('/netzwerk_scanner', methods=['GET', 'POST'])
@login_required
def netzwerk_scanner():
    global active_scans

    # Générer un scan_id unique
    scan_id = session.get('scan_id', f"scan_{int(time.time())}")
    session['scan_id'] = scan_id
    print(f"🎯 scan_id: {scan_id} | in session: {session.get('scan_id')}")

    interfaces = get_network_interfaces()
    subnet = ""
    manual_subnet = ""

    if request.method == 'POST':
        selected_subnet = request.form.get('subnet', '').strip()
        manual_input = request.form.get('manual_subnet', '').strip()

        if manual_input:
            subnet = manual_input
        else:
            subnet = selected_subnet

        if not subnet:
            flash(_("Bitte Netzwerk auswählen oder eingeben."), "warning")
        else:
            try:
                network, cidr = subnet.split('/')
                cidr = int(cidr)
                base_parts = network.split('.')
                if len(base_parts) != 4 or any(not p.isdigit() for p in base_parts):
                    raise ValueError
            except:
                flash(_("Ungültiges Format. Beispiel: 192.168.1.0/24"), "error")
            else:
                # Initialiser le scan
                base_ip = '.'.join(base_parts[:3])
                end = min(
                    254 if cidr == 24 else (14 if cidr == 28 else (30 if cidr == 27 else (62 if cidr == 26 else 126))),
                    254  # Limiter pour rapidité
                )
                start = 1

                # Initialiser la file d'attente et le scan
                q = queue.Queue()
                devices = []
                progress = {'current': 0, 'total': end - start + 1, 'done': False}

                # Stocker dans active_scans
                active_scans[scan_id] = {
                    'queue': q,
                    'devices': devices,
                    'progress': progress,
                    'subnet': subnet,
                    'thread': None,
                    'started_at': datetime.now()
                }

                # Fonction de scan
                def run_scan():
                    for i in range(start, end + 1):
                        ip = f"{base_ip}.{i}"
                        try:
                            result = subprocess.run(
                                ['ping', '-n', '1', '-w', '100', ip] if os.name == 'nt' else ['ping', '-c', '1', '-W',
                                                                                              '1', ip],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                timeout=2
                            )
                            if result.returncode == 0:
                                try:
                                    hostname = socket.gethostbyaddr(ip)[0]
                                except:
                                    hostname = "Unknown"
                                mac = "—"
                                if os.name == 'nt':
                                    arp_out = subprocess.getoutput(f'arp -a | findstr {ip}')
                                    match = re.search(r'([0-9a-fA-F]{2}[-:]){5}[0-9a-fA-F]{2}', arp_out)
                                    if match:
                                        mac = match.group(0).replace('-', ':').upper()
                                else:
                                    arp_out = subprocess.getoutput(f'arp -n {ip}')
                                    match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', arp_out)
                                    if match:
                                        mac = match.group(0).upper()
                                device = {
                                    'ip': ip,
                                    'hostname': hostname,
                                    'mac': mac,
                                    'status': '🟢'
                                }
                                q.put(('device', device))


                        except:
                            pass
                        finally:
                            progress['current'] += 1
                    progress['done'] = True
                    q.put(('done', None))

                # Démarrer le thread
                thread = threading.Thread(target=run_scan, daemon=True)
                print(f"🔍 SCAN STARTED: {scan_id} | Subnet: {subnet} | IPs: {start} → {end}")
                thread.start()
                active_scans[scan_id]['thread'] = thread

                # Rediriger vers la même page pour afficher le scan en cours
                return redirect(url_for('netzwerk_scanner'))

    # Si GET ou après POST
    scan_data = active_scans.get(scan_id, {})
    devices = scan_data.get('devices', [])

    progress = scan_data.get('progress', {'current': 0, 'total': 1, 'done': True})
    scanning = not progress.get('done', True)

    # Valeurs pour le formulaire
    subnet = scan_data.get('subnet', subnet or (interfaces[0]['subnet'] if interfaces else ""))
    manual_subnet = "" if any(i['subnet'] == subnet for i in interfaces) else subnet

    return render_template(
        'netzwerk_scanner.html',
        devices=devices,
        interfaces=interfaces,
        subnet=subnet,
        manual_subnet=manual_subnet,
        scanning=scanning,
        progress=progress,
        scan_id=scan_id
    )


@app.route('/scan_updates')
@login_required
def get_scan_updates():
    scan_id = request.args.get('scan_id', '')
    print(f"🔍 POLLING: scan_id = {scan_id}")
    print(f"📊 active_scans keys: {list(active_scans.keys())}")

    if not scan_id:
        return {'new_devices': [], 'progress': {'current': 0, 'total': 1, 'done': True}}

    scan_data = active_scans.get(scan_id)
    if not scan_data:
        print(f"❌ scan_id '{scan_id}' non trouvé !")
        return {'new_devices': [], 'progress': {'current': 0, 'total': 1, 'done': True}}

    print(f"✅ scan trouvé, progress: {scan_data['progress']}")
    q = scan_data.get('queue')

    new_devices = []
    while True:
        try:
            msg_type, content = q.get_nowait()
            if msg_type == 'device':
                new_devices.append(content)
        except (queue.Empty, Exception):
            break

    progress = scan_data.get('progress', {'current': 0, 'total': 1, 'done': True})

    return {
        'new_devices': new_devices,
        'progress': progress
    }


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
