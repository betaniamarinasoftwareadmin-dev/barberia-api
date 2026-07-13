from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime
from enum import Enum

# ============ ENUMS ============

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    BARBER = "barber"
    CASHIER = "cashier"
    VISITOR = "visitor"

class AppointmentStatus(str, Enum):
    PENDING = "pendiente"
    CONFIRMED = "confirmada"
    CANCELLED = "cancelada"
    COMPLETED = "completada"

class SupplierCondition(str, Enum):
    APPLICANT = "solicitante"
    REGISTERED = "inscrito"
    RENEWAL = "renovacion"

# ============ AUTH ============

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class RegisterRequest(BaseModel):
    ci_trabajador: int
    n_trabajador: str
    a_trabajador: str
    usuario: str
    cargo: str
    contrasena: str
    correoe: str
    dir_trabajador: Optional[str] = None
    privilegio: UserRole = UserRole.VISITOR

# ============ USERS ============

class UserCreate(BaseModel):
    ci_trabajador: int
    n_trabajador: str
    a_trabajador: str
    usuario: str
    cargo: str
    contrasena: str
    correoe: str
    privilegio: UserRole = UserRole.VISITOR
    activo: bool = True

class UserUpdate(BaseModel):
    n_trabajador: Optional[str] = None
    a_trabajador: Optional[str] = None
    cargo: Optional[str] = None
    contrasena: Optional[str] = None
    correoe: Optional[str] = None
    privilegio: Optional[UserRole] = None
    activo: Optional[bool] = None

# ============ CLIENTS ============

class ClientCreate(BaseModel):
    ci_cliente: int
    n_cliente: str
    a_cliente: str
    mail_cliente: str
    usuario_cliente: str
    contrasena_cliente: str
    dir_cliente: Optional[str] = None
    rif_cliente: Optional[str] = None

class ClientUpdate(BaseModel):
    n_cliente: Optional[str] = None
    a_cliente: Optional[str] = None
    mail_cliente: Optional[str] = None
    activo: Optional[bool] = None
    bloqueado: Optional[bool] = None
    causa_bloqueo: Optional[str] = None

# ============ BUDGET ============

class BudgetCreate(BaseModel):
    destino: str
    calificador: str
    descripcion: str
    inicio: date
    final: date
    cantidad_2: float
    advertencia: float = 0
    denom_dest: Optional[str] = None

class BudgetUpdate(BaseModel):
    descripcion: Optional[str] = None
    cantidad_2: Optional[float] = None
    advertencia: Optional[float] = None
    denom_dest: Optional[str] = None
    habilitada: Optional[bool] = None

class BudgetAdjustment(BaseModel):
    destino: str
    calificador: str
    inicio: date
    final: date
    motivo: str
    se_realizo: date
    incremento: bool
    cantidad_3: float
    oficio_num: str

# ============ SUPPLIERS ============

class SupplierCreate(BaseModel):
    cod_proveedor: str
    nombre_proveedor: str
    rif: str
    rif_vence: date
    dir_oficina: str
    ciudad_o_poblacion: str
    estado_o_provincia: str
    pais: str
    inscripcion: date
    condicion: SupplierCondition = SupplierCondition.APPLICANT
    rnc: Optional[str] = None
    rnc_vence: Optional[date] = None
    renovacion: Optional[date] = None

# ============ WAREHOUSES ============

class WarehouseCreate(BaseModel):
    cod_almacen: str
    nombre_almacen: str
    tipo_almacen: str
    dir_almacen: str
    ciudad_o_poblacion: str
    estado_o_provincia: str
    pais: str
    condicion_: int = 1

# ============ INVENTORY ============

class InventoryCreate(BaseModel):
    cod_producto: str
    producto: str
    es_servicio: bool = False
    cod_almacen: Optional[str] = None
    stock: int = 0
    min_stock: int = 5
    precio: float = 0

# ============ APPOINTMENTS ============

class AppointmentCreate(BaseModel):
    ci_cliente: int
    fecha_cita: date
    hora_cita: time
    ci_trabajador: int
    servicio: str

class AppointmentUpdate(BaseModel):
    fecha_cita: Optional[date] = None
    hora_cita: Optional[time] = None
    ci_trabajador: Optional[int] = None
    servicio: Optional[str] = None
    status: Optional[AppointmentStatus] = None

# ============ DASHBOARD ============

class DashboardStats(BaseModel):
    total_users: int = 0
    total_clients: int = 0
    total_services: int = 0
    sales_today: float = 0.0
    appointments_today: int = 0
    low_stock: int = 0