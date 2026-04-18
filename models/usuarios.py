from database import get_connection

def login(email, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE email = %s AND password = %s",
        (email, password))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def registrar(nombre, email, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)",
            (nombre, email, password))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def email_existe(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM usuarios WHERE email = %s", (email,))
    r = cur.fetchone()
    conn.close()
    return r['c'] > 0
