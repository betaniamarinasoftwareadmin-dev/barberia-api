# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base de datos (Aiven)
    DB_HOST = os.getenv('DB_HOST', 'mysql-aiven-host.aivencloud.com')
    DB_USER = os.getenv('DB_USER', 'your_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
    DB_NAME = os.getenv('DB_NAME', 'barberia_db')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # Seguridad
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-for-encryption')
    
    # Variables fiscales
    IVA_PORCENTAJE = float(os.getenv('IVA_PORCENTAJE', 16.0))
    IVS_PORCENTAJE = float(os.getenv('IVS_PORCENTAJE', 0.0))
    OIA_PORCENTAJE = float(os.getenv('OIA_PORCENTAJE', 0.0))
    
    # CORS
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    # Configuración de la API
    API_VERSION = "1.0.0"
    API_TITLE = "Barbería API"
    API_DESCRIPTION = "API para el sistema de administración de Barbería BETANIA"