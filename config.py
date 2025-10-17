import os

basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, 'instance')
# Crée le dossier instance s'il n'existe pas
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

# 🔧 Configure le chemin vers wkhtmltopdf
#WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Ajuste si besoin
WKHTMLTOPDF_PATH = f'{os.path.join(basedir, "wkhtmltopdf\\bin\\wkhtmltopdf.exe")}'

# WKHTMLTOPDF_PATH = (
#     r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
#     if os.path.exists(r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe') else
#     r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
# )



class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uneMeilleur******-cle-secrete-#####+--/vvtres-securisee-mttools'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(instance_dir, "db.sqlite")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LANGUAGES = ['fr', 'de']
    WKHTMLTOPDF_PATH = WKHTMLTOPDF_PATH
