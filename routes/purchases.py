# routes/purchases.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from datetime import datetime

from database import db
from models import PurchaseCreate
from routes.auth import get_current_user, require_manager_or_admin

router = APIRouter()

@router.get("/")
async def get_purchases(
    user: Dict = Depends(get_current_user)
) -> List[Dict]:
    """Obtiene todas las compras"""
    purchases = db.fetch_all(
        """SELECT c.*, p.nombre_proveedor 
           FROM compras c
           LEFT JOIN proveedor p ON c.cod_proveedor = p.cod_proveedor
           ORDER BY c.fecha_compra DESC"""
    )
    return purchases

@router.get("/{purchase_id}")
async def get_purchase(
    purchase_id: int,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """Obtiene una compra por ID con sus ítems"""
    purchase = db.fetch_one(
        "SELECT * FROM compras WHERE id_t5 = %s",
        (purchase_id,)
    )
    
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    # Obtener ítems de la compra
    items = db.fetch_all(
        "SELECT * FROM items_compras WHERE orden_compra = %s",
        (purchase['orden_compra'],)
    )
    
    purchase['items'] = items
    return purchase

@router.post("/")
async def create_purchase(
    purchase_data: PurchaseCreate,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Crea una nueva compra con sus ítems"""
    # Verificar que la orden de compra no existe
    existing = db.fetch_one(
        "SELECT * FROM compras WHERE orden_compra = %s",
        (purchase_data.orden_compra,)
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="La orden de compra ya existe"
        )
    
    # Verificar que el proveedor existe
    supplier = db.fetch_one(
        "SELECT * FROM proveedor WHERE cod_proveedor = %s",
        (purchase_data.cod_proveedor,)
    )
    
    if not supplier:
        raise HTTPException(
            status_code=400,
            detail="Proveedor no encontrado"
        )
    
    # Iniciar transacción
    db.begin_transaction()
    
    try:
        # 1. Crear la compra
        compra_data = {
            'orden_compra': purchase_data.orden_compra,
            'fecha_compra': purchase_data.fecha_compra,
            'cod_proveedor': purchase_data.cod_proveedor,
            'requisicion': purchase_data.requisicion,
            'fecha_requisicion': purchase_data.fecha_requisicion,
            'orden_pago': purchase_data.orden_pago,
            'fecha_orden_pago': purchase_data.fecha_orden_pago,
            'observacion': purchase_data.observacion,
            'estatus_orden_compra': 1,  # Tránsito
            'impresa_orden_compra': 0,
            'fecha_impresion': None
        }
        
        db.insert('compras', compra_data)
        
        # 2. Crear los ítems y actualizar presupuesto
        for item in purchase_data.items:
            # Verificar disponibilidad presupuestaria
            budget = db.fetch_one(
                "SELECT * FROM presupuesto WHERE destino = %s AND calificador = %s AND habilitada = 1",
                (item['destino'], item['calificador'])
            )
            
            if not budget:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"No hay partida presupuestaria para destino {item['destino']} y calificador {item['calificador']}"
                )
            
            monto_item = item['cantidad'] * item['monto_unitario']
            
            if budget['cant_actual'] < monto_item:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Fondos insuficientes. Disponible: {budget['cant_actual']}, Necesario: {monto_item}"
                )
            
            # Insertar ítem
            item_data = {
                'orden_compra': purchase_data.orden_compra,
                'destino': item['destino'],
                'calificador': item['calificador'],
                'cod_producto': item['cod_producto'],
                'cantidad': item['cantidad'],
                'monto_unitario': item['monto_unitario'],
                'cod_almacen': item['cod_almacen'],
                'codigo_item': item['codigo_item'],
                'expedicion_item': item.get('expedicion_item'),
                'vencimiento_item': item.get('vencimiento_item'),
                'observacion_items': item.get('observacion_items'),
                'monto_iva': item.get('monto_iva', 0),
                'monto_ivs': item.get('monto_ivs', 0),
                'monto_oia': item.get('monto_oia', 0),
                'monto_retencion_iva': item.get('monto_retencion_iva', 0)
            }
            
            db.insert('items_compras', item_data)
            
            # Actualizar presupuesto (comprometer fondos)
            db.update(
                'presupuesto',
                {
                    'cant_actual': budget['cant_actual'] - monto_item,
                    'modificado': 1,
                    'ultima_cons': f"Compra N° {purchase_data.orden_compra}"
                },
                {'id_t2': budget['id_t2']}
            )
            
            # Actualizar inventario
            inventory = db.fetch_one(
                "SELECT * FROM inventario WHERE cod_producto = %s",
                (item['cod_producto'],)
            )
            
            if inventory:
                db.update(
                    'inventario',
                    {'stock': inventory['stock'] + int(item['cantidad'])},
                    {'id_t8': inventory['id_t8']}
                )
        
        db.commit()
        
        return {
            'success': True,
            'message': 'Compra creada exitosamente',
            'orden_compra': purchase_data.orden_compra
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear compra: {str(e)}")