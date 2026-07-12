# models.py
from pydantic import BaseModel, Field, EmailStr
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

class PurchaseStatus(str, Enum):
    TRANSIT = "transito"
    EXECUTED = "ejecutada"
    CANCELLED = "anulada"

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
    user: Optional[Dict] = None
    message: Optional[str] = None

class RegisterRequest(BaseModel):
    ci_trabajador: int
    n_trabajador: str
    a_trabajador: str
    usuario: str
    cargo: str
    contrasena: str
    correoe: EmailStr
    dir_trabajador: Optional[str] = None
    codarea1: Optional[str] = None
    telefono1: Optional[str] = None
    privilegio: UserRole = UserRole.VISITOR

# ============ USERS ============
class UserCreate(BaseModel):
    ci_trabajador: int
    n_trabajador: str
    a_trabajador: str
    usuario: str
    cargo: str
    contrasena: str
    correoe: EmailStr
    dir_trabajador: Optional[str] = None
    codarea1: Optional[str] = None
    telefono1: Optional[str] = None
    codarea2: Optional[str] = None
    telefono2: Optional[str] = None
    privilegio: UserRole = UserRole.VISITOR
    es_ext: bool = False

class UserUpdate(BaseModel):
    n_trabajador: Optional[str] = None
    a_trabajador: Optional[str] = None
    cargo: Optional[str] = None
    contrasena: Optional[str] = None
    correoe: Optional[EmailStr] = None
    dir_trabajador: Optional[str] = None
    codarea1: Optional[str] = None
    telefono1: Optional[str] = None
    codarea2: Optional[str] = None
    telefono2: Optional[str] = None
    privilegio: Optional[UserRole] = None
    activo: Optional[bool] = None

# ============ CLIENTS ============
class ClientCreate(BaseModel):
    ci_cliente: int
    n_cliente: str
    a_cliente: str
    mail_cliente: EmailStr
    usuario_cliente: str
    contrasena_cliente: str
    es_ext: bool = False
    rif_cliente: Optional[str] = None
    dir_cliente: Optional[str] = None
    ciu_cliente: Optional[str] = None
    codtlf1: Optional[str] = None
    tlf1_cliente: Optional[str] = None
    codtlf2: Optional[str] = None
    tlf2_cliente: Optional[str] = None

class ClientUpdate(BaseModel):
    n_cliente: Optional[str] = None
    a_cliente: Optional[str] = None
    rif_cliente: Optional[str] = None
    dir_cliente: Optional[str] = None
    ciu_cliente: Optional[str] = None
    codtlf1: Optional[str] = None
    tlf1_cliente: Optional[str] = None
    codtlf2: Optional[str] = None
    tlf2_cliente: Optional[str] = None
    mail_cliente: Optional[EmailStr] = None
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
    incremento: bool  # True = crédito, False = débito
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
    rnc: Optional[str] = None
    rnc_vence: Optional[date] = None
    renovacion: Optional[date] = None
    condicion: SupplierCondition = SupplierCondition.APPLICANT
    objeto: Optional[str] = None
    lugar_referencia: Optional[str] = None
    codigo_postal: Optional[str] = None
    codigo_area1: Optional[str] = None
    telefono_1: Optional[str] = None
    codigo_area2: Optional[str] = None
    telefono_2: Optional[str] = None
    correo_e: Optional[EmailStr] = None
    tipo_producto: Optional[int] = None  # 1:Bienes, 2:Servicios, 3:Mixta
    productos: Optional[str] = None
    junta_vence: Optional[date] = None
    v_e_represent: Optional[bool] = None
    ci_represent: Optional[int] = None
    nom_represent: Optional[str] = None
    ape_represent: Optional[str] = None
    cod_area_represent: Optional[str] = None
    tlf_represent: Optional[str] = None
    correo_e_represent: Optional[EmailStr] = None
    doc_requeridos: Optional[str] = None

# ============ WAREHOUSES ============
class WarehouseCreate(BaseModel):
    cod_almacen: str
    nombre_almacen: str
    tipo_almacen: str
    dir_almacen: str
    ciudad_o_poblacion: str
    estado_o_provincia: str
    pais: str
    finalidad: Optional[str] = None
    objetos_almacena: Optional[str] = None
    lugar_referencia: Optional[str] = None
    cod_postal: Optional[str] = None
    cod_area1_almacen: Optional[str] = None
    tlf1_almacen: Optional[str] = None
    cod_area2_almacen: Optional[str] = None
    tlf2_almacen: Optional[str] = None
    correo_almacen: Optional[EmailStr] = None
    v_e_encargado: Optional[bool] = None
    ci_encargado: Optional[int] = None
    nom_encargado: Optional[str] = None
    ape_encargado: Optional[str] = None
    cod_area_encargado: Optional[str] = None
    tlf_encargado: Optional[str] = None
    correo_e_encargado: Optional[EmailStr] = None
    condicion_: Optional[int] = 1  # 1:Habilitado, 2:Deshabilitado
    fecha_condicion: Optional[date] = None

# ============ INVENTORY ============
class InventoryCreate(BaseModel):
    cod_producto: str
    producto: str
    es_servicio: bool = False
    cod_almacen: Optional[str] = None
    stock: int = 0
    min_stock: int = 5
    precio: float = 0
    color_codigo: Optional[str] = None
    color_denominacion: Optional[str] = None
    dimension_magnitud: Optional[str] = None
    dimension_unidad: Optional[str] = None
    talla: Optional[str] = None
    peso_magnitud: Optional[float] = None
    peso_unidad: Optional[str] = None
    olor: Optional[str] = None
    sensacion: Optional[str] = None
    calidad: Optional[str] = None
    ingredientes: Optional[str] = None
    caracteristica_tec: Optional[str] = None
    modelo: Optional[str] = None
    marca: Optional[str] = None
    con_garantia: bool = False
    servicio_posventa: bool = False
    iva: bool = True
    ivs: bool = False
    oia: bool = False
    observacion: Optional[str] = None

# ============ PURCHASES ============
class PurchaseCreate(BaseModel):
    orden_compra: str
    fecha_compra: date
    cod_proveedor: str
    requisicion: Optional[str] = None
    fecha_requisicion: Optional[date] = None
    orden_pago: Optional[str] = None
    fecha_orden_pago: Optional[date] = None
    observacion: Optional[str] = None
    items: List[Dict[str, Any]]

class PurchaseItemCreate(BaseModel):
    destino: str
    calificador: str
    cod_producto: str
    cantidad: float
    monto_unitario: float
    cod_almacen: str
    codigo_item: str
    expedicion_item: Optional[date] = None
    vencimiento_item: Optional[date] = None
    observacion_items: Optional[str] = None
    monto_iva: float = 0
    monto_ivs: float = 0
    monto_oia: float = 0
    monto_retencion_iva: float = 0

# ============ SALES ============
class SaleCreate(BaseModel):
    factura: Optional[str] = None
    ci_cliente: int
    ci_trabajador: int
    metodo_pago: str
    items: List[Dict[str, Any]]

class SaleItemCreate(BaseModel):
    cod_producto: str
    codigo_item: str
    cod_almacen: str
    cantidad: float
    precio: float
    precio_iva: float = 0
    precio_ivs: float = 0
    precio_oia: float = 0
    precio_retencion_iva: float = 0

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

# ============ SCHEDULE ============
class ScheduleCreate(BaseModel):
    ci_trabajador: int
    dia_semana: str  # Lunes, Martes, ...
    hora_inicio_m: Optional[time] = None
    hora_fin_m: Optional[time] = None
    hora_inicio_t: Optional[time] = None
    hora_fin_t: Optional[time] = None
    es_feriado: bool = False

class ScheduleUpdate(BaseModel):
    hora_inicio_m: Optional[time] = None
    hora_fin_m: Optional[time] = None
    hora_inicio_t: Optional[time] = None
    hora_fin_t: Optional[time] = None
    es_feriado: Optional[bool] = None
    activo: Optional[bool] = None

class HolidayCreate(BaseModel):
    fecha_feriado: date
    feriado: str
    tipo_feriado: str  # Nacional, Regional, Local, Empresarial

class ExceptionCreate(BaseModel):
    ci_trabajador: int
    fecha_excepcion: date
    tipo_excepcion: str  # Laboral, Feriado, Personal
    excepcion: str
    hora_inicio_m: Optional[time] = None
    hora_fin_m: Optional[time] = None
    hora_inicio_t: Optional[time] = None
    hora_fin_t: Optional[time] = None

# ============ FISCAL DATA ============
class FiscalDataUpdate(BaseModel):
    iva_porcentaje: Optional[float] = None
    ivs_porcentaje: Optional[float] = None
    oia_porcentaje: Optional[float] = None
    retencion_iva: Optional[float] = None
    rif_emisor: Optional[str] = None
    razon_social: Optional[str] = None
    domicilio_fiscal: Optional[str] = None
    num_ctrl_fical: Optional[str] = None
    bs_usd: Optional[float] = None
    bs_eur: Optional[float] = None
    bs_cny: Optional[float] = None

# ============ DASHBOARD ============
class DashboardStats(BaseModel):
    total_users: int
    total_clients: int
    total_services: int
    sales_today: float
    appointments_today: int
    low_stock: int