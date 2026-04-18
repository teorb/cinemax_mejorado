import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def inicializar_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'usuario'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS peliculas (
            id SERIAL PRIMARY KEY,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            duracion INTEGER,
            genero TEXT,
            clasificacion TEXT,
            imagen_url TEXT,
            estado TEXT DEFAULT 'activa'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS asientos (
            id SERIAL PRIMARY KEY,
            fila TEXT NOT NULL,
            columna INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS funciones (
            id SERIAL PRIMARY KEY,
            pelicula_id INTEGER REFERENCES peliculas(id),
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            precio REAL NOT NULL,
            estado TEXT DEFAULT 'disponible'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS asiento_funcion (
            id SERIAL PRIMARY KEY,
            funcion_id INTEGER REFERENCES funciones(id),
            asiento_id INTEGER REFERENCES asientos(id),
            estado TEXT DEFAULT 'disponible',
            UNIQUE(funcion_id, asiento_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tiquetes (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            usuario_id INTEGER REFERENCES usuarios(id),
            funcion_id INTEGER REFERENCES funciones(id),
            total REAL NOT NULL,
            estado TEXT DEFAULT 'activo',
            fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS detalle_tiquete (
            id SERIAL PRIMARY KEY,
            tiquete_id INTEGER REFERENCES tiquetes(id),
            asiento_id INTEGER REFERENCES asientos(id),
            precio_unitario REAL NOT NULL
        )
    """)

    # Crear asientos (10 filas A-J, 15 columnas)
    cur.execute("SELECT COUNT(*) as c FROM asientos")
    r = cur.fetchone()
    if r['c'] == 0:
        filas = ['A','B','C','D','E','F','G','H','I','J']
        for fila in filas:
            for col in range(1, 16):
                cur.execute("INSERT INTO asientos (fila, columna) VALUES (%s, %s)", (fila, col))

    # Crear admin por defecto
    cur.execute("SELECT COUNT(*) as c FROM usuarios WHERE email='admin@cine.com'")
    r = cur.fetchone()
    if r['c'] == 0:
        cur.execute("""
            INSERT INTO usuarios (nombre, email, password, rol)
            VALUES ('Admin', 'admin@cine.com', 'admin123', 'admin')
        """)

    conn.commit()
    conn.close()
