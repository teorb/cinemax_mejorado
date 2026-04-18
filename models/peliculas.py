from database import get_connection

def listar_peliculas(solo_activas=True):
    conn = get_connection()
    cur = conn.cursor()
    if solo_activas:
        cur.execute("SELECT * FROM peliculas WHERE estado = 'activa' ORDER BY id DESC")
    else:
        cur.execute("SELECT * FROM peliculas ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def obtener_pelicula(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM peliculas WHERE id = %s", (id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def crear_pelicula(titulo, descripcion, duracion, genero, clasificacion, imagen_url):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO peliculas (titulo, descripcion, duracion, genero, clasificacion, imagen_url)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        (titulo, descripcion, duracion, genero, clasificacion, imagen_url))
    conn.commit()
    conn.close()

def editar_pelicula(id, titulo, descripcion, duracion, genero, clasificacion, imagen_url, estado):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""UPDATE peliculas SET titulo=%s, descripcion=%s, duracion=%s,
        genero=%s, clasificacion=%s, imagen_url=%s, estado=%s WHERE id=%s""",
        (titulo, descripcion, duracion, genero, clasificacion, imagen_url, estado, id))
    conn.commit()
    conn.close()

def eliminar_pelicula(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM peliculas WHERE id = %s", (id,))
    conn.commit()
    conn.close()
