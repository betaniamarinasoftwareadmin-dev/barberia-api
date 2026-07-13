from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any  # ✅ ¡AÑADIR ESTA LÍNEA!

from database import db
from models import DashboardStats
from routes.auth import get_current_user

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    user: Dict[str, Any] = Depends(get_current_user)  # ✅ USAR Dict[str, Any]
) -> DashboardStats:
    today = datetime.now().strftime("%Y-%m-%d")
    
    total_users = db.fetch_one("SELECT COUNT(*) FROM trabajador WHERE activo = 1") or {'COUNT(*)': 0}
    total_clients = db.fetch_one("SELECT COUNT(*) FROM cliente WHERE activo = 1") or {'COUNT(*)': 0}
    total_services = db.fetch_one("SELECT COUNT(*) FROM inventario WHERE es_servicio = 1 AND inexistencia = 0") or {'COUNT(*)': 0}
    
    sales_today = db.fetch_one(
        "SELECT COALESCE(SUM(precio * cantidad), 0) FROM items_ventas WHERE factura IN (SELECT factura FROM ventas WHERE fecha_emision = %s)",
        (today,)
    ) or {'COALESCE(SUM(precio * cantidad), 0)': 0}
    
    appointments_today = db.fetch_one(
        "SELECT COUNT(*) FROM control_citas WHERE fecha_cita = %s AND status != 'cancelada'",
        (today,)
    ) or {'COUNT(*)': 0}
    
    low_stock = db.fetch_one(
        "SELECT COUNT(*) FROM inventario WHERE es_servicio = 0 AND stock <= min_stock AND inexistencia = 0"
    ) or {'COUNT(*)': 0}
    
    return DashboardStats(
        total_users=total_users.get('COUNT(*)', 0),
        total_clients=total_clients.get('COUNT(*)', 0),
        total_services=total_services.get('COUNT(*)', 0),
        sales_today=float(sales_today.get('COALESCE(SUM(precio * cantidad), 0)', 0)),
        appointments_today=appointments_today.get('COUNT(*)', 0),
        low_stock=low_stock.get('COUNT(*)', 0)
    )