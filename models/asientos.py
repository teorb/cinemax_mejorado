from database import get_connection

FILAS = ['A','B','C','D','E','F','G','H','I','J']
COLUMNAS = 15

def inicializar_asientos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM asientos")
    r = cur.fetchone()
    total = r['c'] if hasattr(r, 'keys') else r[0]
    if total == 0:
        for fila in FILAS:
            for col in range(1, COLUMNAS + 1):
                cur.execute("INSERT INTO asientos (fila, columna) VALUES (?,?)", (fila, col))
        conn.commit()
    conn.close()
