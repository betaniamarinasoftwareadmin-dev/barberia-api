# routes/users.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional

from database import db
from models import UserCreate, UserUpdate, UserRole
from routes.auth import get_current_user, check_role, hash_password

router = APIRouter()

# ============ MIDDLEWARE DE ROLES ============

def require_admin(user: Dict = Depends(get_current_user)):
    """Requiere rol de administrador"""
    if user['privilegio'] != 1:  # 1 = Admin
        raise HTTPException(status_code=403, detail="Se requiere permisos de administrador")
    return user

def require_manager_or_admin(user: Dict = Depends(get_current_user)):
    """Requiere rol de gerente o administrador"""
    if user['privilegio'] not in [1, 2]:  # 1=Admin, 2=Gerente
        raise HTTPException(status_code=403, detail="Se requiere permisos de gerente o administrador")
    return user

# ============ ENDPOINTS ============

@router.get("/")
async def get_users(
    user: Dict = Depends(require_manager_or_admin)
) -> List[Dict]:
    """Obtiene todos los usuarios trabajadores"""
    users = db.fetch_all(
        "SELECT id_t1, ci_trabajador, n_trabajador, a_trabajador, usuario, cargo, correoe, privilegio, activo FROM trabajador ORDER BY n_trabajador"
    )
    return users

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Obtiene un usuario por ID"""
    user_data = db.fetch_one(
        "SELECT * FROM trabajador WHERE id_t1 = %s",
        (user_id,)
    )
    
    if not user_data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # No devolver la contraseña
    user_data.pop('contrasena', None)
    return user_data

@router.post("/")
async def create_user(
    user_data: UserCreate,
    admin: Dict = Depends(require_admin)
) -> Dict:
    """Crea un nuevo usuario"""
    # Verificar si el usuario ya existe
    existing = db.fetch_one(
        "SELECT * FROM trabajador WHERE usuario = %s OR ci_trabajador = %s",
        (user_data.usuario, user_data.ci_trabajador)
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="El usuario o cédula ya están registrados"
        )
    
    hashed_password = hash_password(user_data.contrasena)
    
    data = {
        'ci_trabajador': user_data.ci_trabajador,
        'n_trabajador': user_data.n_trabajador,
        'a_trabajador': user_data.a_trabajador,
        'usuario': user_data.usuario,
        'cargo': user_data.cargo,
        'contrasena': hashed_password,
        'correoe': user_data.correoe,
        'privilegio': user_data.privilegio.value if hasattr(user_data.privilegio, 'value') else user_data.privilegio,
        'dir_trabajador': user_data.dir_trabajador,
        'codarea1': user_data.codarea1,
        'telefono1': user_data.telefono1,
        'codarea2': user_data.codarea2,
        'telefono2': user_data.telefono2,
        'es_ext': 1 if user_data.es_ext else 0
    }
    
    user_id = db.insert('trabajador', data)
    
    return {
        'success': True,
        'message': 'Usuario creado exitosamente',
        'user_id': user_id
    }

@router.put("/{user_id}")
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    admin: Dict = Depends(require_admin)
) -> Dict:
    """Actualiza un usuario"""
    # Verificar que existe
    existing = db.fetch_one(
        "SELECT * FROM trabajador WHERE id_t1 = %s",
        (user_id,)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Preparar datos para actualizar
    data = {}
    if update_data.n_trabajador is not None:
        data['n_trabajador'] = update_data.n_trabajador
    if update_data.a_trabajador is not None:
        data['a_trabajador'] = update_data.a_trabajador
    if update_data.cargo is not None:
        data['cargo'] = update_data.cargo
    if update_data.correoe is not None:
        data['correoe'] = update_data.correoe
    if update_data.dir_trabajador is not None:
        data['dir_trabajador'] = update_data.dir_trabajador
    if update_data.codarea1 is not None:
        data['codarea1'] = update_data.codarea1
    if update_data.telefono1 is not None:
        data['telefono1'] = update_data.telefono1
    if update_data.codarea2 is not None:
        data['codarea2'] = update_data.codarea2
    if update_data.telefono2 is not None:
        data['telefono2'] = update_data.telefono2
    if update_data.privilegio is not None:
        data['privilegio'] = update_data.privilegio.value if hasattr(update_data.privilegio, 'value') else update_data.privilegio
    if update_data.activo is not None:
        data['activo'] = 1 if update_data.activo else 0
    if update_data.contrasena is not None:
        data['contrasena'] = hash_password(update_data.contrasena)
    
    if data:
        affected = db.update('trabajador', data, {'id_t1': user_id})
        return {
            'success': True,
            'message': f'Usuario actualizado ({affected} filas)'
        }
    
    return {
        'success': True,
        'message': 'No se realizaron cambios'
    }

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    admin: Dict = Depends(require_admin)
) -> Dict:
    """Elimina un usuario (desactivación lógica)"""
    affected = db.update(
        'trabajador',
        {'activo': 0},
        {'id_t1': user_id}
    )
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        'success': True,
        'message': 'Usuario desactivado exitosamente'
    }