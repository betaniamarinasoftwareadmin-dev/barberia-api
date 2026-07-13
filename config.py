# config.py
import os
from dotenv import load_dotenv

# Cargar .env solo para desarrollo local
# En Railway, las variables ya están en el entorno
if os.path.exists('.env'):
    load_dotenv()

class Config:
    # Base de datos (Aiven)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'barberia_db')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # Seguridad
    SECRET_KEY = os.getenv('SECRET_KEY', 'tu-clave-secreta-por-defecto')
    
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
    
    @classmethod
    def get_db_config(cls):
        """Retorna la configuración de la base de datos para conexión"""
        return {
            'host': cls.DB_HOST,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME,
            'port': cls.DB_PORT
        }