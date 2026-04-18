from database import get_connection
from datetime import date, timedelta

def listar_funciones(pelicula_id=None):
    conn = get_connection()
    cur = conn.cursor()
    if pelicula_id:
        cur.execute("""SELECT f.*, p.titulo, p.duracion, p.clasificacion
            FROM funciones f JOIN peliculas p ON f.pelicula_id = p.id
            WHERE f.pelicula_id = %s AND f.estado = 'disponible'
            ORDER BY f.fecha, f.hora""", (pelicula_id,))
    else:
        cur.execute("""SELECT f.*, p.titulo, p.imagen_url
            FROM funciones f JOIN peliculas p ON f.pelicula_id = p.id
            ORDER BY f.fecha, f.hora""")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def obtener_funcion(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT f.*, p.titulo, p.descripcion, p.duracion, p.genero,
        p.clasificacion, p.imagen_url
        FROM funciones f JOIN peliculas p ON f.pelicula_id = p.id
        WHERE f.id = %s""", (id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def crear_funcion(pelicula_id, fecha, hora, precio):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO funciones (pelicula_id, fecha, hora, precio) 
            VALUES (%s, %s, %s, %s) RETURNING id""",
            (pelicula_id, fecha, hora, precio))
        funcion_id = cur.fetchone()['id']
        cur.execute("SELECT id FROM asientos")
        asientos = cur.fetchall()
        for a in asientos:
            cur.execute("""INSERT INTO asiento_funcion (funcion_id, asiento_id)
                VALUES (%s, %s) ON CONFLICT DO NOTHING""", (funcion_id, a['id']))
        conn.commit()
        conn.close()
        return True, 'Funcion creada'
    except Exception as e:
        conn.close()
        return False, str(e)

def eliminar_funcion(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM asiento_funcion WHERE funcion_id = %s", (id,))
    cur.execute("DELETE FROM funciones WHERE id = %s", (id,))
    conn.commit()
    conn.close()

def asientos_funcion(funcion_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT a.id, a.fila, a.columna, af.estado
        FROM asientos a
        JOIN asiento_funcion af ON a.id = af.asiento_id
        WHERE af.funcion_id = %s
        ORDER BY a.fila, a.columna""", (funcion_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def ocupacion_funcion(funcion_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM asiento_funcion WHERE funcion_id = %s AND estado = 'ocupado'", (funcion_id,))
    r = cur.fetchone()
    conn.close()
    return r['total'] if r else 0
