from database import get_connection

# Usamos posters de TMDB con el CDN oficial que no bloquea
PELICULAS_PREDETERMINADAS = [
    (
        "Instinto Implacable",
        "La vida pacifica de Nikki, ex heroina de guerra, se ve destrozada cuando su hija es secuestrada por una red de trafico. Inmersa en el submundo criminal, lucha contrarreloj para rescatarla.",
        92, "Accion", "PG-13",
        "https://image.tmdb.org/t/p/w500/h8mpNzZKGBEt8NkbLHkGCiGCFGb.jpg"
    ),
    (
        "El Drama",
        "Una historia de amor y traicion en el mundo del teatro de Nueva York protagonizada por Zendaya y Robert Pattinson que cambiara sus vidas para siempre.",
        124, "Drama", "PG",
        "https://image.tmdb.org/t/p/w500/fqv8v6AycXKsivp1T5yKtLbGXce.jpg"
    ),
    (
        "El Testimonio de Ann Lee",
        "Basada en hechos reales. La impactante historia de una mujer que desafio a una poderosa secta religiosa y cambio la historia legal de su pais para siempre.",
        132, "Drama/Biografia", "+13",
        "https://image.tmdb.org/t/p/w500/rktDFPbfHfUbArZ6OOOKsXcv0Bm.jpg"
    ),
    (
        "La Posesion de la Momia",
        "Un arqueologo desentierra una antigua maldicion en Egipto que desata una fuerza sobrenatural. Solo hay una pregunta: que le paso a Katie?",
        108, "Terror", "+16",
        "https://image.tmdb.org/t/p/w500/qNBAXBIQlnOThrVvA6mA2B5ggV6.jpg"
    ),
    (
        "Michael",
        "La historia no contada del Rey del Pop: sus triunfos, sus demonios y el precio de ser la mayor estrella del mundo.",
        148, "Drama/Biografia", "PG-13",
        "https://image.tmdb.org/t/p/w500/2Dv0pgRBqfPFP5i1F0EzfWWEAvl.jpg"
    ),
    (
        "El Diablo Viste a la Moda 2",
        "Miranda Priestly regresa mas poderosa que nunca junto a Anne Hathaway, Emily Blunt y Meryl Streep en esta esperada secuela que revolucionara el mundo de la moda.",
        116, "Comedia/Drama", "PG",
        "https://image.tmdb.org/t/p/w500/b33nnKl1GSFbao4l3fZDDqsMx0F.jpg"
    ),
]

def inicializar_peliculas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM peliculas")
    r = cur.fetchone()
    total = r['c'] if hasattr(r, 'keys') else r[0]
    if total == 0:
        for titulo, desc, dur, genero, clas, img in PELICULAS_PREDETERMINADAS:
            cur.execute("""INSERT INTO peliculas (titulo, descripcion, duracion, genero, clasificacion, imagen_url, estado)
                VALUES (?,?,?,?,?,?,'activa')""", (titulo, desc, dur, genero, clas, img))
        conn.commit()
    conn.close()

def listar_peliculas(solo_activas=True):
    conn = get_connection()
    cur = conn.cursor()
    if solo_activas:
        cur.execute("SELECT * FROM peliculas WHERE estado='activa' ORDER BY id")
    else:
        cur.execute("SELECT * FROM peliculas ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def obtener_pelicula(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM peliculas WHERE id = ?", (id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def crear_pelicula(titulo, descripcion, duracion, genero, clasificacion, imagen_url):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO peliculas (titulo,descripcion,duracion,genero,clasificacion,imagen_url) VALUES (?,?,?,?,?,?)",
        (titulo, descripcion, duracion, genero, clasificacion, imagen_url))
    conn.commit()
    conn.close()

def editar_pelicula(id, titulo, descripcion, duracion, genero, clasificacion, imagen_url, estado):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE peliculas SET titulo=?,descripcion=?,duracion=?,genero=?,clasificacion=?,imagen_url=?,estado=? WHERE id=?",
        (titulo, descripcion, duracion, genero, clasificacion, imagen_url, estado, id))
    conn.commit()
    conn.close()

def eliminar_pelicula(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM peliculas WHERE id=?", (id,))
    conn.commit()
    conn.close()
