# routes/sales.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from datetime import datetime

from database import db
from models import SaleCreate
from routes.auth import get_current_user, require_manager_or_admin

router = APIRouter()

@router.get("/")
async def get_sales(
    user: Dict = Depends(get_current_user)
) -> List[Dict]:
    """Obtiene todas las ventas"""
    sales = db.fetch_all(
        """SELECT v.*, c.n_cliente, c.a_cliente, t.n_trabajador, t.a_trabajador as t_apellido
           FROM ventas v
           JOIN cliente c ON v.ci_cliente = c.ci_cliente
           JOIN trabajador t ON v.ci_trabajador = t.ci_trabajador
           ORDER BY v.fecha_emision DESC, v.hora_emision DESC"""
    )
    return sales

@router.get("/{sale_id}")
async def get_sale(
    sale_id: int,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """Obtiene una venta por ID con sus ítems"""
    sale = db.fetch_one(
        "SELECT * FROM ventas WHERE id_t12 = %s",
        (sale_id,)
    )
    
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    
    # Obtener ítems de la venta
    items = db.fetch_all(
        "SELECT * FROM items_ventas WHERE factura = %s",
        (sale['factura'],)
    )
    
    sale['items'] = items
    return sale

@router.post("/")
async def create_sale(
    sale_data: SaleCreate,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """Crea una nueva venta con sus ítems"""
    
    # Iniciar transacción
    db.begin_transaction()
    
    try:
        # 1. Generar número de factura
        last_invoice = db.fetch_one(
            "SELECT factura FROM ventas ORDER BY id_t12 DESC LIMIT 1"
        )
        
        if last_invoice:
            last_num = int(last_invoice['factura'])
            factura = f"{last_num + 1:010d}"
        else:
            factura = "0000000001"
        
        # 2. Verificar que el cliente existe
        client = db.fetch_one(
            "SELECT * FROM cliente WHERE ci_cliente = %s AND activo = 1 AND bloqueado = 0",
            (sale_data.ci_cliente,)
        )
        
        if not client:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Cliente no encontrado, inactivo o bloqueado"
            )
        
        # 3. Verificar que el trabajador existe
        worker = db.fetch_one(
            "SELECT * FROM trabajador WHERE ci_trabajador = %s AND activo = 1",
            (sale_data.ci_trabajador,)
        )
        
        if not worker:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Trabajador no encontrado o inactivo"
            )
        
        # 4. Obtener datos fiscales
        fiscal = db.fetch_one("SELECT * FROM datos_fiscales LIMIT 1")
        
        if not fiscal:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Datos fiscales no configurados"
            )
        
        # 5. Crear la venta
        venta_data = {
            'factura': factura,
            'fecha_emision': datetime.now().date(),
            'hora_emision': datetime.now().time(),
            'rif_emisor': fiscal['rif_emisor'],
            'ci_cliente': sale_data.ci_cliente,
            'rif_cliente': client.get('rif_cliente'),
            'ci_trabajador': sale_data.ci_trabajador,
            'metodo_pago': sale_data.metodo_pago
        }
        
        db.insert('ventas', venta_data)
        
        # 6. Crear los ítems y actualizar inventario
        for item in sale_data.items:
            # Verificar que el producto existe y tiene stock
            inventory = db.fetch_one(
                "SELECT * FROM inventario WHERE cod_producto = %s AND es_servicio = 0 AND inexistencia = 0",
                (item['cod_producto'],)
            )
            
            if inventory:
                # Es un producto físico
                if inventory['stock'] < item['cantidad']:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Stock insuficiente para {inventory['producto']}. Disponible: {inventory['stock']}"
                    )
            else:
                # Es un servicio
                service = db.fetch_one(
                    "SELECT * FROM inventario WHERE cod_producto = %s AND es_servicio = 1 AND inexistencia = 0",
                    (item['cod_producto'],)
                )
                
                if not service:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Producto o servicio {item['cod_producto']} no encontrado"
                    )
            
            # Calcular precios con impuestos
            iva_porcentaje = fiscal['iva_porcentaje'] or 0
            ivs_porcentaje = fiscal['ivs_porcentaje'] or 0
            oia_porcentaje = fiscal['oia_porcentaje'] or 0
            
            precio_iva = (item['precio'] * iva_porcentaje / 100) if iva_porcentaje else 0
            precio_ivs = (item['precio'] * ivs_porcentaje / 100) if ivs_porcentaje else 0
            precio_oia = (item['precio'] * oia_porcentaje / 100) if oia_porcentaje else 0
            
            # Insertar ítem de venta
            item_data = {
                'factura': factura,
                'cod_producto': item['cod_producto'],
                'codigo_item': item['codigo_item'],
                'cod_almacen': item['cod_almacen'],
                'cantidad': item['cantidad'],
                'precio': item['precio'],
                'precio_iva': precio_iva,
                'precio_ivs': precio_ivs,
                'precio_oia': precio_oia,
                'precio_retencion_iva': item.get('precio_retencion_iva', 0)
            }
            
            db.insert('items_ventas', item_data)
            
            # Actualizar inventario (solo para productos físicos)
            if inventory and not inventory['es_servicio']:
                db.update(
                    'inventario',
                    {'stock': inventory['stock'] - int(item['cantidad'])},
                    {'id_t8': inventory['id_t8']}
                )
        
        db.commit()
        
        return {
            'success': True,
            'message': 'Venta creada exitosamente',
            'factura': factura
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear venta: {str(e)}")