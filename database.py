# database.py
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Tuple
from config import Config

class Database:
    """Conexión a la base de datos MySQL en Aiven"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establece conexión con la base de datos"""
        try:
            self.connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                pool_name="mypool",
                pool_size=5,
                pool_reset_session=True
            )
            self.cursor = self.connection.cursor(dictionary=True)
            return True
        except Error as e:
            print(f"Error de conexión a MySQL: {e}")
            return False
    
    def close(self):
        """Cierra la conexión"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params: tuple = None) -> Any:
        """Ejecuta una consulta y devuelve resultados"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return {'affected_rows': self.cursor.rowcount, 'last_insert_id': self.cursor.lastrowid}
        except Error as e:
            print(f"Error en ejecución de query: {e}")
            raise
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Ejecuta una consulta y devuelve un solo resultado"""
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """Ejecuta una consulta y devuelve todos los resultados"""
        return self.execute_query(query, params) or []
    
    def insert(self, table: str, data: Dict) -> int:
        """Inserta un registro en la tabla"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        result = self.execute_query(query, tuple(data.values()))
        return result.get('last_insert_id', 0)
    
    def update(self, table: str, data: Dict, where: Dict) -> int:
        """Actualiza registros en la tabla"""
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        where_clause = ' AND '.join([f"{k} = %s" for k in where.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = tuple(list(data.values()) + list(where.values()))
        result = self.execute_query(query, params)
        return result.get('affected_rows', 0)
    
    def delete(self, table: str, where: Dict) -> int:
        """Elimina registros de la tabla"""
        where_clause = ' AND '.join([f"{k} = %s" for k in where.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        result = self.execute_query(query, tuple(where.values()))
        return result.get('affected_rows', 0)
    
    def begin_transaction(self):
        """Inicia una transacción"""
        if self.connection:
            self.connection.start_transaction()
    
    def commit(self):
        """Confirma la transacción"""
        if self.connection:
            self.connection.commit()
    
    def rollback(self):
        """Revierte la transacción"""
        if self.connection:
            self.connection.rollback()

# Instancia global de la base de datos
db = Database()