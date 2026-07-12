# routes/dashboard.py
from fastapi import APIRouter, Depends
from datetime import datetime

from database import db
from models import DashboardStats
from routes.auth import get_current_user

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    user: Dict = Depends(get_current_user)
) -> DashboardStats:
    """Obtiene estadísticas para el dashboard"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Total de usuarios activos
    total_users = db.fetch_one("SELECT COUNT(*) FROM trabajador WHERE activo = 1")['COUNT(*)']
    
    # Total de clientes activos
    total_clients = db.fetch_one("SELECT COUNT(*) FROM cliente WHERE activo = 1")['COUNT(*)']
    
    # Servicios activos
    total_services = db.fetch_one(
        "SELECT COUNT(*) FROM inventario WHERE es_servicio = 1 AND inexistencia = 0"
    )['COUNT(*)']
    
    # Ventas del día
    sales_today = db.fetch_one(
        """SELECT COALESCE(SUM(precio * cantidad), 0) FROM items_ventas 
           WHERE factura IN (
               SELECT factura FROM ventas WHERE fecha_emision = %s
           )""",
        (today,)
    )['COALESCE(SUM(precio * cantidad), 0)']
    
    # Citas del día
    appointments_today = db.fetch_one(
        "SELECT COUNT(*) FROM control_citas WHERE fecha_cita = %s AND status != 'cancelada'",
        (today,)
    )['COUNT(*)']
    
    # Productos con stock bajo
    low_stock = db.fetch_one(
        "SELECT COUNT(*) FROM inventario WHERE es_servicio = 0 AND stock <= min_stock AND inexistencia = 0"
    )['COUNT(*)']
    
    return DashboardStats(
        total_users=total_users,
        total_clients=total_clients,
        total_services=total_services,
        sales_today=float(sales_today),
        appointments_today=appointments_today,
        low_stock=low_stock
    )

@router.get("/recent-sales")
async def get_recent_sales(
    limit: int = 5,
    user: Dict = Depends(get_current_user)
) -> List[Dict]:
    """Obtiene las ventas recientes"""
    sales = db.fetch_all(
        """SELECT v.factura, c.n_cliente, c.a_cliente, v.fecha_emision, 
                  COALESCE(SUM(iv.cantidad * iv.precio), 0) as total
           FROM ventas v
           JOIN cliente c ON v.ci_cliente = c.ci_cliente
           LEFT JOIN items_ventas iv ON v.factura = iv.factura
           GROUP BY v.factura, c.n_cliente, c.a_cliente, v.fecha_emision
           ORDER BY v.fecha_emision DESC, v.hora_emision DESC
           LIMIT %s""",
        (limit,)
    )
    
    return sales