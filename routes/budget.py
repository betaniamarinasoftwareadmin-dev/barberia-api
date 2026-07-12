# routes/budget.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from datetime import date

from database import db
from models import BudgetCreate, BudgetUpdate, BudgetAdjustment
from routes.auth import get_current_user, require_manager_or_admin

router = APIRouter()

# ============ ENDPOINTS ============

@router.get("/")
async def get_budget(
    user: Dict = Depends(get_current_user)
) -> List[Dict]:
    """Obtiene todas las partidas presupuestarias"""
    budget = db.fetch_all(
        "SELECT * FROM presupuesto ORDER BY inicio DESC, destino, calificador"
    )
    return budget

@router.get("/{budget_id}")
async def get_budget_item(
    budget_id: int,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """Obtiene una partida presupuestaria por ID"""
    item = db.fetch_one(
        "SELECT * FROM presupuesto WHERE id_t2 = %s",
        (budget_id,)
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="Partida presupuestaria no encontrada")
    
    return item

@router.post("/")
async def create_budget(
    budget_data: BudgetCreate,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Crea una nueva partida presupuestaria"""
    # Verificar si ya existe
    existing = db.fetch_one(
        "SELECT * FROM presupuesto WHERE destino = %s AND calificador = %s AND inicio = %s AND final = %s",
        (budget_data.destino, budget_data.calificador, budget_data.inicio, budget_data.final)
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Esta partida presupuestaria ya existe para el período indicado"
        )
    
    data = {
        'destino': budget_data.destino,
        'calificador': budget_data.calificador,
        'descripcion': budget_data.descripcion,
        'inicio': budget_data.inicio,
        'final': budget_data.final,
        'cantidad_2': budget_data.cantidad_2,
        'cant_actual': budget_data.cantidad_2,  # Inicialmente igual a cantidad_2
        'advertencia': budget_data.advertencia,
        'denom_dest': budget_data.denom_dest,
        'habilitada': 1
    }
    
    budget_id = db.insert('presupuesto', data)
    
    return {
        'success': True,
        'message': 'Partida presupuestaria creada exitosamente',
        'budget_id': budget_id
    }

@router.put("/{budget_id}")
async def update_budget(
    budget_id: int,
    update_data: BudgetUpdate,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Actualiza una partida presupuestaria"""
    existing = db.fetch_one(
        "SELECT * FROM presupuesto WHERE id_t2 = %s",
        (budget_id,)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Partida presupuestaria no encontrada")
    
    data = {}
    if update_data.descripcion is not None:
        data['descripcion'] = update_data.descripcion
    if update_data.cantidad_2 is not None:
        data['cantidad_2'] = update_data.cantidad_2
        # Actualizar también el monto actual si es mayor
        if update_data.cantidad_2 > existing['cant_actual']:
            data['cant_actual'] = update_data.cantidad_2
    if update_data.advertencia is not None:
        data['advertencia'] = update_data.advertencia
    if update_data.denom_dest is not None:
        data['denom_dest'] = update_data.denom_dest
    if update_data.habilitada is not None:
        data['habilitada'] = 1 if update_data.habilitada else 0
    
    if data:
        affected = db.update('presupuesto', data, {'id_t2': budget_id})
        return {
            'success': True,
            'message': f'Partida presupuestaria actualizada ({affected} filas)'
        }
    
    return {
        'success': True,
        'message': 'No se realizaron cambios'
    }

@router.post("/adjust")
async def adjust_budget(
    adjustment: BudgetAdjustment,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Realiza un ajuste presupuestario (crédito/débito)"""
    # Verificar que la partida existe
    budget_item = db.fetch_one(
        "SELECT * FROM presupuesto WHERE destino = %s AND calificador = %s AND inicio = %s AND final = %s AND habilitada = 1",
        (adjustment.destino, adjustment.calificador, adjustment.inicio, adjustment.final)
    )
    
    if not budget_item:
        raise HTTPException(
            status_code=404,
            detail="Partida presupuestaria no encontrada o deshabilitada"
        )
    
    # Verificar disponibilidad para débito
    if not adjustment.incremento and adjustment.cantidad_3 > budget_item['cant_actual']:
        raise HTTPException(
            status_code=400,
            detail="Fondos insuficientes para el débito solicitado"
        )
    
    # Calcular nuevo monto actual
    new_amount = budget_item['cant_actual']
    if adjustment.incremento:  # Crédito
        new_amount += adjustment.cantidad_3
    else:  # Débito
        new_amount -= adjustment.cantidad_3
    
    # Iniciar transacción
    db.begin_transaction()
    
    try:
        # Registrar el ajuste
        ajuste_data = {
            'destino': adjustment.destino,
            'calificador': adjustment.calificador,
            'inicio': adjustment.inicio,
            'final': adjustment.final,
            'motivo': adjustment.motivo,
            'se_realizo': adjustment.se_realizo,
            'incremento': 1 if adjustment.incremento else 0,
            'cantidad_3': adjustment.cantidad_3,
            'traelacant': budget_item['cant_actual'],
            'oficio_num': adjustment.oficio_num
        }
        
        db.insert('ajustes', ajuste_data)
        
        # Actualizar el presupuesto
        db.update(
            'presupuesto',
            {
                'cant_actual': new_amount,
                'modificado': 1,
                'ultima_cons': f"Ajuste por oficio N° {adjustment.oficio_num} - {adjustment.se_realizo}"
            },
            {'id_t2': budget_item['id_t2']}
        )
        
        db.commit()
        
        return {
            'success': True,
            'message': 'Ajuste presupuestario realizado exitosamente',
            'new_amount': new_amount
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al realizar ajuste: {str(e)}")

@router.get("/adjustments")
async def get_adjustments(
    user: Dict = Depends(get_current_user)
) -> List[Dict]:
    """Obtiene todos los ajustes presupuestarios"""
    adjustments = db.fetch_all(
        "SELECT * FROM ajustes ORDER BY se_realizo DESC"
    )
    return adjustments

@router.get("/check-availability")
async def check_budget_availability(
    destino: str,
    calificador: str,
    inicio: date,
    final: date,
    amount: float,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """Verifica la disponibilidad presupuestaria para una compra"""
    budget_item = db.fetch_one(
        "SELECT * FROM presupuesto WHERE destino = %s AND calificador = %s AND inicio = %s AND final = %s AND habilitada = 1",
        (destino, calificador, inicio, final)
    )
    
    if not budget_item:
        return {
            'success': False,
            'error': 'Partida presupuestaria no encontrada o deshabilitada'
        }
    
    if budget_item['cant_actual'] >= amount:
        return {
            'success': True,
            'available': True,
            'current_amount': budget_item['cant_actual'],
            'requested_amount': amount
        }
    else:
        return {
            'success': True,
            'available': False,
            'current_amount': budget_item['cant_actual'],
            'requested_amount': amount,
            'deficit': amount - budget_item['cant_actual']
        }