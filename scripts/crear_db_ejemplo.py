"""
Utilidad para crear una base de datos de ejemplo
"""
import sqlite3
import os
from datetime import datetime, timedelta
import random

def crear_base_datos_ejemplo():
    """
    Crea una base de datos SQLite con datos de ejemplo
    """
    # Crear carpeta data si no existe
    os.makedirs("data", exist_ok=True)
    
    db_path = "./data/ejemplo.db"
    
    # Conectar (crea el archivo si no existe)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📦 Creando base de datos de ejemplo...")
    
    # Tabla de Clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefono TEXT,
            ciudad TEXT,
            fecha_registro DATE
        )
    """)
    
    # Tabla de Productos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT,
            precio REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)
    
    # Tabla de Ventas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER,
            fecha DATE,
            total REAL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)
    
    # Insertar clientes de ejemplo
    clientes = [
        ("Juan Pérez", "juan.perez@email.com", "555-0101", "Madrid", "2023-01-15"),
        ("María García", "maria.garcia@email.com", "555-0102", "Barcelona", "2023-02-20"),
        ("Carlos López", "carlos.lopez@email.com", "555-0103", "Valencia", "2023-03-10"),
        ("Ana Martínez", "ana.martinez@email.com", "555-0104", "Sevilla", "2023-04-05"),
        ("Luis Rodríguez", "luis.rodriguez@email.com", "555-0105", "Madrid", "2023-05-12"),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO clientes (nombre, email, telefono, ciudad, fecha_registro)
        VALUES (?, ?, ?, ?, ?)
    """, clientes)
    
    # Insertar productos de ejemplo
    productos = [
        ("Laptop HP", "Electrónica", 899.99, 15),
        ("Mouse Logitech", "Electrónica", 29.99, 50),
        ("Teclado Mecánico", "Electrónica", 79.99, 30),
        ("Monitor LG 24''", "Electrónica", 199.99, 20),
        ("Audífonos Sony", "Electrónica", 149.99, 25),
        ("Escritorio", "Muebles", 299.99, 10),
        ("Silla Ergonómica", "Muebles", 249.99, 12),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO productos (nombre, categoria, precio, stock)
        VALUES (?, ?, ?, ?)
    """, productos)
    
    # Insertar ventas de ejemplo
    fecha_base = datetime.now() - timedelta(days=90)
    ventas = []
    
    for i in range(50):  # 50 ventas aleatorias
        cliente_id = random.randint(1, 5)
        producto_id = random.randint(1, 7)
        cantidad = random.randint(1, 3)
        
        # Obtener precio del producto
        cursor.execute("SELECT precio FROM productos WHERE id = ?", (producto_id,))
        precio = cursor.fetchone()[0]
        total = precio * cantidad
        
        fecha = fecha_base + timedelta(days=random.randint(0, 90))
        fecha_str = fecha.strftime("%Y-%m-%d")
        
        ventas.append((cliente_id, producto_id, cantidad, fecha_str, total))
    
    cursor.executemany("""
        INSERT INTO ventas (cliente_id, producto_id, cantidad, fecha, total)
        VALUES (?, ?, ?, ?, ?)
    """, ventas)
    
    conn.commit()
    
    # Mostrar estadísticas
    cursor.execute("SELECT COUNT(*) FROM clientes")
    num_clientes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM productos")
    num_productos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM ventas")
    num_ventas = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total) FROM ventas")
    total_ventas = cursor.fetchone()[0]
    
    print(f"\n✅ Base de datos creada exitosamente en: {db_path}")
    print(f"📊 Estadísticas:")
    print(f"   - Clientes: {num_clientes}")
    print(f"   - Productos: {num_productos}")
    print(f"   - Ventas registradas: {num_ventas}")
    print(f"   - Total en ventas: ${total_ventas:.2f}\n")
    
    conn.close()

if __name__ == "__main__":
    crear_base_datos_ejemplo()
