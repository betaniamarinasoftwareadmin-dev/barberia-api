# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import uvicorn

from config import Config
from database import db
from routes import auth, users, clients, budget, suppliers, warehouses, inventory, purchases, sales, appointments, schedule

# Crear la aplicación FastAPI
app = FastAPI(
    title=Config.API_TITLE,
    description=Config.API_DESCRIPTION,
    version=Config.API_VERSION
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ RUTAS PRINCIPALES ============

@app.get("/")
async def root():
    return {
        "message": "Bienvenido a la API de Barbería BETANIA",
        "version": Config.API_VERSION,
        "status": "online"
    }

@app.get("/health")
async def health_check():
    """Verifica el estado de la API y la conexión a la base de datos"""
    try:
        db.connect()
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

# ============ INCLUIR ROUTERS ============

app.include_router(auth.router, prefix="/api", tags=["Autenticación"])
app.include_router(users.router, prefix="/api/users", tags=["Usuarios"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clientes"])
app.include_router(budget.router, prefix="/api/budget", tags=["Presupuesto"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["Proveedores"])
app.include_router(warehouses.router, prefix="/api/warehouses", tags=["Almacenes"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventario"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["Compras"])
app.include_router(sales.router, prefix="/api/sales", tags=["Ventas"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Citas"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["Horarios"])

# ============ MANEJADOR DE ERRORES GLOBAL ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    print(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Error interno del servidor"
        }
    )

# ============ EVENTOS DE INICIO ============

@app.on_event("startup")
async def startup():
    """Inicializa la conexión a la base de datos"""
    print("🔄 Iniciando API de Barbería BETANIA...")
    if db.connect():
        print("✅ Conexión a MySQL establecida correctamente")
    else:
        print("❌ Error al conectar con MySQL")
    
    # Crear tablas si no existen
    await create_tables_if_not_exist()

@app.on_event("shutdown")
async def shutdown():
    """Cierra la conexión a la base de datos"""
    print("🔄 Cerrando API...")
    db.close()
    print("✅ Conexión cerrada")

async def create_tables_if_not_exist():
    """Crea las tablas si no existen"""
    tables = [
        """CREATE TABLE IF NOT EXISTS conectividad (
            id_t0 INT AUTO_INCREMENT PRIMARY KEY,
            ci_trabajador INT NOT NULL,
            usuario VARCHAR(100) NOT NULL,
            estacion VARCHAR(25) NOT NULL,
            entrada DATETIME DEFAULT CURRENT_TIMESTAMP,
            salida DATETIME NULL
        )""",
        
        """CREATE TABLE IF NOT EXISTS trabajador (
            id_t1 INT AUTO_INCREMENT PRIMARY KEY,
            es_ext TINYINT(1) DEFAULT 0,
            ci_trabajador INT NOT NULL UNIQUE,
            n_trabajador VARCHAR(30) NOT NULL,
            a_trabajador VARCHAR(30) NOT NULL,
            usuario VARCHAR(100) NOT NULL UNIQUE,
            cargo VARCHAR(60) NOT NULL,
            dir_trabajador VARCHAR(140),
            codarea1 VARCHAR(4),
            telefono1 VARCHAR(7),
            codarea2 VARCHAR(4),
            telefono2 VARCHAR(7),
            privilegio TINYINT NOT NULL DEFAULT 5,
            contrasena VARCHAR(255) NOT NULL,
            correoe VARCHAR(120) NOT NULL,
            activo TINYINT(1) DEFAULT 1
        )""",
        
        """CREATE TABLE IF NOT EXISTS presupuesto (
            id_t2 INT AUTO_INCREMENT PRIMARY KEY,
            destino VARCHAR(11) NOT NULL,
            calificador VARCHAR(13) NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            inicio DATE NOT NULL,
            final DATE NOT NULL,
            cantidad_2 DECIMAL(15,2) NOT NULL,
            advertencia DECIMAL(15,2) NOT NULL DEFAULT 0,
            cant_actual DECIMAL(15,2) NOT NULL,
            ultima_cons VARCHAR(80),
            modificado TINYINT(1) DEFAULT 0,
            denom_dest VARCHAR(60),
            habilitada TINYINT(1) DEFAULT 1,
            UNIQUE KEY (destino, calificador, inicio, final)
        )""",
        
        """CREATE TABLE IF NOT EXISTS ajustes (
            id_t3 INT AUTO_INCREMENT PRIMARY KEY,
            destino VARCHAR(11) NOT NULL,
            calificador VARCHAR(13) NOT NULL,
            inicio DATE NOT NULL,
            final DATE NOT NULL,
            motivo VARCHAR(200) NOT NULL,
            se_realizo DATE NOT NULL,
            incremento TINYINT(1) NOT NULL,
            cantidad_3 DECIMAL(15,2) NOT NULL,
            traelacant DECIMAL(15,2) NOT NULL,
            oficio_num VARCHAR(25) NOT NULL
        )""",
        
        """CREATE TABLE IF NOT EXISTS proveedor (
            id_t4 INT AUTO_INCREMENT PRIMARY KEY,
            cod_proveedor VARCHAR(11) NOT NULL UNIQUE,
            nombre_proveedor VARCHAR(60) NOT NULL,
            rif VARCHAR(15) NOT NULL,
            rif_vence DATE NOT NULL,
            rnc VARCHAR(31),
            rnc_vence DATE,
            inscripcion DATE NOT NULL,
            renovacion DATE,
            condicion TINYINT(1) DEFAULT 1,
            objeto VARCHAR(250),
            dir_oficina VARCHAR(140) NOT NULL,
            lugar_referencia VARCHAR(50),
            ciudad_o_poblacion VARCHAR(20) NOT NULL,
            estado_o_provincia VARCHAR(20) NOT NULL,
            pais VARCHAR(35) NOT NULL,
            codigo_postal VARCHAR(10),
            codigo_area1 VARCHAR(4),
            telefono_1 VARCHAR(7),
            codigo_area2 VARCHAR(4),
            telefono_2 VARCHAR(7),
            correo_e VARCHAR(120),
            tipo_producto TINYINT(1),
            productos VARCHAR(250),
            junta_vence DATE,
            v_e_represent TINYINT(1),
            ci_represent INT,
            nom_represent VARCHAR(30),
            ape_represent VARCHAR(30),
            cod_area_represent VARCHAR(4),
            tlf_represent VARCHAR(7),
            correo_e_represent VARCHAR(120),
            doc_requeridos VARCHAR(10)
        )""",
        
        """CREATE TABLE IF NOT EXISTS compras (
            id_t5 INT AUTO_INCREMENT PRIMARY KEY,
            orden_compra VARCHAR(13) NOT NULL UNIQUE,
            fecha_compra DATE NOT NULL,
            requisicion VARCHAR(13),
            fecha_requisicion DATE,
            orden_pago VARCHAR(13),
            fecha_orden_pago DATE,
            observacion VARCHAR(140),
            estatus_orden_compra TINYINT(1) DEFAULT 1,
            impresa_orden_compra TINYINT(1) DEFAULT 0,
            fecha_impresion DATE,
            cod_proveedor VARCHAR(11) NOT NULL,
            FOREIGN KEY (cod_proveedor) REFERENCES proveedor(cod_proveedor)
        )""",
        
        """CREATE TABLE IF NOT EXISTS items_compras (
            id_t6 INT AUTO_INCREMENT PRIMARY KEY,
            orden_compra VARCHAR(13) NOT NULL,
            destino VARCHAR(11) NOT NULL,
            calificador VARCHAR(13) NOT NULL,
            cod_producto VARCHAR(13) NOT NULL,
            cantidad DECIMAL(12,2) NOT NULL,
            monto_unitario DECIMAL(15,2) NOT NULL,
            monto_iva DECIMAL(10,2) DEFAULT 0,
            monto_ivs DECIMAL(10,2) DEFAULT 0,
            monto_oia DECIMAL(10,2) DEFAULT 0,
            monto_retencion_iva DECIMAL(10,2) DEFAULT 0,
            observacion_items VARCHAR(140),
            inexistencia TINYINT(1) DEFAULT 0,
            cod_almacen VARCHAR(11) NOT NULL,
            codigo_item VARCHAR(11) NOT NULL UNIQUE,
            expedicion_item DATE,
            vencimiento_item DATE,
            fecha_presupuesto DATE,
            ultima_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (orden_compra) REFERENCES compras(orden_compra)
        )""",
        
        """CREATE TABLE IF NOT EXISTS almacen (
            id_t7 INT AUTO_INCREMENT PRIMARY KEY,
            cod_almacen VARCHAR(11) NOT NULL UNIQUE,
            nombre_almacen VARCHAR(60) NOT NULL,
            tipo_almacen VARCHAR(25) NOT NULL,
            finalidad VARCHAR(250),
            objetos_almacena VARCHAR(250),
            dir_almacen VARCHAR(140) NOT NULL,
            lugar_referencia VARCHAR(50),
            ciudad_o_poblacion VARCHAR(20) NOT NULL,
            estado_o_provincia VARCHAR(20) NOT NULL,
            pais VARCHAR(35) NOT NULL,
            cod_postal VARCHAR(10),
            cod_area1_almacen VARCHAR(4),
            tlf1_almacen VARCHAR(7),
            cod_area2_almacen VARCHAR(4),
            tlf2_almacen VARCHAR(7),
            correo_almacen VARCHAR(120),
            v_e_encargado TINYINT(1),
            ci_encargado INT,
            nom_encargado VARCHAR(30),
            ape_encargado VARCHAR(30),
            cod_area_encargado VARCHAR(4),
            tlf_encargado VARCHAR(7),
            correo_e_encargado VARCHAR(120),
            condicion_ TINYINT(1) DEFAULT 1,
            fecha_condicion DATE,
            saturacion TINYINT(1) DEFAULT 0,
            fecha_saturacion DATE
        )""",
        
        """CREATE TABLE IF NOT EXISTS inventario (
            id_t8 INT AUTO_INCREMENT PRIMARY KEY,
            es_servicio TINYINT(1) DEFAULT 0,
            cod_producto VARCHAR(13) NOT NULL UNIQUE,
            producto VARCHAR(60) NOT NULL,
            cod_almacen VARCHAR(11),
            color_codigo VARCHAR(7),
            color_denominacion VARCHAR(25),
            dimension_magnitud VARCHAR(20),
            dimension_unidad VARCHAR(2),
            talla VARCHAR(4),
            peso_magnitud DECIMAL(7,2),
            peso_unidad VARCHAR(2),
            olor VARCHAR(25),
            sensacion VARCHAR(25),
            calidad VARCHAR(25),
            ingredientes VARCHAR(140),
            caracteristica_tec VARCHAR(140),
            modelo VARCHAR(25),
            marca VARCHAR(25),
            con_garantia TINYINT(1) DEFAULT 0,
            servicio_posventa TINYINT(1) DEFAULT 0,
            stock INT DEFAULT 0,
            min_stock INT DEFAULT 5,
            precio DECIMAL(12,2) DEFAULT 0,
            iva TINYINT(1) DEFAULT 1,
            ivs TINYINT(1) DEFAULT 0,
            oia TINYINT(1) DEFAULT 0,
            observacion VARCHAR(140),
            inexistencia TINYINT(1) DEFAULT 0
        )""",
        
        """CREATE TABLE IF NOT EXISTS datos_fiscales (
            id_t9 INT AUTO_INCREMENT PRIMARY KEY,
            iva_porcentaje DECIMAL(5,2) DEFAULT 16.00,
            ivs_porcentaje DECIMAL(5,2) DEFAULT 0,
            oia_porcentaje DECIMAL(5,2) DEFAULT 0,
            retencion_iva DECIMAL(5,2) DEFAULT 0,
            destino_ret VARCHAR(11),
            calificador_ret VARCHAR(13),
            destino_iva VARCHAR(11),
            calificador_iva VARCHAR(13),
            rif_emisor VARCHAR(15) NOT NULL,
            razon_social VARCHAR(60) NOT NULL,
            domicilio_fiscal VARCHAR(60) NOT NULL,
            num_ctrl_fical VARCHAR(12),
            fecha_ctrl_fiscal DATE,
            bs_usd DECIMAL(10,2) DEFAULT 1,
            bs_eur DECIMAL(10,2) DEFAULT 1,
            bs_cny DECIMAL(10,2) DEFAULT 1
        )""",
        
        """CREATE TABLE IF NOT EXISTS cliente (
            id_t10 INT AUTO_INCREMENT PRIMARY KEY,
            es_ext TINYINT(1) DEFAULT 0,
            ci_cliente INT NOT NULL UNIQUE,
            rif_cliente VARCHAR(15),
            n_cliente VARCHAR(30) NOT NULL,
            a_cliente VARCHAR(30) NOT NULL,
            dir_cliente VARCHAR(60),
            ciu_cliente VARCHAR(20),
            codtlf1 VARCHAR(4),
            tlf1_cliente VARCHAR(7),
            codtlf2 VARCHAR(4),
            tlf2_cliente VARCHAR(7),
            mail_cliente VARCHAR(120),
            usuario_cliente VARCHAR(100) NOT NULL UNIQUE,
            contrasena_cliente VARCHAR(255) NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_login DATETIME NULL,
            activo TINYINT(1) DEFAULT 1,
            intento_fallido INT DEFAULT 0,
            bloqueado TINYINT(1) DEFAULT 0,
            fecha_bloqueo DATE,
            causa_bloqueo VARCHAR(60)
        )""",
        
        """CREATE TABLE IF NOT EXISTS control_citas (
            id_t11 INT AUTO_INCREMENT PRIMARY KEY,
            ci_cliente INT NOT NULL,
            fecha_cita DATE NOT NULL,
            hora_cita TIME NOT NULL,
            ci_trabajador INT NOT NULL,
            status ENUM('pendiente', 'confirmada', 'cancelada', 'completada') DEFAULT 'pendiente',
            creada DATETIME DEFAULT CURRENT_TIMESTAMP,
            servicio VARCHAR(13) NOT NULL,
            FOREIGN KEY (ci_cliente) REFERENCES cliente(ci_cliente),
            FOREIGN KEY (ci_trabajador) REFERENCES trabajador(ci_trabajador),
            UNIQUE KEY (ci_trabajador, fecha_cita, hora_cita)
        )""",
        
        """CREATE TABLE IF NOT EXISTS ventas (
            id_t12 INT AUTO_INCREMENT PRIMARY KEY,
            factura VARCHAR(10) NOT NULL UNIQUE,
            fecha_emision DATE NOT NULL,
            hora_emision TIME NOT NULL,
            rif_emisor VARCHAR(15) NOT NULL,
            ci_cliente INT NOT NULL,
            rif_cliente VARCHAR(15),
            ci_trabajador INT NOT NULL,
            metodo_pago VARCHAR(50) NOT NULL,
            FOREIGN KEY (ci_cliente) REFERENCES cliente(ci_cliente),
            FOREIGN KEY (ci_trabajador) REFERENCES trabajador(ci_trabajador)
        )""",
        
        """CREATE TABLE IF NOT EXISTS items_ventas (
            id_t13 INT AUTO_INCREMENT PRIMARY KEY,
            factura VARCHAR(10) NOT NULL,
            cod_producto VARCHAR(13) NOT NULL,
            codigo_item VARCHAR(11) NOT NULL,
            cod_almacen VARCHAR(11) NOT NULL,
            cantidad DECIMAL(12,2) NOT NULL,
            precio DECIMAL(15,2) NOT NULL,
            precio_iva DECIMAL(10,2) DEFAULT 0,
            precio_ivs DECIMAL(10,2) DEFAULT 0,
            precio_oia DECIMAL(10,2) DEFAULT 0,
            precio_retencion_iva DECIMAL(10,2) DEFAULT 0,
            desincorporacion TINYINT(1) DEFAULT 0,
            causa VARCHAR(200),
            cuando DATE,
            FOREIGN KEY (factura) REFERENCES ventas(factura)
        )""",
        
        """CREATE TABLE IF NOT EXISTS horario_trabajo (
            id_t14 INT AUTO_INCREMENT PRIMARY KEY,
            ci_trabajador INT NOT NULL,
            dia_semana ENUM('Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo') NOT NULL,
            hora_inicio_m TIME,
            hora_fin_m TIME,
            hora_inicio_t TIME,
            hora_fin_t TIME,
            es_feriado TINYINT(1) DEFAULT 0,
            activo TINYINT(1) DEFAULT 1,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion DATETIME NULL,
            FOREIGN KEY (ci_trabajador) REFERENCES trabajador(ci_trabajador)
        )""",
        
        """CREATE TABLE IF NOT EXISTS horario_excepcion (
            id_t15 INT AUTO_INCREMENT PRIMARY KEY,
            ci_trabajador INT NOT NULL,
            fecha_excepcion DATE NOT NULL,
            hora_inicio_m TIME,
            hora_fin_m TIME,
            hora_inicio_t TIME,
            hora_fin_t TIME,
            tipo_excepcion ENUM('Laboral','Feriado','Personal') NOT NULL,
            excepcion VARCHAR(255) NOT NULL,
            activo TINYINT(1) DEFAULT 1,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion DATETIME NULL,
            FOREIGN KEY (ci_trabajador) REFERENCES trabajador(ci_trabajador)
        )""",
        
        """CREATE TABLE IF NOT EXISTS horario_feriado (
            id_t16 INT AUTO_INCREMENT PRIMARY KEY,
            ci_trabajador INT NOT NULL,
            fecha_feriado DATE NOT NULL,
            feriado VARCHAR(255) NOT NULL,
            tipo_feriado ENUM('Nacional','Regional','Local','Empresarial') NOT NULL,
            activo TINYINT(1) DEFAULT 1,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion DATETIME NULL,
            FOREIGN KEY (ci_trabajador) REFERENCES trabajador(ci_trabajador)
        )"""
    ]
    
    for table in tables:
        try:
            db.execute_query(table)
        except Exception as e:
            print(f"Error creando tabla: {e}")

# ============ PUNTO DE ENTRADA ============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )