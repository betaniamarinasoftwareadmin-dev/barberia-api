# routes/warehouses.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict

from database import db
from models import WarehouseCreate
from routes.auth import get_current_user, require_manager_or_admin

router = APIRouter()

@router.get("/")
async def get_warehouses(
    user: Dict = Depends(get_current_user)
) -> List[Dict]:
    """Obtiene todos los almacenes"""
    warehouses = db.fetch_all(
        "SELECT * FROM almacen ORDER BY nombre_almacen"
    )
    return warehouses

@router.get("/{warehouse_id}")
async def get_warehouse(
    warehouse_id: int,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """Obtiene un almacén por ID"""
    warehouse = db.fetch_one(
        "SELECT * FROM almacen WHERE id_t7 = %s",
        (warehouse_id,)
    )
    
    if not warehouse:
        raise HTTPException(status_code=404, detail="Almacén no encontrado")
    
    return warehouse

@router.post("/")
async def create_warehouse(
    warehouse_data: WarehouseCreate,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Crea un nuevo almacén"""
    existing = db.fetch_one(
        "SELECT * FROM almacen WHERE cod_almacen = %s",
        (warehouse_data.cod_almacen,)
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="El código de almacén ya existe"
        )
    
    data = warehouse_data.dict()
    warehouse_id = db.insert('almacen', data)
    
    return {
        'success': True,
        'message': 'Almacén creado exitosamente',
        'warehouse_id': warehouse_id
    }

@router.put("/{warehouse_id}")
async def update_warehouse(
    warehouse_id: int,
    warehouse_data: WarehouseCreate,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Actualiza un almacén"""
    existing = db.fetch_one(
        "SELECT * FROM almacen WHERE id_t7 = %s",
        (warehouse_id,)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Almacén no encontrado")
    
    data = warehouse_data.dict()
    affected = db.update('almacen', data, {'id_t7': warehouse_id})
    
    return {
        'success': True,
        'message': f'Almacén actualizado ({affected} filas)'
    }

@router.delete("/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: int,
    user: Dict = Depends(require_admin)
) -> Dict:
    """Elimina un almacén"""
    affected = db.delete('almacen', {'id_t7': warehouse_id})
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Almacén no encontrado")
    
    return {
        'success': True,
        'message': 'Almacén eliminado exitosamente'
    }