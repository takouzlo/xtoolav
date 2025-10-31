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

netzwerk_scanner_bp = Blueprint('netzwerk_scanner', __name__, url_prefix='/netzwerk_scanner')

# Global storage
active_scans = {}

def get_network_interfaces():
    def get_subnet(ip):
        parts = ip.split('.')
        return f"{'.'.join(parts[:3])}.0/24"
    interfaces = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 53))
            local_ip = s.getsockname()[0]
            interfaces.append({'name': 'Standard Interface', 'ip': local_ip, 'subnet': get_subnet(local_ip)})
    except: pass
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[-1]:
            if not ip.startswith("127"):
                subnet = get_subnet(ip)
                if not any(i['subnet'] == subnet for i in interfaces):
                    name = "Wi-Fi" if "192.168.1" in ip else "Ethernet"
                    interfaces.append({'name': name, 'ip': ip, 'subnet': subnet})
    except: pass
    return interfaces or [{'name': 'localhost', 'ip': '127.0.0.1', 'subnet': '127.0.0.0/24'}]

@netzwerk_scanner_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
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
                return redirect(url_for('netzwerk_scanner.index'))

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



@netzwerk_scanner_bp.route('/updates')
@login_required
def updates():
    scan_id = request.args.get('scan_id', '')
    scan_data = active_scans.get(scan_id, {})
    q = scan_data.get('queue', queue.Queue())
    new_devices = []
    while True:
        try:
            msg_type, content = q.get_nowait()
            if msg_type == 'device':
                new_devices.append(content)
        except:
            break
    progress = scan_data.get('progress', {'current': 0, 'total': 1, 'done': True})
    return {'new_devices': new_devices, 'progress': progress}