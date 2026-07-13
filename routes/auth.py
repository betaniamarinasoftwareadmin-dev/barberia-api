from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional, Any
import hashlib
from datetime import datetime, timedelta
import jwt

from database import db
from models import LoginRequest, LoginResponse, RegisterRequest, UserRole
from config import Config

router = APIRouter()
security = HTTPBearer()

# ============ FUNCIONES DE SEGURIDAD ============

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_data: Dict[str, Any]) -> str:
    payload = {
        'user_id': user_data.get('id_t1', user_data.get('id_t10', 1)),
        'username': user_data.get('usuario', user_data.get('usuario_cliente', 'admin')),
        'role': user_data.get('privilegio', 5),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

def verify_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    token = credentials.credentials
    payload = verify_token(token)
    
    # Buscar en trabajadores
    user = db.fetch_one(
        "SELECT * FROM trabajador WHERE id_t1 = %s AND activo = 1",
        (payload.get('user_id', 1),)
    )
    
    if user:
        return user
    
    # Buscar en clientes
    client = db.fetch_one(
        "SELECT * FROM cliente WHERE id_t10 = %s AND activo = 1",
        (payload.get('user_id', 1),)
    )
    
    if client:
        return {
            'id_t1': client['id_t10'],
            'ci_trabajador': client['ci_cliente'],
            'n_trabajador': client['n_cliente'],
            'a_trabajador': client['a_cliente'],
            'usuario': client['usuario_cliente'],
            'privilegio': 5,
            'activo': 1
        }
    
    # Usuario por defecto (para pruebas)
    return {
        'id_t1': payload.get('user_id', 1),
        'ci_trabajador': 12345678,
        'n_trabajador': 'Admin',
        'a_trabajador': 'Sistema',
        'usuario': payload.get('username', 'admin'),
        'cargo': 'Administrador',
        'privilegio': payload.get('role', 1),
        'activo': 1
    }

# ============ FUNCIONES DE VERIFICACIÓN DE ROLES ============

def check_role(user: Dict[str, Any], allowed_roles: list) -> bool:
    """Verifica si el usuario tiene un rol permitido"""
    return user.get('privilegio', 0) in allowed_roles

def require_admin(user: Dict[str, Any] = Depends(get_current_user)):
    """Requiere rol de administrador (privilegio = 1)"""
    if user.get('privilegio', 0) != 1:
        raise HTTPException(status_code=403, detail="Se requiere permisos de administrador")
    return user

def require_manager_or_admin(user: Dict[str, Any] = Depends(get_current_user)):
    """Requiere rol de gerente (2) o administrador (1)"""
    if user.get('privilegio', 0) not in [1, 2]:
        raise HTTPException(status_code=403, detail="Se requiere permisos de gerente o administrador")
    return user

# ============ ENDPOINTS DE AUTENTICACIÓN ============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # Buscar en trabajadores
    user = db.fetch_one(
        "SELECT * FROM trabajador WHERE usuario = %s AND activo = 1",
        (request.username,)
    )
    
    if user:
        hashed_password = hash_password(request.password)
        if user['contrasena'] == hashed_password:
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
    
    # Buscar en clientes
    client = db.fetch_one(
        "SELECT * FROM cliente WHERE usuario_cliente = %s AND activo = 1 AND bloqueado = 0",
        (request.username,)
    )
    
    if client:
        hashed_password = hash_password(request.password)
        if client['contrasena_cliente'] == hashed_password:
            token = create_token({
                'id_t10': client['id_t10'],
                'usuario_cliente': client['usuario_cliente'],
                'privilegio': 5
            })
            return LoginResponse(
                success=True,
                user={
                    'id': client['id_t10'],
                    'ci_cliente': client['ci_cliente'],
                    'nombre': f"{client['n_cliente']} {client['a_cliente']}",
                    'usuario': client['usuario_cliente'],
                    'privilegio': 5,
                    'token': token
                },
                message="Inicio de sesión exitoso"
            )
    
    # Login de prueba (sin base de datos)
    if request.username == "admin" and request.password == "admin123":
        token = create_token({
            'id_t1': 1,
            'usuario': 'admin',
            'privilegio': 1
        })
        return LoginResponse(
            success=True,
            user={
                'id': 1,
                'ci_trabajador': 12345678,
                'nombre': 'Admin Sistema',
                'usuario': 'admin',
                'cargo': 'Administrador',
                'privilegio': 1,
                'token': token
            },
            message="Inicio de sesión exitoso (modo prueba)"
        )
    
    return LoginResponse(
        success=False,
        message="Usuario o contraseña incorrectos"
    )

@router.post("/logout")
async def logout(user: Dict[str, Any] = Depends(get_current_user)):
    return {'success': True, 'message': 'Sesión cerrada exitosamente'}

@router.get("/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    return {
        'success': True,
        'user': {
            'id': user.get('id_t1', user.get('id_t10')),
            'ci': user.get('ci_trabajador', user.get('ci_cliente')),
            'nombre': f"{user.get('n_trabajador', user.get('n_cliente', ''))} {user.get('a_trabajador', user.get('a_cliente', ''))}",
            'usuario': user.get('usuario', user.get('usuario_cliente')),
            'cargo': user.get('cargo', ''),
            'privilegio': user.get('privilegio', 5)
        }
    }