# routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
import hashlib
import os
from datetime import datetime, timedelta
import jwt

from database import db
from models import LoginRequest, LoginResponse, RegisterRequest, UserRole
from config import Config

router = APIRouter()
security = HTTPBearer()

# ============ FUNCIONES DE SEGURIDAD ============

def hash_password(password: str) -> str:
    """Hashea una contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_data: Dict) -> str:
    """Crea un token JWT"""
    payload = {
        'user_id': user_data['id_t1'],
        'username': user_data['usuario'],
        'role': user_data['privilegio'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

def verify_token(token: str) -> Dict:
    """Verifica un token JWT"""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Obtiene el usuario actual desde el token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    user = db.fetch_one(
        "SELECT * FROM trabajador WHERE id_t1 = %s AND activo = 1",
        (payload['user_id'],)
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    return user

def check_role(user: Dict, allowed_roles: list) -> bool:
    """Verifica si el usuario tiene un rol permitido"""
    return user.get('privilegio') in allowed_roles

# ============ ENDPOINTS DE AUTENTICACIÓN ============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Inicia sesión de usuario"""
    # Verificar en trabajadores
    user = db.fetch_one(
        "SELECT * FROM trabajador WHERE usuario = %s AND activo = 1",
        (request.username,)
    )
    
    if user:
        # Verificar contraseña
        hashed_password = hash_password(request.password)
        if user['contrasena'] == hashed_password:
            # Registrar entrada en bitácora
            db.execute_query(
                """INSERT INTO conectividad (ci_trabajador, usuario, estacion, entrada)
                   VALUES (%s, %s, %s, NOW())""",
                (user['ci_trabajador'], user['usuario'], 'API')
            )
            
            token = create_token(user)
            return LoginResponse(
                success=True,
                user={
                    'id': user['id_t1'],
                    'ci_trabajador': user['ci_trabajador'],
                    'nombre': f"{user['n_trabajador']} {user['a_trabajador']}",
                    'usuario': user['usuario'],
                    'cargo': user['cargo'],
                    'privilegio': user['privilegio'],
                    'token': token
                },
                message="Inicio de sesión exitoso"
            )
    
    # Si no es trabajador, verificar en clientes
    client = db.fetch_one(
        "SELECT * FROM cliente WHERE usuario_cliente = %s AND activo = 1 AND bloqueado = 0",
        (request.username,)
    )
    
    if client:
        # Verificar contraseña
        hashed_password = hash_password(request.password)
        if client['contrasena_cliente'] == hashed_password:
            # Actualizar último login
            db.execute_query(
                "UPDATE cliente SET ultimo_login = NOW() WHERE ci_cliente = %s",
                (client['ci_cliente'],)
            )
            
            token = create_token({
                'id_t1': client['id_t10'],
                'usuario': client['usuario_cliente'],
                'privilegio': 5  # Visitante
            })
            
            return LoginResponse(
                success=True,
                user={
                    'id': client['id_t10'],
                    'ci_cliente': client['ci_cliente'],
                    'nombre': f"{client['n_cliente']} {client['a_cliente']}",
                    'usuario': client['usuario_cliente'],
                    'privilegio': 5,  # Visitante
                    'token': token
                },
                message="Inicio de sesión exitoso"
            )
    
    # Falló la autenticación
    return LoginResponse(
        success=False,
        message="Usuario o contraseña incorrectos"
    )

@router.post("/register")
async def register_user(request: RegisterRequest):
    """Registra un nuevo usuario (trabajador)"""
    # Verificar si el usuario ya existe
    existing = db.fetch_one(
        "SELECT * FROM trabajador WHERE usuario = %s OR ci_trabajador = %s",
        (request.usuario, request.ci_trabajador)
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="El usuario o cédula ya están registrados"
        )
    
    # Crear nuevo usuario
    hashed_password = hash_password(request.contrasena)
    
    user_data = {
        'ci_trabajador': request.ci_trabajador,
        'n_trabajador': request.n_trabajador,
        'a_trabajador': request.a_trabajador,
        'usuario': request.usuario,
        'cargo': request.cargo,
        'contrasena': hashed_password,
        'correoe': request.correoe,
        'privilegio': request.privilegio.value if hasattr(request.privilegio, 'value') else request.privilegio,
        'dir_trabajador': request.dir_trabajador,
        'codarea1': request.codarea1,
        'telefono1': request.telefono1,
        'es_ext': 0
    }
    
    user_id = db.insert('trabajador', user_data)
    
    if user_id:
        return {
            'success': True,
            'message': 'Usuario registrado exitosamente',
            'user_id': user_id
        }
    else:
        raise HTTPException(status_code=500, detail="Error al registrar usuario")

@router.post("/logout")
async def logout(user: Dict = Depends(get_current_user)):
    """Cierra sesión del usuario"""
    # Registrar salida en bitácora
    db.execute_query(
        """UPDATE conectividad 
           SET salida = NOW() 
           WHERE ci_trabajador = %s AND salida IS NULL 
           ORDER BY id_t0 DESC LIMIT 1""",
        (user['ci_trabajador'],)
    )
    
    return {
        'success': True,
        'message': 'Sesión cerrada exitosamente'
    }

@router.get("/me")
async def get_me(user: Dict = Depends(get_current_user)):
    """Obtiene la información del usuario actual"""
    return {
        'success': True,
        'user': {
            'id': user['id_t1'],
            'ci_trabajador': user['ci_trabajador'],
            'nombre': f"{user['n_trabajador']} {user['a_trabajador']}",
            'usuario': user['usuario'],
            'cargo': user['cargo'],
            'privilegio': user['privilegio'],
            'correo': user['correoe']
        }
    }