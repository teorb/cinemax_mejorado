from database import get_connection

def inicializar_asientos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM asientos")
    r = cur.fetchone()
    if r['c'] == 0:
        filas = ['A','B','C','D','E','F','G','H','I','J']
        for fila in filas:
            for col in range(1, 16):
                cur.execute("INSERT INTO asientos (fila, columna) VALUES (%s, %s)", (fila, col))
        conn.commit()
    conn.close()
