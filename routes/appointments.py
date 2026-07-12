# routes/appointments.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from database import db
from models import AppointmentCreate, AppointmentUpdate, AppointmentStatus
from routes.auth import get_current_user, require_manager_or_admin

router = APIRouter()

# ============ SERVICIO DE DISPONIBILIDAD ============

def is_worker_available(ci_trabajador: int, fecha: str, hora: str) -> bool:
    """Verifica si un trabajador está disponible en una fecha y hora específica"""
    
    # 1. Verificar si es feriado del trabajador
    holiday = db.fetch_one(
        "SELECT * FROM horario_feriado WHERE ci_trabajador = %s AND fecha_feriado = %s AND activo = 1",
        (ci_trabajador, fecha)
    )
    if holiday:
        return False
    
    # 2. Verificar si tiene excepción
    exception = db.fetch_one(
        "SELECT * FROM horario_excepcion WHERE ci_trabajador = %s AND fecha_excepcion = %s AND activo = 1",
        (ci_trabajador, fecha)
    )
    if exception:
        return False
    
    # 3. Verificar horario laboral del día
    dia_semana = datetime.strptime(fecha, "%Y-%m-%d").strftime("%A")
    # Convertir a español
    dias_es = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
               'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado',
               'Sunday': 'Domingo'}
    dia_semana_es = dias_es.get(dia_semana, dia_semana)
    
    schedule = db.fetch_one(
        "SELECT * FROM horario_trabajo WHERE ci_trabajador = %s AND dia_semana = %s AND activo = 1",
        (ci_trabajador, dia_semana_es)
    )
    
    if not schedule:
        return False
    
    # 4. Verificar si la hora está dentro del horario
    hora_entrada_m = schedule.get('hora_inicio_m')
    hora_salida_m = schedule.get('hora_fin_m')
    hora_entrada_t = schedule.get('hora_inicio_t')
    hora_salida_t = schedule.get('hora_fin_t')
    
    hora_obj = datetime.strptime(hora, "%H:%M").time()
    
    disponible = False
    
    if hora_entrada_m and hora_salida_m:
        if hora_entrada_m <= hora_obj <= hora_salida_m:
            disponible = True
    
    if not disponible and hora_entrada_t and hora_salida_t:
        if hora_entrada_t <= hora_obj <= hora_salida_t:
            disponible = True
    
    if not disponible:
        return False
    
    # 5. Verificar que no tenga cita a esa hora
    appointment = db.fetch_one(
        "SELECT * FROM control_citas WHERE ci_trabajador = %s AND fecha_cita = %s AND hora_cita = %s AND status != 'cancelada'",
        (ci_trabajador, fecha, hora)
    )
    
    return appointment is None

# ============ ENDPOINTS ============

@router.get("/")
async def get_appointments(
    user: Dict = Depends(get_current_user),
    filter_date: Optional[str] = None,
    ci_trabajador: Optional[int] = None
) -> List[Dict]:
    """Obtiene las citas con filtros opcionales"""
    query = """
        SELECT c.*, cl.n_cliente, cl.a_cliente, t.n_trabajador, t.a_trabajador, i.producto as servicio_nombre
        FROM control_citas c
        JOIN cliente cl ON c.ci_cliente = cl.ci_cliente
        JOIN trabajador t ON c.ci_trabajador = t.ci_trabajador
        JOIN inventario i ON c.servicio = i.cod_producto
        WHERE 1=1
    """
    params = []
    
    if filter_date:
        query += " AND c.fecha_cita = %s"
        params.append(filter_date)
    
    if ci_trabajador:
        query += " AND c.ci_trabajador = %s"
        params.append(ci_trabajador)
    
    query += " ORDER BY c.fecha_cita DESC, c.hora_cita ASC"
    
    appointments = db.fetch_all(query, tuple(params) if params else None)
    return appointments

@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: int,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """Obtiene una cita por ID"""
    appointment = db.fetch_one(
        """SELECT c.*, cl.n_cliente, cl.a_cliente, t.n_trabajador, t.a_trabajador, i.producto as servicio_nombre
           FROM control_citas c
           JOIN cliente cl ON c.ci_cliente = cl.ci_cliente
           JOIN trabajador t ON c.ci_trabajador = t.ci_trabajador
           JOIN inventario i ON c.servicio = i.cod_producto
           WHERE c.id_t11 = %s""",
        (appointment_id,)
    )
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    return appointment

@router.post("/")
async def create_appointment(
    appointment_data: AppointmentCreate,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """Crea una nueva cita"""
    
    # 1. Verificar que el cliente existe
    client = db.fetch_one(
        "SELECT * FROM cliente WHERE ci_cliente = %s AND activo = 1 AND bloqueado = 0",
        (appointment_data.ci_cliente,)
    )
    
    if not client:
        raise HTTPException(
            status_code=400,
            detail="Cliente no encontrado, inactivo o bloqueado"
        )
    
    # 2. Verificar que el servicio existe y es un servicio
    service = db.fetch_one(
        "SELECT * FROM inventario WHERE cod_producto = %s AND es_servicio = 1 AND inexistencia = 0",
        (appointment_data.servicio,)
    )
    
    if not service:
        raise HTTPException(
            status_code=400,
            detail="Servicio no disponible o no encontrado"
        )
    
    # 3. Verificar que el trabajador existe
    worker = db.fetch_one(
        "SELECT * FROM trabajador WHERE ci_trabajador = %s AND activo = 1",
        (appointment_data.ci_trabajador,)
    )
    
    if not worker:
        raise HTTPException(
            status_code=400,
            detail="Trabajador no encontrado o inactivo"
        )
    
    # 4. Verificar disponibilidad del trabajador
    fecha_str = appointment_data.fecha_cita.strftime("%Y-%m-%d")
    hora_str = appointment_data.hora_cita.strftime("%H:%M")
    
    if not is_worker_available(appointment_data.ci_trabajador, fecha_str, hora_str):
        raise HTTPException(
            status_code=400,
            detail="El trabajador no está disponible en esa fecha y hora"
        )
    
    # 5. Crear la cita
    data = appointment_data.dict()
    data['status'] = 'pendiente'
    
    appointment_id = db.insert('control_citas', data)
    
    return {
        'success': True,
        'message': 'Cita creada exitosamente',
        'appointment_id': appointment_id
    }

@router.put("/{appointment_id}")
async def update_appointment(
    appointment_id: int,
    update_data: AppointmentUpdate,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """Actualiza una cita"""
    existing = db.fetch_one(
        "SELECT * FROM control_citas WHERE id_t11 = %s",
        (appointment_id,)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Verificar disponibilidad si cambia fecha, hora o trabajador
    if update_data.fecha_cita or update_data.hora_cita or update_data.ci_trabajador:
        trabajador = update_data.ci_trabajador or existing['ci_trabajador']
        fecha = update_data.fecha_cita or existing['fecha_cita']
        hora = update_data.hora_cita or existing['hora_cita']
        
        fecha_str = fecha.strftime("%Y-%m-%d")
        hora_str = hora.strftime("%H:%M")
        
        # Verificar que no sea la misma cita
        if trabajador == existing['ci_trabajador'] and fecha_str == existing['fecha_cita'].strftime("%Y-%m-%d") and hora_str == existing['hora_cita'].strftime("%H:%M"):
            pass
        else:
            if not is_worker_available(trabajador, fecha_str, hora_str):
                raise HTTPException(
                    status_code=400,
                    detail="El trabajador no está disponible en esa fecha y hora"
                )
    
    # Preparar datos para actualizar
    data = {}
    if update_data.fecha_cita is not None:
        data['fecha_cita'] = update_data.fecha_cita
    if update_data.hora_cita is not None:
        data['hora_cita'] = update_data.hora_cita
    if update_data.ci_trabajador is not None:
        data['ci_trabajador'] = update_data.ci_trabajador
    if update_data.servicio is not None:
        data['servicio'] = update_data.servicio
    if update_data.status is not None:
        data['status'] = update_data.status.value if hasattr(update_data.status, 'value') else update_data.status
    
    if data:
        affected = db.update('control_citas', data, {'id_t11': appointment_id})
        return {
            'success': True,
            'message': f'Cita actualizada ({affected} filas)'
        }
    
    return {
        'success': True,
        'message': 'No se realizaron cambios'
    }

@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    user: Dict = Depends(require_manager_or_admin)
) -> Dict:
    """Elimina una cita"""
    affected = db.delete('control_citas', {'id_t11': appointment_id})
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    return {
        'success': True,
        'message': 'Cita eliminada exitosamente'
    }

@router.put("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: int,
    status: str,
    user: Dict = Depends(get_current_user)
) -> Dict:
    """Actualiza el estado de una cita"""
    valid_status = ['pendiente', 'confirmada', 'cancelada', 'completada']
    
    if status not in valid_status:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Debe ser uno de: {', '.join(valid_status)}"
        )
    
    affected = db.update(
        'control_citas',
        {'status': status},
        {'id_t11': appointment_id}
    )
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    return {
        'success': True,
        'message': f'Cita actualizada a "{status}"'
    }

@router.get("/available-slots")
async def get_available_slots(
    ci_trabajador: int,
    fecha: str,
    user: Dict = Depends(get_current_user)
) -> List[str]:
    """Obtiene los horarios disponibles para un trabajador en una fecha"""
    slots = []
    dias_es = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
               'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado',
               'Sunday': 'Domingo'}
    
    dia_semana = datetime.strptime(fecha, "%Y-%m-%d").strftime("%A")
    dia_semana_es = dias_es.get(dia_semana, dia_semana)
    
    # Obtener horario del trabajador
    schedule = db.fetch_one(
        "SELECT * FROM horario_trabajo WHERE ci_trabajador = %s AND dia_semana = %s AND activo = 1",
        (ci_trabajador, dia_semana_es)
    )
    
    if not schedule:
        return slots
    
    # Generar slots de 30 minutos
    intervalos = []
    
    if schedule.get('hora_inicio_m') and schedule.get('hora_fin_m'):
        inicio = datetime.strptime(str(schedule['hora_inicio_m']), "%H:%M:%S")
        fin = datetime.strptime(str(schedule['hora_fin_m']), "%H:%M:%S")
        intervalos.append((inicio, fin))
    
    if schedule.get('hora_inicio_t') and schedule.get('hora_fin_t'):
        inicio = datetime.strptime(str(schedule['hora_inicio_t']), "%H:%M:%S")
        fin = datetime.strptime(str(schedule['hora_fin_t']), "%H:%M:%S")
        intervalos.append((inicio, fin))
    
    # Verificar cada slot
    for inicio, fin in intervalos:
        current = inicio
        while current + timedelta(minutes=30) <= fin:
            hora_str = current.strftime("%H:%M")
            if is_worker_available(ci_trabajador, fecha, hora_str):
                slots.append(hora_str)
            current += timedelta(minutes=30)
    
    return slots