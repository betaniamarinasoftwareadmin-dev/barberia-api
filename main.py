from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import sys

print("🐍 Iniciando API Barbería BETANIA...")

# Intentar importar config y database
try:
    from config import Config
    print("✅ Config importado correctamente")
except ImportError as e:
    print(f"❌ Error importando Config: {e}")
    class Config:
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_USER = os.getenv('DB_USER', '')
        DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        DB_NAME = os.getenv('DB_NAME', '')
        DB_PORT = int(os.getenv('DB_PORT', 3306))
        SECRET_KEY = 'clave-secreta-para-desarrollo'
        IVA_PORCENTAJE = 16.0
        ALLOWED_ORIGINS = ['*']
        API_VERSION = "1.0.0"
        API_TITLE = "Barbería API"
        API_DESCRIPTION = "API para Barbería BETANIA"

try:
    from database import db
    print("✅ Database importado correctamente")
except ImportError as e:
    print(f"❌ Error importando Database: {e}")
    class Database:
        def connect(self): return True
        def close(self): pass
        def execute_query(self, q, p=None): return {}
        def fetch_one(self, q, p=None): return None
        def fetch_all(self, q, p=None): return []
    db = Database()

# Intentar importar rutas
routes_loaded = {}

# Lista de rutas a importar
routes_list = [
    ('auth', 'routes.auth'),
    ('users', 'routes.users'),
    ('clients', 'routes.clients'),
    ('budget', 'routes.budget'),
    ('suppliers', 'routes.suppliers'),
    ('warehouses', 'routes.warehouses'),
    ('inventory', 'routes.inventory'),
    ('purchases', 'routes.purchases'),
    ('sales', 'routes.sales'),
    ('appointments', 'routes.appointments'),
    ('schedule', 'routes.schedule'),
    ('dashboard', 'routes.dashboard')
]

for route_name, route_path in routes_list:
    try:
        module = __import__(route_path, fromlist=['router'])
        if hasattr(module, 'router'):
            routes_loaded[route_name] = True
            print(f"✅ routes/{route_name} importado correctamente")
        else:
            routes_loaded[route_name] = False
            print(f"⚠️ routes/{route_name} no tiene 'router'")
    except ImportError as e:
        routes_loaded[route_name] = False
        print(f"⚠️ No se pudo importar routes/{route_name}: {e}")

# Crear la aplicación
app = FastAPI(
    title=Config.API_TITLE,
    description=Config.API_DESCRIPTION,
    version=Config.API_VERSION
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ RUTAS PRINCIPALES ============

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "API Barbería BETANIA",
        "version": Config.API_VERSION,
        "routes_loaded": routes_loaded
    }

@app.get("/health")
async def health_check():
    try:
        db_connected = db.connect()
        return {
            "status": "healthy",
            "database": "connected" if db_connected else "disconnected",
            "routes": routes_loaded
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "error",
                "error": str(e)
            }
        )

# ============ INCLUIR RUTAS ============

if routes_loaded.get('auth', False):
    from routes import auth
    app.include_router(auth.router, prefix="/api", tags=["Autenticación"])

if routes_loaded.get('users', False):
    from routes import users
    app.include_router(users.router, prefix="/api/users", tags=["Usuarios"])

if routes_loaded.get('clients', False):
    from routes import clients
    app.include_router(clients.router, prefix="/api/clients", tags=["Clientes"])

if routes_loaded.get('budget', False):
    from routes import budget
    app.include_router(budget.router, prefix="/api/budget", tags=["Presupuesto"])

if routes_loaded.get('suppliers', False):
    from routes import suppliers
    app.include_router(suppliers.router, prefix="/api/suppliers", tags=["Proveedores"])

if routes_loaded.get('warehouses', False):
    from routes import warehouses
    app.include_router(warehouses.router, prefix="/api/warehouses", tags=["Almacenes"])

if routes_loaded.get('inventory', False):
    from routes import inventory
    app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventario"])

if routes_loaded.get('purchases', False):
    from routes import purchases
    app.include_router(purchases.router, prefix="/api/purchases", tags=["Compras"])

if routes_loaded.get('sales', False):
    from routes import sales
    app.include_router(sales.router, prefix="/api/sales", tags=["Ventas"])

if routes_loaded.get('appointments', False):
    from routes import appointments
    app.include_router(appointments.router, prefix="/api/appointments", tags=["Citas"])

if routes_loaded.get('schedule', False):
    from routes import schedule
    app.include_router(schedule.router, prefix="/api/schedule", tags=["Horarios"])

if routes_loaded.get('dashboard', False):
    from routes import dashboard
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

# ============ MANEJADOR DE ERRORES ============

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    print(f"❌ Error: {exc}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)}
    )

# ============ PUNTO DE ENTRADA ============

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Servidor iniciado en puerto {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )