import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional
from config import Config
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.connection = None
        self.cursor = None
        self.connected = False
    
    def connect(self, retry=3, delay=2):
        for attempt in range(retry):
            try:
                if self.connection and self.connection.is_connected():
                    return True
                
                logger.info(f"Conectando a MySQL... (Intento {attempt + 1}/{retry})")
                
                if not Config.DB_HOST or not Config.DB_USER:
                    logger.warning("Configuración de base de datos incompleta")
                    return False
                
                self.connection = mysql.connector.connect(
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    port=Config.DB_PORT,
                    connection_timeout=10,
                    pool_name="mypool",
                    pool_size=3
                )
                
                if self.connection and self.connection.is_connected():
                    self.cursor = self.connection.cursor(dictionary=True)
                    self.connected = True
                    logger.info("✅ Conexión a MySQL establecida")
                    return True
                    
            except Error as e:
                logger.warning(f"Error de conexión (intento {attempt + 1}): {e}")
                if attempt < retry - 1:
                    time.sleep(delay)
                else:
                    logger.error("❌ No se pudo conectar a MySQL")
                    self.connected = False
        
        return False
    
    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection and self.connection.is_connected():
                self.connection.close()
            self.connected = False
        except Exception as e:
            logger.error(f"Error cerrando conexión: {e}")
    
    def execute_query(self, query: str, params: tuple = None) -> Any:
        if not self.connected or not self.connection or not self.connection.is_connected():
            self.connect()
        
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            return self.cursor.fetchall()
        else:
            self.connection.commit()
            return {'affected_rows': self.cursor.rowcount, 'last_insert_id': self.cursor.lastrowid}
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        return self.execute_query(query, params) or []
    
    def insert(self, table: str, data: Dict) -> int:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        result = self.execute_query(query, tuple(data.values()))
        return result.get('last_insert_id', 0)
    
    def update(self, table: str, data: Dict, where: Dict) -> int:
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        where_clause = ' AND '.join([f"{k} = %s" for k in where.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = tuple(list(data.values()) + list(where.values()))
        result = self.execute_query(query, params)
        return result.get('affected_rows', 0)
    
    def delete(self, table: str, where: Dict) -> int:
        where_clause = ' AND '.join([f"{k} = %s" for k in where.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        result = self.execute_query(query, tuple(where.values()))
        return result.get('affected_rows', 0)
    
    def begin_transaction(self):
        if self.connection and self.connection.is_connected():
            self.connection.start_transaction()
    
    def commit(self):
        if self.connection and self.connection.is_connected():
            self.connection.commit()
    
    def rollback(self):
        if self.connection and self.connection.is_connected():
            self.connection.rollback()

db = Database()