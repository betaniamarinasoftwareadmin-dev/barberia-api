# routes/schedule.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional

from database import db
from models import ScheduleCreate, ScheduleUpdate, HolidayCreate, ExceptionCreate
from routes.auth import get_current_user, require_manager_or_admin

router = APIRouter()

# ============ HORARIO TRABAJO ============

@router.get("/")
async def get_schedules(
    user: Dict = Depends(get_current_user),
    ci_trabajador: Optional[int] = None
) -> List[Dict]:
    """Obtiene los horarios de trabajo"""
    if ci_trabajador:
        schedules = db.fetch_all(
            "SELECT * FROM horario_trabajo WHERE ci_trabajador = %s ORDER BY FIELD(dia_semana, 'Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo')",
            (ci_trabajador,)
        )
    else:
        schedules = db.fetch_all(
            "SELECT * FROM horario_trabajo ORDER BY ci_trabajador, FIELD(dia_semana, 'Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo')"
        )
    return schedules

@router.post("/")
async def create_schedule(
    schedule_data: ScheduleCreate,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Crea un horario de trabajo"""
    # Verificar que el trabajador existe
    worker = db.fetch_one(
        "SELECT * FROM trabajador WHERE ci_trabajador = %s AND activo = 1",
        (schedule_data.ci_trabajador,)
    )
    
    if not worker:
        raise HTTPException(
            status_code=400,
            detail="Trabajador no encontrado o inactivo"
        )
    
    # Verificar que no exista un horario para ese día
    existing = db.fetch_one(
        "SELECT * FROM horario_trabajo WHERE ci_trabajador = %s AND dia_semana = %s",
        (schedule_data.ci_trabajador, schedule_data.dia_semana)
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un horario para ese día"
        )
    
    data = schedule_data.dict()
    schedule_id = db.insert('horario_trabajo', data)
    
    return {
        'success': True,
        'message': 'Horario creado exitosamente',
        'schedule_id': schedule_id
    }

@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: int,
    update_data: ScheduleUpdate,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Actualiza un horario de trabajo"""
    existing = db.fetch_one(
        "SELECT * FROM horario_trabajo WHERE id_t14 = %s",
        (schedule_id,)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    data = {}
    if update_data.hora_inicio_m is not None:
        data['hora_inicio_m'] = update_data.hora_inicio_m
    if update_data.hora_fin_m is not None:
        data['hora_fin_m'] = update_data.hora_fin_m
    if update_data.hora_inicio_t is not None:
        data['hora_inicio_t'] = update_data.hora_inicio_t
    if update_data.hora_fin_t is not None:
        data['hora_fin_t'] = update_data.hora_fin_t
    if update_data.es_feriado is not None:
        data['es_feriado'] = 1 if update_data.es_feriado else 0
    if update_data.activo is not None:
        data['activo'] = 1 if update_data.activo else 0
    
    if data:
        data['fecha_actualizacion'] = 'NOW()'
        affected = db.update('horario_trabajo', data, {'id_t14': schedule_id})
        return {
            'success': True,
            'message': f'Horario actualizado ({affected} filas)'
        }
    
    return {
        'success': True,
        'message': 'No se realizaron cambios'
    }

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Elimina un horario de trabajo"""
    affected = db.delete('horario_trabajo', {'id_t14': schedule_id})
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    return {
        'success': True,
        'message': 'Horario eliminado exitosamente'
    }

# ============ FERIADOS ============

@router.get("/holidays")
async def get_holidays(
    user: Dict = Depends(get_current_user),
    ci_trabajador: Optional[int] = None
) -> List[Dict]:
    """Obtiene los feriados"""
    if ci_trabajador:
        holidays = db.fetch_all(
            "SELECT * FROM horario_feriado WHERE ci_trabajador = %s ORDER BY fecha_feriado",
            (ci_trabajador,)
        )
    else:
        holidays = db.fetch_all(
            "SELECT * FROM horario_feriado ORDER BY ci_trabajador, fecha_feriado"
        )
    return holidays

@router.post("/holidays")
async def create_holiday(
    holiday_data: HolidayCreate,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Crea un feriado"""
    data = holiday_data.dict()
    holiday_id = db.insert('horario_feriado', data)
    
    return {
        'success': True,
        'message': 'Feriado creado exitosamente',
        'holiday_id': holiday_id
    }

@router.delete("/holidays/{holiday_id}")
async def delete_holiday(
    holiday_id: int,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Elimina un feriado"""
    affected = db.delete('horario_feriado', {'id_t16': holiday_id})
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Feriado no encontrado")
    
    return {
        'success': True,
        'message': 'Feriado eliminado exitosamente'
    }

# ============ EXCEPCIONES ============

@router.get("/exceptions")
async def get_exceptions(
    user: Dict = Depends(get_current_user),
    ci_trabajador: Optional[int] = None
) -> List[Dict]:
    """Obtiene las excepciones"""
    if ci_trabajador:
        exceptions = db.fetch_all(
            "SELECT * FROM horario_excepcion WHERE ci_trabajador = %s ORDER BY fecha_excepcion",
            (ci_trabajador,)
        )
    else:
        exceptions = db.fetch_all(
            "SELECT * FROM horario_excepcion ORDER BY ci_trabajador, fecha_excepcion"
        )
    return exceptions

@router.post("/exceptions")
async def create_exception(
    exception_data: ExceptionCreate,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Crea una excepción"""
    # Verificar que el trabajador existe
    worker = db.fetch_one(
        "SELECT * FROM trabajador WHERE ci_trabajador = %s AND activo = 1",
        (exception_data.ci_trabajador,)
    )
    
    if not worker:
        raise HTTPException(
            status_code=400,
            detail="Trabajador no encontrado o inactivo"
        )
    
    data = exception_data.dict()
    exception_id = db.insert('horario_excepcion', data)
    
    return {
        'success': True,
        'message': 'Excepción creada exitosamente',
        'exception_id': exception_id
    }

@router.delete("/exceptions/{exception_id}")
async def delete_exception(
    exception_id: int,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Elimina una excepción"""
    affected = db.delete('horario_excepcion', {'id_t15': exception_id})
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Excepción no encontrada")
    
    return {
        'success': True,
        'message': 'Excepción eliminada exitosamente'
    }