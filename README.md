# xtoolav – Votre boîte à outils AV tout-en-un

🔧 **xtoolav** est une application web conçue pour les **techniciens audiovisuels** en salles de conférence, auditoriums et installations professionnelles.  
Elle regroupe tous les outils essentiels en un seul endroit, multilingue, hors-ligne, et évolutif vers un modèle **SaaS freemium**.

> 💡 Idéal pour les chantiers, support technique, intégrateurs AV.

🌐 [Version démo](https://demo.xtoolav.com) | 📄 [Documentation](docs/) | 🚀 [Télécharger .exe](releases/)

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

---

## 🚀 Modèle Freemium

| Plan | Fonctionnalités |
|------|----------------|
| **Free** | Accès de base (calculatrices, convertisseurs) |
| **Basic (5€/mois)** | + Historique, PDF, réseau, notifications |
| **Premium (12€/mois)** | + Sync cloud, rapports avancés, API, support prioritaire |

---

## 🖥️ Mode d'emploi

```bash
git clone https://github.com/takouzlo/xtoolav.git
cd xtoolav
pip install -r requirements.txt
python app.py