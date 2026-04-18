import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cine.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def inicializar_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre   TEXT NOT NULL,
            email    TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol      TEXT DEFAULT 'cliente'
        );
        CREATE TABLE IF NOT EXISTS peliculas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo        TEXT NOT NULL,
            descripcion   TEXT,
            duracion      INTEGER,
            genero        TEXT,
            clasificacion TEXT,
            imagen_url    TEXT,
            estado        TEXT DEFAULT 'activa'
        );
        CREATE TABLE IF NOT EXISTS funciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            pelicula_id INTEGER NOT NULL,
            fecha       TEXT NOT NULL,
            hora        TEXT NOT NULL,
            precio      REAL NOT NULL,
            estado      TEXT DEFAULT 'disponible',
            FOREIGN KEY (pelicula_id) REFERENCES peliculas(id)
        );
        CREATE TABLE IF NOT EXISTS asientos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            fila    TEXT NOT NULL,
            columna INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tiquetes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo       TEXT UNIQUE NOT NULL,
            usuario_id   INTEGER,
            funcion_id   INTEGER NOT NULL,
            fecha_compra TEXT DEFAULT (datetime('now')),
            total        REAL,
            estado       TEXT DEFAULT 'activo',
            FOREIGN KEY (funcion_id) REFERENCES funciones(id)
        );
        CREATE TABLE IF NOT EXISTS detalle_tiquete (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            tiquete_id      INTEGER NOT NULL,
            asiento_id      INTEGER NOT NULL,
            precio_unitario REAL,
            UNIQUE (tiquete_id, asiento_id),
            FOREIGN KEY (tiquete_id) REFERENCES tiquetes(id),
            FOREIGN KEY (asiento_id) REFERENCES asientos(id)
        );
        CREATE TABLE IF NOT EXISTS asiento_funcion (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            funcion_id INTEGER NOT NULL,
            asiento_id INTEGER NOT NULL,
            estado     TEXT DEFAULT 'disponible',
            UNIQUE (funcion_id, asiento_id),
            FOREIGN KEY (funcion_id) REFERENCES funciones(id),
            FOREIGN KEY (asiento_id) REFERENCES asientos(id)
        );
    """)
    conn.commit()
    conn.close()
    from models.asientos import inicializar_asientos
    from models.usuarios import crear_admin
    from models.peliculas import inicializar_peliculas
    from models.funciones import inicializar_funciones
    inicializar_asientos()
    crear_admin()
    inicializar_peliculas()
    inicializar_funciones()
