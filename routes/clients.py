# routes/clients.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional

from database import db
from models import ClientCreate, ClientUpdate, UserRole
from routes.auth import get_current_user, require_admin, hash_password

router = APIRouter()

# ============ ENDPOINTS ============

@router.get("/")
async def get_clients(
    user: Dict = Depends(require_admin)
) -> List[Dict]:
    """Obtiene todos los clientes"""
    clients = db.fetch_all(
        "SELECT id_t10, ci_cliente, n_cliente, a_cliente, mail_cliente, usuario_cliente, activo, bloqueado, fecha_registro, ultimo_login FROM cliente ORDER BY n_cliente"
    )
    return clients

@router.get("/{client_id}")
async def get_client(
    client_id: int,
    user: Dict = Depends(require_admin)
) -> Dict:
    """Obtiene un cliente por ID"""
    client = db.fetch_one(
        "SELECT * FROM cliente WHERE id_t10 = %s",
        (client_id,)
    )
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    client.pop('contrasena_cliente', None)
    return client

@router.post("/")
async def create_client(
    client_data: ClientCreate,
    user: Dict = Depends(require_admin)
) -> Dict:
    """Crea un nuevo cliente"""
    # Verificar si ya existe
    existing = db.fetch_one(
        "SELECT * FROM cliente WHERE ci_cliente = %s OR usuario_cliente = %s",
        (client_data.ci_cliente, client_data.usuario_cliente)
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="El cliente o usuario ya está registrado"
        )
    
    hashed_password = hash_password(client_data.contrasena_cliente)
    
    data = {
        'ci_cliente': client_data.ci_cliente,
        'n_cliente': client_data.n_cliente,
        'a_cliente': client_data.a_cliente,
        'mail_cliente': client_data.mail_cliente,
        'usuario_cliente': client_data.usuario_cliente,
        'contrasena_cliente': hashed_password,
        'es_ext': 1 if client_data.es_ext else 0,
        'rif_cliente': client_data.rif_cliente,
        'dir_cliente': client_data.dir_cliente,
        'ciu_cliente': client_data.ciu_cliente,
        'codtlf1': client_data.codtlf1,
        'tlf1_cliente': client_data.tlf1_cliente,
        'codtlf2': client_data.codtlf2,
        'tlf2_cliente': client_data.tlf2_cliente
    }
    
    client_id = db.insert('cliente', data)
    
    return {
        'success': True,
        'message': 'Cliente creado exitosamente',
        'client_id': client_id
    }

@router.put("/{client_id}")
async def update_client(
    client_id: int,
    update_data: ClientUpdate,
    user: Dict = Depends(require_admin)
) -> Dict:
    """Actualiza un cliente"""
    existing = db.fetch_one(
        "SELECT * FROM cliente WHERE id_t10 = %s",
        (client_id,)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    data = {}
    if update_data.n_cliente is not None:
        data['n_cliente'] = update_data.n_cliente
    if update_data.a_cliente is not None:
        data['a_cliente'] = update_data.a_cliente
    if update_data.rif_cliente is not None:
        data['rif_cliente'] = update_data.rif_cliente
    if update_data.dir_cliente is not None:
        data['dir_cliente'] = update_data.dir_cliente
    if update_data.ciu_cliente is not None:
        data['ciu_cliente'] = update_data.ciu_cliente
    if update_data.codtlf1 is not None:
        data['codtlf1'] = update_data.codtlf1
    if update_data.tlf1_cliente is not None:
        data['tlf1_cliente'] = update_data.tlf1_cliente
    if update_data.codtlf2 is not None:
        data['codtlf2'] = update_data.codtlf2
    if update_data.tlf2_cliente is not None:
        data['tlf2_cliente'] = update_data.tlf2_cliente
    if update_data.mail_cliente is not None:
        data['mail_cliente'] = update_data.mail_cliente
    if update_data.activo is not None:
        data['activo'] = 1 if update_data.activo else 0
    if update_data.bloqueado is not None:
        data['bloqueado'] = 1 if update_data.bloqueado else 0
    if update_data.causa_bloqueo is not None:
        data['causa_bloqueo'] = update_data.causa_bloqueo
        data['fecha_bloqueo'] = 'CURDATE()' if update_data.bloqueado else None
    
    if data:
        affected = db.update('cliente', data, {'id_t10': client_id})
        return {
            'success': True,
            'message': f'Cliente actualizado ({affected} filas)'
        }
    
    return {
        'success': True,
        'message': 'No se realizaron cambios'
    }

@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    user: Dict = Depends(require_admin)
) -> Dict:
    """Elimina un cliente (desactivación lógica)"""
    affected = db.update(
        'cliente',
        {'activo': 0},
        {'id_t10': client_id}
    )
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return {
        'success': True,
        'message': 'Cliente desactivado exitosamente'
    }

@router.post("/{client_id}/block")
async def block_client(
    client_id: int,
    cause: str,
    user: Dict = Depends(require_admin)
) -> Dict:
    """Bloquea un cliente"""
    affected = db.update(
        'cliente',
        {
            'bloqueado': 1,
            'causa_bloqueo': cause,
            'fecha_bloqueo': 'CURDATE()'
        },
        {'id_t10': client_id}
    )
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return {
        'success': True,
        'message': 'Cliente bloqueado exitosamente'
    }

@router.post("/{client_id}/unblock")
async def unblock_client(
    client_id: int,
    user: Dict = Depends(require_admin)
) -> Dict:
    """Desbloquea un cliente"""
    affected = db.update(
        'cliente',
        {
            'bloqueado': 0,
            'causa_bloqueo': None,
            'fecha_bloqueo': None,
            'intento_fallido': 0
        },
        {'id_t10': client_id}
    )
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return {
        'success': True,
        'message': 'Cliente desbloqueado exitosamente'
    }