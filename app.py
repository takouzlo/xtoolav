# app.py - Version finale corrigée (Freemium Pro)
from datetime import datetime, timezone
from flask import Flask, render_template, redirect, url_for, flash, request, session, make_response, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_babel import Babel, gettext as _
import os
import stripe
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# === Configuration de l'app ===
app = Flask(__name__)
app.config.from_object('config.Config')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# === Base de données ===
from models import db, User
db.init_app(app)

# === Login Manager ===
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = _("Bitte melden Sie sich an, um fortzufahren.")

# === Traduction ===
def get_locale():
    if 'lang' in session:
        return session['lang']
    if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        return current_user.language
    return request.accept_languages.best_match(['de', 'fr']) or 'de'

babel = Babel(app, locale_selector=get_locale)

# === Charger utilisateur ===
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # ✅ Fix LegacyAPIWarning

# === Créer tables si besoin ===
@app.before_request
def create_tables():
    if not os.path.exists('db.sqlite'):
        with app.app_context():
            db.create_all()

# ===================================================================
# ✅=== ENREGISTRER TOUS LES BLUEPRINTS ICI (AVANT TOUTE ROUTE) ======
# ===================================================================

free_modules = [
    ('tools.free.audio', 'audio_bp'),
    ('tools.free.converter', 'converter_bp'),
    ('tools.free.strom', 'strom_bp'),
    ('tools.free.poe', 'poe_bp'),
    ('tools.free.viewing_distance', 'viewing_distance_bp'),
    ('tools.free.netzwerktest', 'netzwerktest_bp'),
    ('tools.free.uhf', 'uhf_bp'),
    ('tools.free.projektion', 'projektion_bp'),
    ('tools.free.audio_niveau', 'audio_niveau_bp'),
    ('tools.free.waerme', 'waerme_bp'),
    ('tools.free.screen_size', 'screen_size_bp'),
    ('tools.free.ascii_decoder', 'ascii_decoder_bp'),
    ('tools.free.pinouts', 'pinouts_bp'),
    ('tools.free.netzwerk_scanner', 'netzwerk_scanner_bp')
]

for module_path, bp_name in free_modules:
    try:
        module = __import__(module_path, fromlist=[bp_name])
        blueprint = getattr(module, bp_name)
        app.register_blueprint(blueprint)
        print(f"✅ Chargé: {module_path}.{bp_name}")
    except Exception as e:
        print(f"❌ Échec chargement {module_path}: {e}")

# ===================================================================
# ✅=== Routes principales (après les Blueprints) ====================
# ===================================================================

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
        flash(_("Registrierung erfolgreich!"), "success")
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_("Sie wurden abgemeldet."), "info")
    return redirect(url_for('login'))

@app.route('/setlang/<lang>')
@login_required
def set_language(lang):
    if lang in ['de', 'fr']:
        current_user.language = lang
        db.session.commit()
        session['lang'] = lang
        login_user(current_user, force=True)
        flash(_("Sprache auf {lang} geändert").format(lang="Deutsch" if lang == 'de' else "Français"), "success")
    return redirect(request.referrer or url_for('dashboard'))

# --- DÉCORATEURS DE PLAN ---
def basic_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.plan not in ['basic', 'premium']:
            flash(_("Abonnement Basic erforderlich"), "warning")
            return redirect(url_for('pricing'))
        return f(*args, **kwargs)
    return decorated_function

def premium_only(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.plan != 'premium':
            flash(_("Abonnement Premium erforderlich"), "warning")
            return redirect(url_for('pricing'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
@login_required
def dashboard():
    tools = [
        {
            'title': _("Konverter"),
            'desc': _("Auflösungen, Kabel, NDI-Bandbreite"),
            'url': url_for('converter.index'),
            'icon': '🔄'
        },
        {
            'title': _("Audio-Rechner"),
            'desc': _("dB, Lautstärke, Empfindlichkeit"),
            'url': url_for('audio.index'),
            'icon': '🔊'
        },
        {
            'title': _("Stromrechner"),
            'desc': _("Strom, Sicherung, Kabelquerschnitt"),
            'url': url_for('strom.index'),
            'icon': '🔌'
        },
        {
            'title': _("PoE-Rechner"),
            'desc': _("Power over Ethernet (Kamera, Telefon)"),
            'url': url_for('poe.index'),
            'icon': '🔌'
        },
        {
            'title': _("Sichtabstand"),
            'desc': _("Optimale Distanz für 1080p, 4K, 8K"),
            'url': url_for('viewing_distance.index'),
            'icon': '📏'
        },
        {
            'title': _("Bilddiagonalen"),
            'desc': _("Umrechnung cm/Zoll, Breite/Höhe"),
            'url': url_for('screen_size.index'),
            'icon': '📏'
        },
        {
            'title': _("Netzwerktest"),
            'desc': _("Ping und Port-Prüfung"),
            'url': url_for('netzwerktest.index'),
            'icon': '📡'
        },
        {
            'title': "UHF",
            'desc': _("Kanäle für kabellose Mikrofone"),
            'url': url_for('uhf.index'),
            'icon': '📻'
        },
        {
            'title': _("Projektion"),
            'desc': _("Projektionsdistanz berechnen"),
            'url': url_for('projektion.index'),
            'icon': '📽️'
        },
        {
            'title': "dBu/dBV",
            'desc': _("Audio-Niveau-Konvertierung"),
            'url': url_for('audio_niveau.index'),
            'icon': '🔊'
        },
        {
            'title': _("Wärme"),
            'desc': _("Wärmeabgabe von Geräten"),
            'url': url_for('waerme.index'),
            'icon': '🌡️'
        },
        {
            'title': _("Netzwerk-Scanner"),
            'desc': _("IP, MAC, Hostname finden"),
            'url': url_for('netzwerk_scanner.index'),
            'icon': '🔍'
        },
        {
            'title': _("ASCII-Decodierer"),
            'desc': _("DEC, HEX, OCT, HTML Entity"),
            'url': url_for('ascii_decoder.index'),
            'icon': '🔣'
        }
    ]
    return render_template('dashboard.html', tools=tools)

@app.route('/export_pdf')
@login_required
@basic_required  # ✅ Protège par plan Basic+
def export_pdf():
    data = {
        'title': _("Technische Konfiguration") if current_user.language == 'de' else "Configuration technique",
        'user': current_user.username,
        'calculs': session.get('recent_calculations', []),
        'date': datetime.now().strftime("%d %B %Y à %H:%M") if current_user.language == 'fr' else datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")
    }
    html = render_template('pdf_template.html', data=data)
    try:
        import pdfkit
        config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')  # ✅ Linux
        pdf = pdfkit.from_string(html, False, configuration=config)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=xtoolav_export.pdf'
        return response
    except Exception as e:
        flash(_("Fehler beim PDF-Export: ") + str(e), "error")
        return redirect(url_for('dashboard'))

@app.route('/pricing')
@login_required
def pricing():
    return render_template('pricing.html')

@app.route('/upgrade/basic', methods=['POST'])
@login_required
def upgrade_basic():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            line_items=[{
                'price': os.getenv('STRIPE_PRICE_BASIC_ID'),
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('payment_success', _external=True),
            cancel_url=url_for('pricing', _external=True),
            metadata={'user_id': current_user.id}
        )
        return redirect(session.url, code=303)
    except Exception as e:
        flash(f"Fehler: {str(e)}", "error")
        return redirect(url_for('pricing'))

@app.route('/upgrade/premium', methods=['POST'])
@login_required
def upgrade_premium():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            line_items=[{
                'price': os.getenv('STRIPE_PRICE_PREMIUM_ID'),
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('payment_success', _external=True),
            cancel_url=url_for('pricing', _external=True),
            metadata={'user_id': current_user.id}
        )
        return redirect(session.url, code=303)
    except Exception as e:
        flash(f"Fehler: {str(e)}", "error")
        return redirect(url_for('pricing'))

@app.route('/payment_success')
@login_required
def payment_success():
    flash(_("Vielen Dank! Ihr Abonnement wurde aktiviert."), "success")
    return redirect(url_for('dashboard'))

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        print("❌ Invalid payload")
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        print("❌ Invalid signature")
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        user_id = session_obj.get('metadata', {}).get('user_id')
        if not user_id:
            print("❌ No user_id in metadata")
            return 'Missing user_id', 400
        
        user = db.session.get(User, int(user_id))  # ✅ Fix LegacyAPIWarning
        if not user:
            print(f"❌ User {user_id} not found")
            return 'User not found', 400
        
        try:
            line_items = stripe.checkout.Session.list_line_items(session_obj.id, limit=1)
            price_id = line_items.data[0].price.id
        except Exception as e:
            print(f"❌ Failed to get line items: {e}")
            return 'Failed to get price', 500

        if price_id == os.getenv('STRIPE_PRICE_BASIC_ID'):
            user.plan = 'basic'
            print(f"✅ {user.username} upgraded to BASIC")
        elif price_id == os.getenv('STRIPE_PRICE_PREMIUM_ID'):
            user.plan = 'premium'
            print(f"✅ {user.username} upgraded to PREMIUM")
        else:
            print(f"⚠️ Unknown price ID: {price_id}")
            return 'Unknown plan', 400

        db.session.commit()

    return 'OK', 200


# --- DÉCORATEUR ADMIN ---
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.username != 'admin':  # ou ajouter un champ is_admin
            flash(_("Zugriff verboten"), "error")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- ADMIN PANEL ---
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = [] # Définir users ici pour qu'il soit accessible dans le except si nécessaire
    try:
        users = User.query.all() # Récupérer les utilisateurs
        # Liste tous les paiements réussis
        events = stripe.Event.list(
            type='checkout.session.completed',
            limit=100  # Ajuste selon ton volume
        )

        payments = []
        revenue_by_month = {}

        for event in events.data:
            session = event['data']['object']
            # Convertir le timestamp en objet datetime aware UTC
            created_datetime = datetime.fromtimestamp(session.get('created'), tz=timezone.utc)
            customer_email = session.get('customer_details', {}).get('email', 'N/A')
            amount = session.get('amount_total', 0) / 100  # en euros
            currency = session.get('currency', 'EUR').upper()
            # Utiliser created_datetime pour formater la date et la clé du mois
            date_str = created_datetime.strftime('%d.%m.%Y %H:%M')
            # Clé pour le mois/an, basé sur l'objet datetime
            month_key = created_datetime.strftime('%Y-%m') 

            # Ajouter le revenu au mois correspondant
            revenue_by_month[month_key] = revenue_by_month.get(month_key, 0) + amount

            # Récupérer le plan depuis le prix
            plan = "Unknown"
            try:
                # S'assurer qu'il y a des line_items
                line_items = stripe.checkout.Session.list_line_items(session.id, limit=1)
                if line_items and line_items.data:
                    price_id = line_items.data[0].price.id
                    # Comparer avec les IDs définis dans .env
                    if price_id == os.getenv('STRIPE_PRICE_BASIC_ID'):
                        plan = "Basic"
                    elif price_id == os.getenv('STRIPE_PRICE_PREMIUM_ID'):
                        plan = "Premium"
                else:
                     print(f"Avertissement : Aucun line_item trouvé pour la session {session.id}")
            except Exception as e:
                print(f"Erreur lors de la récupération du plan pour la session {session.id} : {e}")
                # plan reste "Unknown"

            payments.append({
                'email': customer_email,
                'plan': plan,
                'amount': f"{amount:.2f} {currency}",
                'date': date_str # Utiliser la date formatée
            })
            # total_revenue est calculé après la boucle

        # Calculer le revenu total HORS de la boucle
        total_revenue = sum(revenue_by_month.values())

        # --- Préparation des données pour le graphique ---
        # Trier les mois (clés de type 'YYYY-MM')
        sorted_months = sorted(revenue_by_month.items()) 
        # Créer les labels (ex: ['Mar 2025', 'Apr 2025'])
        # On reformate la clé 'YYYY-MM' en objet datetime puis en chaîne lisible
        chart_labels = [datetime.strptime(k, '%Y-%m').strftime('%b %Y') for k, v in sorted_months]
        # Créer les valeurs (ex: [120.0, 240.5])
        chart_values = [v for k, v in sorted_months]
        # ----------------------------------------------------

        # Renvoyer toutes les données au template
        # Correction de la syntaxe : parenthèse fermante ajoutée, guillemets corrigés
        return render_template(
            'admin/panel.html',
            users=users, # Passer les utilisateurs
            payments=payments,
            total_revenue=f"{total_revenue:.2f}",
            chart_labels=chart_labels,
            chart_values=chart_values
        )

    except Exception as e:
        print(f"Erreur dans admin_panel : {e}") # Log pour débogage
        flash(f"Fehler bei Stripe-Daten: {str(e)}", "error")
        # En cas d'erreur, renvoyer un état minimal
        # S'assurer que users est défini (il l'est au début maintenant)
        return render_template(
            'admin/panel.html',
             users=users, # Passer users même en cas d'erreur
             payments=[],
             total_revenue="0.00",
             chart_labels=[],
             chart_values=[]
        )

# --- NOTIFICATIONS ADMIN ---

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = os.getenv('EMAIL_ADDRESS')
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText("""
    <html>
    <body>
        <h2>🔔 Notification xtoolav</h2>
        <p>Bonjour,</p>
        <p>Votre dernier calcul est <strong>terminé</strong>.</p>
        <a href="https://xtoolav.duckdns.org/dashboard">🔗 Voir le dashboard</a>
        <br><br>
        <small>Cordialement,<br>L'équipe xtoolav</small>
    </body>
    </html>
    """, 'html'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD'))
        server.sendmail(msg['From'], [to_email], msg.as_string())
        server.quit()
        print("📧 Email envoyé à", to_email)
    except Exception as e:
        print("❌ Erreur envoi email :", e)


@app.route('/api/send_notification', methods=['POST'])
@login_required
@premium_only  # Assure-toi que ce décorateur existe
def api_send_notification():
    try:
        data = request.get_json()
        subject = data.get('subject', 'xtoolav Notification')
        message = data.get('message', 'Default message')

        # === Envoi email (ex: Gmail) ===
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_ADDRESS')
        msg['To'] = current_user.email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login("xtoolav@gmail.com", os.getenv('EMAIL_PASSWORD'))  # ⚠️ Remplacer par vrai mot de passe
        server.sendmail("xtoolav@gmail.com", [current_user.email], msg.as_string())
        server.quit()

        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

# === API REST (Premium) ===
@app.route('/api/audio', methods=['POST'])
@login_required
@premium_only
def api_audio():
    try:
        data = request.get_json()
        sensitivity = float(data['sensitivity'])
        power = float(data['power'])
        distance = float(data['distance'])
        spl = sensitivity + 10 * math.log10(power) - 20 * math.log10(distance)
        return jsonify({
            "input": data,
            "result": {
                "spl": round(spl, 2),
                "interpretation": "Laut" if spl > 85 else "Normal"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5005, debug=True, use_reloader=False)