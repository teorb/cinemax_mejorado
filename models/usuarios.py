from database import get_connection
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def crear_admin():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE email = 'admin@cine.com'")
    if not cur.fetchone():
        cur.execute("INSERT INTO usuarios (nombre, email, password, rol) VALUES (?,?,?,?)",
            ("Administrador", "admin@cine.com", hash_password("admin123"), "admin"))
        conn.commit()
    conn.close()

def login(email, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE email = ? AND password = ?",
        (email, hash_password(password)))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def registrar(nombre, email, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO usuarios (nombre, email, password, rol) VALUES (?,?,?,?)",
            (nombre, email, hash_password(password), "cliente"))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def email_existe(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    r = cur.fetchone()
    conn.close()
    return r is not None
