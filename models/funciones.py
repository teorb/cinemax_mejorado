from database import get_connection
from datetime import date, timedelta

def inicializar_funciones():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM funciones")
    r = cur.fetchone()
    total = r['c'] if hasattr(r, 'keys') else r[0]
    if total == 0:
        cur.execute("SELECT id FROM peliculas")
        peliculas = cur.fetchall()
        today = date.today()
        horarios = ["14:00", "16:30", "19:00", "21:30"]
        precios  = [15000, 15000, 18000, 18000]
        for i, p in enumerate(peliculas):
            pid = p['id'] if hasattr(p, 'keys') else p[0]
            for j in range(4):
                fecha = (today + timedelta(days=j)).strftime("%Y-%m-%d")
                for k, hora in enumerate(horarios):
                    cur.execute("INSERT INTO funciones (pelicula_id, fecha, hora, precio) VALUES (?,?,?,?)",
                        (pid, fecha, hora, precios[k]))
                    funcion_id = cur.lastrowid
                    cur.execute("SELECT id FROM asientos")
                    asientos = cur.fetchall()
                    for a in asientos:
                        aid = a['id'] if hasattr(a, 'keys') else a[0]
                        cur.execute("INSERT OR IGNORE INTO asiento_funcion (funcion_id, asiento_id) VALUES (?,?)",
                            (funcion_id, aid))
        conn.commit()
    conn.close()

def verificar_traslape(fecha, hora, pelicula_id=None, excluir_id=None):
    """Verifica si ya existe una funcion en la misma fecha y hora."""
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT f.*, p.titulo, p.duracion FROM funciones f JOIN peliculas p ON f.pelicula_id=p.id WHERE f.fecha=? AND f.hora=? AND f.estado='disponible'"
    params = [fecha, hora]
    if excluir_id:
        query += " AND f.id != ?"
        params.append(excluir_id)
    cur.execute(query, params)
    conflicto = cur.fetchone()
    conn.close()
    return dict(conflicto) if conflicto else None

def listar_funciones(pelicula_id=None):
    conn = get_connection()
    cur = conn.cursor()
    if pelicula_id:
        cur.execute("""SELECT f.*, p.titulo, p.duracion, p.clasificacion
            FROM funciones f JOIN peliculas p ON f.pelicula_id=p.id
            WHERE f.pelicula_id=? AND f.estado='disponible'
            ORDER BY f.fecha, f.hora""", (pelicula_id,))
    else:
        cur.execute("""SELECT f.*, p.titulo, p.imagen_url
            FROM funciones f JOIN peliculas p ON f.pelicula_id=p.id
            ORDER BY f.fecha, f.hora""")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def obtener_funcion(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT f.*, p.titulo, p.descripcion, p.duracion, p.genero,
        p.clasificacion, p.imagen_url
        FROM funciones f JOIN peliculas p ON f.pelicula_id=p.id
        WHERE f.id=?""", (id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def crear_funcion(pelicula_id, fecha, hora, precio):
    # Verificar traslape
    conflicto = verificar_traslape(fecha, hora)
    if conflicto:
        return False, f"Ya existe una funcion de '{conflicto['titulo']}' el {fecha} a las {hora}"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO funciones (pelicula_id,fecha,hora,precio) VALUES (?,?,?,?)",
        (pelicula_id, fecha, hora, precio))
    funcion_id = cur.lastrowid
    cur.execute("SELECT id FROM asientos")
    asientos = cur.fetchall()
    for a in asientos:
        aid = a['id'] if hasattr(a, 'keys') else a[0]
        cur.execute("INSERT OR IGNORE INTO asiento_funcion (funcion_id, asiento_id) VALUES (?,?)",
            (funcion_id, aid))
    conn.commit()
    conn.close()
    return True, "Funcion creada exitosamente"

def eliminar_funcion(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM asiento_funcion WHERE funcion_id=?", (id,))
    cur.execute("DELETE FROM funciones WHERE id=?", (id,))
    conn.commit()
    conn.close()

def asientos_funcion(funcion_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT a.id, a.fila, a.columna, af.estado
        FROM asientos a
        JOIN asiento_funcion af ON a.id=af.asiento_id
        WHERE af.funcion_id=?
        ORDER BY a.fila, a.columna""", (funcion_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def ocupacion_funcion(funcion_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM asiento_funcion WHERE funcion_id=? AND estado='ocupado'", (funcion_id,))
    r = cur.fetchone()
    conn.close()
    return r['total'] if r else 0
