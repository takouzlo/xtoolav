# xtoolav – Votre boîte à outils AV tout-en-un 🛠️

🔧 **xtoolav** est une application web conçue pour les **techniciens audiovisuels** en salles de conférence, auditoriums et installations professionnelles.  
Elle regroupe tous les outils essentiels en un seul endroit, **multilingue**, **hors-ligne**, et **évolution vers SaaS freemium**.

> 💡 Idéal pour les chantiers, support technique, intégrateurs AV.

🌐 [Version démo](https://xtoolav.duckdns.org) | 📄 [Documentation](docs/) | 🚀 [Télécharger .exe](releases/)

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-red)](https://flask.palletsprojects.com)
[![PWA](https://img.shields.io/badge/PWA-Offline_capable-orange)](manifest.json)

---

## 🌟 Fonctionnalités

| Outil | Description |
|------|-------------|
| 🔌 **Calculateur de courant & PoE** | Puissance, fusibles, câbles, switchs |
| 🔄 **Convertisseur NDI / HDMI / Câbles** | Bande passante, résolutions |
| 🔊 **Audio Rechner (dB, dBu/dBV)** | SPL, sensibilité, niveaux pro |
| 📏 **Bilddiagonalen & Sichtabstand** | Taille écran, distance de vision |
| 📡 **Netzwerk-Scanner & Test** | Ping, port, ARP, découverte IP |
| 📶 **Dante Assistant** | Découverte automatique des périphériques Dante |
| 🔣 **ASCII Decoder** | DEC, HEX, OCT, HTML entities |
| 📋 **Historique & Export PDF** | Sauvegarde + rapport exportable |
| 🌍 **Multilingue (DE/FR)** | Interface adaptée aux techniciens germanophones |
| ☁️ **Cloud Sync (Basic+)** | Sauvegarde automatique des calculs |
| 📤 **API REST (Premium)** | Accès programmatique aux outils |
| 📧 **Notifications email (Premium)** | Envoi automatique de rapports |
| 🧑‍🔧 **Support prioritaire (Premium)** | Assistance dédiée |

---

## 🚀 Modèle Freemium

| Plan | Prix | Fonctionnalités |
|------|------|----------------|
| **Free** | Gratuit | Outils de base, historique local |
| **Basic** | 5€/mois | + Historique cloud, PDF avancé, notifications |
| **Premium** | 12€/mois | + API REST, notifications email, support prioritaire |

---

🧩 Technologies

    Backend : Python Flask

    Frontend : HTML/CSS/JS + Bootstrap 5

    Base de données : SQLite (local) / PostgreSQL (cloud)

    Authentification : Flask-Login

    Traduction : Flask-Babel

    Paiement : Stripe (abonnements)

    PDF : pdfkit + wkhtmltopdf

    Offline : Service Worker (PWA)

📦 Packaging

    ✅ .exe autonome (Windows)

    ✅ .deb (Linux)

    ✅ Docker (bientôt)

🤝 Contribution

    Toute contribution est la bienvenue !

    Ouvrez une issue ou une pull request pour :

    Ajouter un nouvel outil

    Corriger un bug

    Traduire dans une nouvelle langue

📬 Contact

    📧 xtoolav@gmail.com

    💼 Pour partenariats, licences ou version entreprise

🚀 xtoolav – L’avenir des outils AV intelligents et connectés.

## 🖥️ Déploiement

### 🌐 Accès en ligne
[xtoolav.duckdns.org](https://xtoolav.duckdns.org) – Déjà en ligne !

### 🖥️ Version locale (Windows)
Téléchargez `xtoolav.exe` dans [releases/](releases/)

### 🧑‍💻 Développement local
```bash
git clone https://github.com/takouzlo/xtoolav.git
cd xtoolav
pip install -r requirements.txt
python app.py


