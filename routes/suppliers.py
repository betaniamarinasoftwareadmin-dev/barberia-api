from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from database import db
from models import SupplierCreate
from routes.auth import get_current_user, require_admin, require_manager_or_admin

router = APIRouter()

@router.get("/")
async def get_suppliers(
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Obtiene todos los proveedores"""
    suppliers = db.fetch_all(
        "SELECT * FROM proveedor ORDER BY nombre_proveedor"
    )
    return suppliers

@router.get("/{supplier_id}")
async def get_supplier(
    supplier_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Obtiene un proveedor por ID"""
    supplier = db.fetch_one(
        "SELECT * FROM proveedor WHERE id_t4 = %s",
        (supplier_id,)
    )
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    return supplier

@router.post("/")
async def create_supplier(
    supplier_data: SupplierCreate,
    user: Dict[str, Any] = Depends(require_manager_or_admin)
) -> Dict[str, Any]:
    """Crea un nuevo proveedor"""
    existing = db.fetch_one(
        "SELECT * FROM proveedor WHERE cod_proveedor = %s",
        (supplier_data.cod_proveedor,)
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="El código de proveedor ya existe"
        )
    
    data = supplier_data.dict()
    supplier_id = db.insert('proveedor', data)
    
    return {
        'success': True,
        'message': 'Proveedor creado exitosamente',
        'supplier_id': supplier_id
    }

@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierCreate,
    user: Dict[str, Any] = Depends(require_manager_or_admin)
) -> Dict[str, Any]:
    """Actualiza un proveedor"""
    existing = db.fetch_one(
        "SELECT * FROM proveedor WHERE id_t4 = %s",
        (supplier_id,)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    data = supplier_data.dict()
    affected = db.update('proveedor', data, {'id_t4': supplier_id})
    
    return {
        'success': True,
        'message': f'Proveedor actualizado ({affected} filas)'
    }

@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Elimina un proveedor"""
    affected = db.delete('proveedor', {'id_t4': supplier_id})
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    return {
        'success': True,
        'message': 'Proveedor eliminado exitosamente'
    }