from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional

from database import db
from models import InventoryCreate
from routes.auth import get_current_user, require_admin, require_manager_or_admin

router = APIRouter()

@router.get("/")
async def get_inventory(
    user: Dict[str, Any] = Depends(get_current_user),
    es_servicio: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """Obtiene todo el inventario, opcionalmente filtrado por tipo"""
    query = "SELECT * FROM inventario WHERE inexistencia = 0"
    params = []
    
    if es_servicio is not None:
        query += " AND es_servicio = %s"
        params.append(1 if es_servicio else 0)
    
    query += " ORDER BY producto"
    
    inventory = db.fetch_all(query, tuple(params) if params else None)
    return inventory

@router.get("/{item_id}")
async def get_inventory_item(
    item_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Obtiene un ítem del inventario por ID"""
    item = db.fetch_one(
        "SELECT * FROM inventario WHERE id_t8 = %s",
        (item_id,)
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    
    return item

@router.post("/")
async def create_inventory_item(
    item_data: InventoryCreate,
    user: Dict[str, Any] = Depends(require_manager_or_admin)
) -> Dict[str, Any]:
    """Crea un nuevo ítem en el inventario"""
    existing = db.fetch_one(
        "SELECT * FROM inventario WHERE cod_producto = %s",
        (item_data.cod_producto,)
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="El código de producto ya existe"
        )
    
    data = item_data.dict()
    item_id = db.insert('inventario', data)
    
    return {
        'success': True,
        'message': 'Ítem creado exitosamente',
        'item_id': item_id
    }

@router.put("/{item_id}")
async def update_inventory_item(
    item_id: int,
    item_data: InventoryCreate,
    user: Dict[str, Any] = Depends(require_manager_or_admin)
) -> Dict[str, Any]:
    """Actualiza un ítem del inventario"""
    existing = db.fetch_one(
        "SELECT * FROM inventario WHERE id_t8 = %s",
        (item_id,)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    
    data = item_data.dict()
    affected = db.update('inventario', data, {'id_t8': item_id})
    
    return {
        'success': True,
        'message': f'Ítem actualizado ({affected} filas)'
    }

@router.delete("/{item_id}")
async def delete_inventory_item(
    item_id: int,
    user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Elimina un ítem del inventario (marca como inexistente)"""
    affected = db.update(
        'inventario',
        {'inexistencia': 1},
        {'id_t8': item_id}
    )
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    
    return {
        'success': True,
        'message': 'Ítem marcado como inexistente'
    }